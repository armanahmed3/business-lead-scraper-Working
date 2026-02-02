import streamlit as st
import pandas as pd
import requests
import json
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
import sqlite3
import hashlib

# Database Path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')

# Import our existing modules
from config import Config
from utils import setup_logging
from selenium_scraper import SeleniumScraper
from exporter import DataExporter
from dedupe import Deduplicator
from robots_checker import RobotsChecker
from yelp_scraper import YelpScraper
from yelp_scraper import YelpScraper
from yellow_pages_scraper import YellowPagesScraper
import extra_streamlit_components as stx
from datetime import timedelta
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# --- DB Handler Class ---
class DBHandler:
    def __init__(self):
        self.use_gsheets = False
        try:
            if GSheetsConnection and "connections" in st.secrets and "gsheets" in st.secrets.connections:
                self.use_gsheets = True
                self.conn = st.connection("gsheets", type=GSheetsConnection)
        except Exception:
            self.use_gsheets = False
            
    def init_db(self):
        if self.use_gsheets:
            # Check if we can read
            try:
                # Use ttl=0 to ensure we check the actual sheet status
                df = self.conn.read(ttl=0)
                if df is not None and not df.empty and 'username' in df.columns:
                    # Sheet exists and has data, don't overwrite
                    return
                
                # If we get here, the sheet might be empty or missing headers
                if df is not None and (df.empty or 'username' not in df.columns):
                    initial_data = pd.DataFrame([
                        {'username': 'admin', 'password': hash_password('admin'), 'role': 'admin', 'active': 1, 'created_at': datetime.now().isoformat()}
                    ])
                    self.conn.update(data=initial_data)
                    print("Initialized new Google Sheet database.")
            except Exception as e:
                # If it's a connection error, DON'T initialize/overwrite
                print(f"Warning: Could not connect to Google Sheets: {e}")
                # We don't set self.use_gsheets = False here because it might be transient
        else:
            # SQLite Logic
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (username TEXT PRIMARY KEY, password TEXT, role TEXT, active INTEGER DEFAULT 1, openrouter_key TEXT)''')
            
            # Migration for existing DBs
            try:
                c.execute("ALTER TABLE users ADD COLUMN openrouter_key TEXT")
            except sqlite3.OperationalError:
                pass # Already exists
            
            # Check if admin exists
            c.execute("SELECT username FROM users WHERE username='admin'")
            if not c.fetchone():
                admin_pass = hash_password("admin")
                try:
                    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                             ("admin", admin_pass, "admin"))
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
            conn.close()

    def get_user(self, username):
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                user = df[df['username'] == username]
                if not user.empty:
                    # Return tuple like sqlite: (password, role, active, openrouter_key)
                    row = user.iloc[0]
                    return (row['password'], row['role'], row.get('active', 1), row.get('openrouter_key', ""))
            except Exception as e:
                print(f"GSheets Read Error: {e}")
            return None
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT password, role, active, openrouter_key FROM users WHERE username=?", (username,))
            result = c.fetchone()
            conn.close()
            return result

    def update_api_key(self, username, key):
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                if 'openrouter_key' not in df.columns:
                    df['openrouter_key'] = ""
                df.loc[df['username'] == username, 'openrouter_key'] = key
                self.conn.update(data=df)
                return True
            except: return False
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE users SET openrouter_key = ? WHERE username = ?", (key, username))
                conn.commit()
                conn.close()
                return True
            except: return False

    def get_all_users(self):
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                return df[['username', 'role', 'active']]
            except:
                return pd.DataFrame(columns=['username', 'role', 'active'])
        else:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT username, role, active FROM users", conn)
            conn.close()
            return df

    def add_user(self, username, password, role):
        username = username.strip().lower()
        password = password.strip()
        hashed = hash_password(password)
        
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                if username in df['username'].values:
                    return False
                
                new_user = pd.DataFrame([{
                    'username': username, 
                    'password': hashed, 
                    'role': role, 
                    'active': 1,
                    'created_at': datetime.now().isoformat()
                }])
                updated_df = pd.concat([df, new_user], ignore_index=True)
                self.conn.update(data=updated_df)
                return True
            except Exception as e:
                print(f"Add User Error: {e}")
                return False
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                         (username, hashed, role))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()

    def update_user(self, username, new_password=None, new_role=None, active=None):
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                mask = df['username'] == username
                if not mask.any(): return False
                
                if new_password:
                    df.loc[mask, 'password'] = hash_password(new_password)
                if new_role:
                    df.loc[mask, 'role'] = new_role
                if active is not None:
                    df.loc[mask, 'active'] = 1 if active else 0
                    
                self.conn.update(data=df)
                return True
            except Exception as e:
                print(f"Update Error: {e}")
                return False
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                updates = []
                params = []
                
                if new_password:
                    updates.append("password = ?")
                    params.append(hash_password(new_password))
                if new_role:
                    updates.append("role = ?")
                    params.append(new_role)
                if active is not None:
                    updates.append("active = ?")
                    params.append(1 if active else 0)
                
                if updates:
                    params.append(username)
                    c.execute(f"UPDATE users SET {', '.join(updates)} WHERE username = ?", params)
                    conn.commit()
                conn.close()
                return True
            except Exception:
                return False

    def delete_user(self, username):
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                df = df[df['username'] != username]
                self.conn.update(data=df)
                return True
            except:
                return False
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
                conn.close()
                return True
            except:
                return False

    def get_storage_type(self):
        if self.use_gsheets:
            return "Google Sheets (Persistent)"
        return "Local SQLite (Temporary on Cloud)"

    def is_ephemeral(self):
        # Check if running on Streamlit Cloud and using SQLite
        is_cloud = os.environ.get('STREAMLIT_RUNTIME_ENV', '') != '' or 'SH_APP_ID' in os.environ
        return is_cloud and not self.use_gsheets

# Initialize DB Handler globally
db = DBHandler()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 'google_maps'

# User management functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize session state for UI enhancement
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark' # Default to dark as it looks professional

def init_db():
    db.init_db()

def authenticate_user(username, password):
    hashed_input = hash_password(password)
    result = db.get_user(username)
    
    if result:
        stored_password, role, active, openrouter_key = result
        # Robust boolean conversion
        if isinstance(active, str):
            if active.lower() in ['true', '1', 'yes']:
                active_bool = True
            else:
                active_bool = False
        else:
            try:
                active_bool = bool(active)
            except:
                active_bool = False
            
        print(f"Debug: User {username} found. ActiveRaw: {active} -> Bool: {active_bool}")
        
        if stored_password == hashed_input:
            if active_bool:
                st.session_state.username = username
                st.session_state.openrouter_api_key = openrouter_key if openrouter_key else ""
                return "success", role
            else:
                return "inactive", None
        else:
            # Check for plaintext password (migration case)
            if password == stored_password:
                 # Auto-migrate to hash if using GSheets or similar manual entry
                 db.update_user(username, new_password=password)
                 if active_bool:
                    st.session_state.username = username
                    st.session_state.openrouter_api_key = openrouter_key if openrouter_key else ""
                    return "success", role
            print(f"Debug: Password mismatch for {username}")
            
    return "invalid", None

def get_users():
    return db.get_all_users()

def add_user(username, password, role):
    return db.add_user(username, password, role)

def update_user(username, new_password=None, new_role=None, active=None):
    return db.update_user(username, new_password, new_role, active)

def delete_user(username):
    return db.delete_user(username)

def login_page():
    # Exact Replica of the Dark Theme Login UI
    # Dynamic Theme Colors
    if st.session_state.theme == 'dark':
        bg_color = "#0e1117"
        card_bg = "#151921"
        text_color = "#ffffff"
        input_bg = "#262730"
        label_color = "#bdc3c7"
        border_color = "#2d333b"
    else:
        bg_color = "#f0f2f6"
        card_bg = "#ffffff"
        text_color = "#1a1a1a"
        input_bg = "#f9f9f9"
        label_color = "#4a4a4a"
        border_color = "#e0e0e0"

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* General App Styling */
        .stApp {{
            background-color: {bg_color};
            transition: all 0.3s ease;
        }}
        
        /* Hide default Streamlit elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

        /* Centering Wrapper */
        .login-wrapper {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding-top: 50px;
            width: 100%;
        }}

        /* 1. Header Card */
        .header-card {{
            width: 100%;
            max-width: 500px;
            background: linear-gradient(90deg, #6c5ce7 0%, #a29bfe 100%); /* Purple Gradient */
            border-radius: 15px;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            position: relative;
        }}
        
        .header-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }}

        .header-title {{
            color: white;
            font-family: 'Inter', sans-serif;
            font-size: 32px;
            font-weight: 700;
            margin: 0;
            line-height: 1;
        }}
        
        .lock-icon {{
            font-size: 32px;
        }}

        /* 2. Login Form Styling */
        [data-testid="stForm"] {{
            background-color: {card_bg};
            border: 1px solid {border_color};
            border-radius: 15px;
            padding: 30px;
            max-width: 500px;
            margin: 0 auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}

        /* Input Fields */
        .stTextInput label {{
            color: {label_color} !important;
            font-size: 14px;
            font-weight: 500;
        }}
        
        .stTextInput > div > div > input {{
            background-color: {input_bg};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 12px;
        }}
        
        .stTextInput > div > div > input:focus {{
            border-color: #6c5ce7;
            box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.2);
        }}

        /* Checkbox */
        .stCheckbox label {{
            color: {text_color} !important;
        }}

        /* Submit Button */
        .stButton > button {{
            background-color: #ff4757 !important;
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }}
        
        .stButton > button:hover {{
            background-color: #ff6b81 !important;
            box-shadow: 0 4px 12px rgba(255, 71, 87, 0.3);
            transform: translateY(-1px);
        }}

        /* Theme Toggle Button Link Styling */
        .theme-toggle-container {{
            text-align: center;
            margin-top: 20px;
        }}
        </style>
    """, unsafe_allow_html=True)

    # 0. Theme Switcher (External to form)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        theme_label = "🌙 Dark Mode" if st.session_state.theme == "light" else "☀️ Light Mode"
        if st.button(theme_label, key="login_theme_toggle", use_container_width=True):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()

    # Layout using Columns to center the content effectively
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 1. Header Card (HTML)
        st.markdown("""
            <div class="header-card">
                <div class="header-content">
                    <span class="lock-icon">🔐</span>
                    <h1 class="header-title">Login</h1>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 2. Form (Streamlit native widgets styled with CSS)
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username or Email", placeholder="Enter your username or email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            remember_me = st.checkbox("Keep me signed in for 7 days")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # The submit button
            submit_button = st.form_submit_button("Login")

        if submit_button:
            # Strip whitespace to prevent accidental copy-paste errors
            clean_username = username.strip().lower() # Case insensitive username
            clean_password = password.strip()
            
            if not clean_username or not clean_password:
                st.warning("Please enter all fields.", icon="⚠️")
            else:
                # Authenticate
                status, role = authenticate_user(clean_username, clean_password)
                
                if status == "success":
                    st.session_state.logged_in = True
                    st.session_state.user_role = role
                    st.session_state.page = 'dashboard'
                    
                    # Handle "Remember Me"
                    if remember_me:
                        try:
                            # Use session state to pass signal to main or handle here carefully
                            # Re-initializing here might be risky if component already mounted
                            # Instead, we'll set a flag and let main handle it or try a specific key
                            temp_cookie_manager = stx.CookieManager(key="login_cookie_setter")
                            # Set cookie to expire in 7 days
                            expires = datetime.now() + timedelta(days=7)
                            temp_cookie_manager.set('user_token', clean_username, expires_at=expires)
                            temp_cookie_manager.set('user_role', role, expires_at=expires)
                        except Exception as e:
                            print(f"Cookie error: {e}")
                    
                    st.success("Login successful!", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                elif status == "inactive":
                    st.error("Account is inactive. Please contact admin.", icon="🚫")
                else:
                    st.error("Invalid credentials.", icon="❌")


def admin_panel():
    st.title("🛡️ Admin Panel")
    
    if st.session_state.user_role != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    st.header("Manage Users")
    
    # Persistence Warning
    if db.is_ephemeral():
        st.warning("""
        ⚠️ **Warning: Temporary Storage Detected**
        You are running on a cloud platform but haven't configured Google Sheets. 
        **Any users you add will be deleted** when the app restarts (usually after 30 mins of inactivity).
        
        Please follow the `PERSISTENT_STORAGE_GUIDE.md` to set up Google Sheets for permanent storage.
        """, icon="🚨")
    else:
        st.success(f"✅ Storage Mode: {db.get_storage_type()}", icon="💾")
    
    # Add new user
    st.subheader("Add New User")
    with st.form("add_user_form"):
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        new_role = st.selectbox("Role", ["admin", "user"])
        add_user_btn = st.form_submit_button("Add User")
        
        if add_user_btn:
            if new_username and new_password:
                if add_user(new_username, new_password, new_role):
                    st.success(f"User {new_username} added successfully!")
                    st.rerun()
                else:
                    st.error("Username already exists!")
            else:
                st.error("Please fill in all fields")
    
    # Show existing users
    st.subheader("Existing Users")
    users_df = get_users()
    st.dataframe(users_df)
    
    # Update/Delete users
    if not users_df.empty:
        selected_user = st.selectbox("Select User to Manage", users_df['username'].tolist())
        if selected_user:
            user_data = users_df[users_df['username'] == selected_user].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                new_password = st.text_input("New Password (leave blank to keep current)", type="password")
            with col2:
                new_role = st.selectbox("New Role", ["admin", "user"], index=0 if user_data['role'] == 'admin' else 1)
            with col3:
                active_status = st.checkbox("Active", value=bool(user_data['active']))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update User"):
                    if update_user(selected_user, new_password if new_password else None, new_role, active_status):
                        st.success(f"User {selected_user} updated!")
                        st.rerun()
                    else:
                        st.error("Failed to update user. Check DB connection.")
            with col2:
                if st.button("Delete User"):
                    if delete_user(selected_user):
                        st.success(f"User {selected_user} deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete user.")

def user_panel():
    st.markdown("""
        <div style="background-color: #2c3e50; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: white; margin: 0;">🌍 Google Maps Lead Scraper Pro</h2>
            <p style="color: #bdc3c7;">This is for Ti-Tech Software House Candidates. Generate high-quality business leads with advanced extraction.</p>
        </div>
    """, unsafe_allow_html=True)
    google_maps_scraping()

def price_estimator_tab():
    st.markdown("""
        <div style="background-color: #2c3e50; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: white; margin: 0;">💰 Professional Price Estimator</h2>
            <p style="color: #bdc3c7;">Generate detailed, professional service quotes based on client requirements using AI.</p>
        </div>
    """, unsafe_allow_html=True)

    # Use session state to persist API key during session
    if 'openrouter_api_key' not in st.session_state:
        st.session_state.openrouter_api_key = ""

    with st.expander("🔑 API Configuration", expanded=not st.session_state.openrouter_api_key):
        api_key = st.text_input("OpenRouter API Key", 
                                value=st.session_state.openrouter_api_key,
                                type="password", 
                                help="Enter your OpenRouter API key. Get one at openrouter.ai")
        
        col_save, col_clear = st.columns([1, 1])
        with col_save:
            if st.button("💾 Save Permanently", use_container_width=True):
                if api_key:
                    if db.update_api_key(st.session_state.username, api_key):
                        st.session_state.openrouter_api_key = api_key
                        st.success("✅ API Key saved permanently for this user!")
                    else:
                        st.error("Failed to save API Key.")
                else:
                    st.warning("Please enter a key first.")
        
        with col_clear:
            if st.button("🗑️ Clear Stored Key", use_container_width=True):
                if db.update_api_key(st.session_state.username, ""):
                    st.session_state.openrouter_api_key = ""
                    st.rerun()

        if not st.session_state.openrouter_api_key:
            st.info("Please enter your OpenRouter API key to proceed.")
        else:
            st.success("✅ API Key is loaded from your profile.")

    client_req = st.text_area("Client Requirements / Project Details", 
                             height=200, 
                             placeholder="Enter the detailed requirements provided by the client (e.g., 'I need a mobile app for food delivery with real-time tracking...')")

    col1, col2 = st.columns(2)
    with col1:
        model_options = {
            "Meta: Llama 3 8B Instruct (Free)": "meta-llama/llama-3-8b-instruct:free",
            "Mistral: Mistral 7B Instruct (Free)": "mistralai/mistral-7b-instruct:free",
            "Google: Gemini 2.0 Flash Exp (Free)": "google/gemini-2.0-flash-exp:free",
            "Microsoft: Phi-3 Mini (Free)": "microsoft/phi-3-mini-128k-instruct:free",
            "OpenRouter: Auto (Free)": "openrouter/auto"
        }
        selected_model_name = st.selectbox("Select AI Model", list(model_options.keys()), help="If one model is slow or rate-limited, try another free option!")
        selected_model = model_options[selected_model_name]
    
    with col2:
        currency = st.selectbox("Currency", ["USD ($)", "EUR (€)", "GBP (£)", "PKR (Rs.)", "INR (₹)"])

    if st.button("📊 Generate Premium Quote", key="gen_quote_btn", use_container_width=True):
        if not st.session_state.openrouter_api_key:
            st.error("❌ API Key is required! Please enter it in the API Configuration section.")
            return
        if not client_req:
            st.error("❌ Please enter client requirements!")
            return
            
        with st.spinner("🚀 AI is analyzing requirements and crafting a premium professional quote..."):
            try:
                # ... (prompt remains the same)
                prompt = f"""
                You are a senior project manager and lead consultant at a world-class, premium software development agency. 
                Your task is to analyze the following client requirements and provide a highly professional, detailed, and premium-tier price estimation in {currency}.
                
                CLIENT REQUIREMENTS:
                {client_req}
                
                GUIDELINES FOR ESTIMATION:
                1. Professional Tone: Use sophisticated, persuasive business language. 
                2. Detailed Breakdown: 
                   - Discovery & Strategy
                   - UI/UX Design (Premium)
                   - Development Phase (Frontend & Backend)
                   - Quality Assurance & Testing
                   - Deployment & DevOps
                   - Post-Launch Support & Maintenance
                3. Itemized Pricing: Provide a detailed price table that includes costs for specific sub-tasks and "each and every thing" mentioned in the requirements. Do not be vague.
                4. Premium Pricing: The prices must reflect high-end, top-tier agency standards (e.g., $150-$300/hour equivalent). These are "high price trained" estimations for elite clientele.
                5. Value Proposition: Briefly explain why each phase is critical for the success of their project.
                6. Timeline: Estimate a professional timeline for delivery.
                7. Total Investment: Provide a clear total investment range at the end.
                8. Formatting: Use professional Markdown with clear headings, bold text, bullet points, and tables. 
                
                Act as if you are closing a high-ticket deal. Be authoritative, detailed, and clear.
                """
                
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {st.session_state.openrouter_api_key}",
                        "HTTP-Referer": "http://localhost:8501",
                        "X-Title": "Lead Scraper Pro Price Estimator",
                    },
                    json={
                        "model": selected_model,
                        "messages": [
                            {"role": "system", "content": "You are an elite business consultant and senior project estimator for a top-tier software house."},
                            {"role": "user", "content": prompt}
                        ]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # ... rest of the logic
                    if 'choices' in result and len(result['choices']) > 0:
                        quote = result['choices'][0]['message']['content']
                        st.success("✅ Quote generated successfully!")
                        st.markdown("---")
                        st.markdown(quote)
                        
                        st.markdown("---")
                        # Option to download as text
                        st.download_button(
                            label="📥 Download Professional Quote (TXT)",
                            data=quote,
                            file_name=f"Professional_Quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    else:
                        st.error(f"Unexpected response format from AI: {result}")
                elif response.status_code == 429:
                    st.error("🚨 **Error 429: Rate Limit Exceeded**")
                    st.warning("The selected AI model (Gemini) is currently busy. Please **select a different model** (like Llama 3 or Mistral) from the dropdown and try again!")
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
                    
            except Exception as e:
                st.error(f"💥 System Error: {str(e)}")

def google_maps_scraping():
    col1, col2 = st.columns(2)
    with col1:
        query = st.text_input("Business Criteria", "restaurants", help="E.g., Restaurants, Plumbers, Software Companies")
        location = st.text_input("Target Location", "New York, USA", help="City, State, or Region")
    with col2:
        max_leads = st.number_input("Target Unique Leads", min_value=1, max_value=1000, value=50, step=1, help="Exact number of unique leads to generate")
        delay = st.slider("Safe Delay (seconds)", 1.0, 10.0, 3.0, step=0.5, help="Increase to avoid detection")
    
    # Enhanced format selection including Excel
    formats = st.multiselect(
        "Export Formats", 
        ["excel", "csv", "json", "sqlite"], 
        default=["excel"],
        help="Select output formats. Excel includes CRM tracking columns."
    )
    
    if st.button("🚀 Start Lead Generation", key="google_maps_start", use_container_width=True):
        if not query or not location:
            st.error("Please specify both business criteria and target location.")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            config = Config()
            # Temporarily disable robots.txt for testing to ensure results
            config._config['robots']['enabled'] = False
            config._config['scraping']['default_delay'] = delay
            config._config['scraping']['max_leads_per_session'] = max_leads
            
            logger = setup_logging(config)
            
            status_text.markdown("### 🔄 Initializing Advanced Scraper...")
            
            # Initialize scraper
            scraper = SeleniumScraper(
                config=config,
                headless=not st.checkbox("Debug Mode (Show Browser)", value=False),
                guest_mode=True,
                delay=delay
            )
            
            status_text.markdown(f"### 🔍 Searching for **{query}** in **{location}**...")
            progress_bar.progress(10)
            
            # Perform scraping
            # Note: The scraper collects leads. Deduplication ensures uniqueness.
            leads = scraper.scrape_google_maps(
                query=query,
                location=location,
                max_results=max_leads
            )
            
            scraper.close()
            status_text.markdown("### ⚙️ Processing and Deduplicating Data...")
            progress_bar.progress(75)
            
            # Deduplicate
            deduplicator = Deduplicator(config)
            unique_leads = deduplicator.deduplicate(leads)
            
            # Verify count - if we have duplicates, we might have fewer than requested
            # In a real "exact count" scenario, we'd loop. 
            # For now, we report what we have.
            
            status_text.markdown("### 💾 Preparing Download...")
            progress_bar.progress(90)
            
            # Use temporary directory for export to avoid disk usage issues on Cloud
            with tempfile.TemporaryDirectory() as temp_dir:
                exporter = DataExporter(config, output_dir=temp_dir)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                clean_query = "".join(x for x in query if x.isalnum() or x in " -_").strip().replace(" ", "_")
                clean_loc = "".join(x for x in location if x.isalnum() or x in " -_").strip().replace(" ", "_")
                base_filename = f"Leads_{clean_query}_{clean_loc}_{timestamp}"
                
                exported_files = exporter.export(
                    data=unique_leads,
                    formats=formats,
                    filename=base_filename
                )
                
                progress_bar.progress(100)
                status_text.markdown("### ✅ Generation Complete!")
                
                st.success(f"Successfully generated {len(unique_leads)} unique leads (Raw: {len(leads)})")
                
                if unique_leads:
                    df = pd.DataFrame(unique_leads)
                    # Show preview (limit columns for UI)
                    preview_cols = ['name', 'phone', 'email', 'website', 'address']
                    st.dataframe(df[ [c for c in preview_cols if c in df.columns] ])
                    
                    # Download buttons - Read into memory immediately
                    st.markdown("### 📥 Download Results" )
                    cols = st.columns(len(exported_files))
                    for idx, file_path in enumerate(exported_files):
                        with cols[idx]:
                            path_obj = Path(file_path)
                            with open(file_path, 'rb') as f:
                                file_data = f.read()
                                
                            st.download_button(
                                label=f"Download {path_obj.suffix[1:].upper()}",
                                data=file_data,
                                file_name=path_obj.name,
                                mime="application/octet-stream" if path_obj.suffix != '.xlsx' else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"dl_{idx}"
                            )
                
            # Temp dir is automatically cleaned up here
        
        except Exception as e:
            st.error(f"System Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

def main():
    init_db()
    
    # Cookie Manager for session persistence
    cookie_manager = stx.CookieManager()
    
    # Check for existing cookies if not logged in
    if not st.session_state.get('logged_in', False):
        user_token = cookie_manager.get('user_token')
        role_token = cookie_manager.get('user_role')
        
        if user_token and role_token:
            # Validate user against DB to ensure they still exist/active
            user_data = db.get_user(user_token)
            
            if user_data:
                # user_data = (password, role, active, openrouter_key)
                active_val = user_data[2]
                
                # Robust boolean conversion
                if isinstance(active_val, str):
                    active_bool = active_val.lower() in ['true', '1', 'yes']
                else:
                    active_bool = bool(active_val)
                    
                if active_bool:
                    st.session_state.logged_in = True
                    st.session_state.username = user_token
                    st.session_state.user_role = role_token
                    st.session_state.openrouter_api_key = user_data[3] if user_data[3] else ""
                    st.session_state.page = 'dashboard'
                    st.rerun()
                else:
                    result = None # Force cleanup below
            else:
                result = None
            
            if result is None:
                # Invalid or inactive user, clear cookies
                cookie_manager.delete('user_token')
                cookie_manager.delete('user_role')
    
    if st.session_state.page == 'login' or not st.session_state.get('logged_in', False):
        login_page()
    else:
        # Enhanced sidebar with beautiful design
        with st.sidebar:
            st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            [data-testid="stSidebar"] .css-1d391kg {
                padding-top: 1rem;
            }
            .sidebar-header {
                color: white;
                font-size: 1.5rem;
                font-weight: bold;
                margin-bottom: 1rem;
                text-align: center;
            }
            .user-info {
                color: #e0e0e0;
                font-size: 0.9rem;
                margin-bottom: 1rem;
                text-align: center;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="sidebar-header">📊 Lead Scraper Pro</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="user-info">👤 User: {st.session_state.get("username", "Unknown")}<br>🏷️ Role: {st.session_state.get("user_role", "user")}</div>', unsafe_allow_html=True)
            
            # Theme Toggle In Sidebar
            st.divider()
            theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"
            theme_btn_text = f"{theme_icon} Switch to {'Light' if st.session_state.theme == 'dark' else 'Dark'} Mode"
            if st.button(theme_btn_text, use_container_width=True):
                st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
                st.rerun()
            
            # Navigation Choices
            nav_options = ["🏠 Home / Scraper", "💰 Price Estimator"]
            if st.session_state.user_role == 'admin':
                nav_options.append("🛡️ Admin Panel")
            
            # Find current index
            current_tab = st.session_state.get('current_tab', 'user')
            if current_tab == 'admin':
                default_idx = nav_options.index("🛡️ Admin Panel")
            elif current_tab == 'estimator':
                default_idx = nav_options.index("💰 Price Estimator")
            else:
                default_idx = 0

            nav_selection = st.radio(
                "Navigation",
                nav_options,
                index=default_idx,
                key="nav_radio"
            )

            if nav_selection == "🛡️ Admin Panel":
                st.session_state.current_tab = 'admin'
            elif nav_selection == "💰 Price Estimator":
                st.session_state.current_tab = 'estimator'
            else:
                st.session_state.current_tab = 'user'
            
            st.divider()
            
            if st.button("🚪 Logout", key="logout_btn"):
                # Clear cookies
                try:
                    cookie_manager.delete('user_token')
                    cookie_manager.delete('user_role')
                except:
                    pass
                
                st.session_state.logged_in = False
                st.session_state.user_role = None
                st.session_state.page = 'login'
                st.session_state.current_tab = 'user'
                st.rerun()
        
        # Main content based on current tab
        if st.session_state.get('current_tab') == 'admin' and st.session_state.user_role == 'admin':
            admin_panel()
        elif st.session_state.get('current_tab') == 'estimator':
            price_estimator_tab()
        else:
            user_panel()

if __name__ == "__main__":
    main()