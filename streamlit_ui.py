import streamlit as st
import pandas as pd
import requests
import json
import os
import shutil
import tempfile
import time
import random
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
from yellow_pages_scraper import YellowPagesScraper
import extra_streamlit_components as stx
from datetime import timedelta
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

try:
    import gspread
except ImportError:
    gspread = None

# --- Enhanced DB Handler Class ---
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
                        {
                            'username': 'admin', 
                            'password': hash_password('admin'), 
                            'role': 'admin', 
                            'active': 1, 
                            'created_at': datetime.now().isoformat(),
                            'openrouter_key': "",
                            'aimlapi_key': "",
                            'bytez_key': "", 
                            'default_provider': 'openrouter',
                            'smtp_user': "",
                            'smtp_pass': "",
                            'gsheets_creds': "",
                            'plan': 'enterprise',
                            'usage_count': 0,
                            'usage_limit': 1000000,
                            'email_count': 0,
                            'email_limit': 1000000
                        }
                    ])
                    self.conn.update(data=initial_data)
                    print("Initialized new Google Sheet database with all SaaS columns.")
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
            except sqlite3.OperationalError: pass

            try:
                c.execute("ALTER TABLE users ADD COLUMN aimlapi_key TEXT")
            except sqlite3.OperationalError: pass

            try:
                c.execute("ALTER TABLE users ADD COLUMN bytez_key TEXT")
            except sqlite3.OperationalError: pass

            try:
                c.execute("ALTER TABLE users ADD COLUMN default_provider TEXT DEFAULT 'openrouter'")
            except sqlite3.OperationalError: pass
            
            try:
                c.execute("ALTER TABLE users ADD COLUMN smtp_user TEXT")
            except sqlite3.OperationalError: pass
            
            try:
                c.execute("ALTER TABLE users ADD COLUMN smtp_pass TEXT")
            except sqlite3.OperationalError: pass
            
            try:
                c.execute("ALTER TABLE users ADD COLUMN gsheets_creds TEXT")
            except sqlite3.OperationalError: pass

            try:
                c.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
            except sqlite3.OperationalError: pass

            try:
                c.execute("ALTER TABLE users ADD COLUMN usage_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError: pass

            try:
                c.execute("ALTER TABLE users ADD COLUMN usage_limit INTEGER DEFAULT 50")
            except sqlite3.OperationalError: pass

            try:
                c.execute("ALTER TABLE users ADD COLUMN email_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError: pass

            try:
                c.execute("ALTER TABLE users ADD COLUMN email_limit INTEGER DEFAULT 100")
            except sqlite3.OperationalError: pass
            
            # Check if admin exists
            c.execute("SELECT username FROM users WHERE username='admin'")
            if not c.fetchone():
                admin_pass = hash_password("admin")
                try:
                    c.execute("INSERT INTO users (username, password, role, plan, usage_limit, email_limit) VALUES (?, ?, ?, ?, ?, ?)",
                             ("admin", admin_pass, "admin", "enterprise", 1000000, 1000000))
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
                    # Return tuple like sqlite with all SaaS fields
                    row = user.iloc[0]
                    return (
                        row.get('password', ""), 
                        row.get('role', 'user'), 
                        row.get('active', 1), 
                        row.get('openrouter_key', ""),
                        row.get('default_provider', "openrouter"),
                        row.get('smtp_user', ""),
                        row.get('smtp_pass', ""),
                        row.get('gsheets_creds', ""),
                        row.get('plan', 'free'),
                        row.get('usage_count', 0),
                        row.get('usage_limit', 50),
                        row.get('email_count', 0),
                        row.get('email_limit', 100)
                    )
            except Exception as e:
                print(f"GSheets Read Error: {e}")
            return None
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Try to get all columns, fallback to basic ones
            try:
                c.execute("SELECT password, role, active, openrouter_key, default_provider, smtp_user, smtp_pass, gsheets_creds, plan, usage_count, usage_limit, email_count, email_limit FROM users WHERE username=?", (username,))
            except sqlite3.OperationalError:
                # Fallback for older DB versions
                c.execute("SELECT password, role, active, openrouter_key FROM users WHERE username=?", (username,))
                result = c.fetchone()
                conn.close()
                if result and len(result) == 4:
                    # Extend with default values for missing columns
                    return result + ("openrouter", "", "", "", "free", 0, 50, 0, 100)
                return result
            result = c.fetchone()
            conn.close()
            return result

    def update_settings(self, username, settings_dict):
        """Update multiple user settings at once."""
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                mask = df['username'] == username
                for key, value in settings_dict.items():
                    if key not in df.columns: df[key] = ""
                    df.loc[mask, key] = value
                self.conn.update(data=df)
                return True
            except: return False
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                for key, value in settings_dict.items():
                    # Sanitize key name for SQL injection prevention
                    if key in ['openrouter_key', 'default_provider', 'smtp_user', 'smtp_pass', 'gsheets_creds', 'plan', 'usage_count', 'usage_limit', 'email_count', 'email_limit']:
                        c.execute(f"UPDATE users SET {key} = ? WHERE username = ?", (value, username))
                conn.commit()
                conn.close()
                return True
            except: return False

    def migrate_to_gsheets(self):
        """Copies users from SQLite to Google Sheets if GSheets is connected."""
        if not self.use_gsheets:
            return False, "Google Sheets not connected."
        
        try:
            # 1. Get all users from SQLite
            conn = sqlite3.connect(DB_PATH)
            local_users = pd.read_sql_query("SELECT * FROM users", conn)
            conn.close()
            
            # 2. Get existing GSheets users
            df_gsheets = self.conn.read(ttl=0)
            
            # 3. Merge users (prioritize local if duplicates)
            new_users = []
            for _, row in local_users.iterrows():
                if row['username'] not in df_gsheets['username'].values:
                    # Clean the data to match expected columns
                    new_user = {
                        'username': row['username'],
                        'password': row['password'],
                        'role': row.get('role', 'user'),
                        'active': row.get('active', 1),
                        'created_at': datetime.now().isoformat(),
                        'openrouter_key': row.get('openrouter_key', ''),
                        'aimlapi_key': row.get('aimlapi_key', ''),
                        'bytez_key': row.get('bytez_key', ''),
                        'default_provider': row.get('default_provider', 'openrouter'),
                        'smtp_user': row.get('smtp_user', ''),
                        'smtp_pass': row.get('smtp_pass', ''),
                        'gsheets_creds': row.get('gsheets_creds', ''),
                        'plan': row.get('plan', 'free'),
                        'usage_count': row.get('usage_count', 0),
                        'usage_limit': row.get('usage_limit', 50),
                        'email_count': row.get('email_count', 0),
                        'email_limit': row.get('email_limit', 100)
                    }
                    new_users.append(new_user)
            
            if new_users:
                # Add missing columns to existing df if needed
                for col in new_users[0].keys():
                    if col not in df_gsheets.columns:
                        df_gsheets[col] = ""
                        
                df_final = pd.concat([df_gsheets, pd.DataFrame(new_users)], ignore_index=True)
                self.conn.update(data=df_final)
                return True, f"Successfully migrated {len(new_users)} users to Google Sheets!"
            else:
                return True, "No new users to migrate (everything already synced)."
                
        except Exception as e:
            return False, f"Migration Failed: {str(e)}"

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

    def update_user(self, username, new_password=None, new_role=None, active=None, plan=None, usage_limit=None, email_limit=None):
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                if df.empty: return False
                
                # Make a true copy to avoid view warnings/issues
                df = df.copy()
                
                mask = df['username'] == username
                if not mask.any(): return False
                
                # Careful updating
                if new_password:
                    df.loc[mask, 'password'] = hash_password(new_password)
                if new_role:
                    df.loc[mask, 'role'] = new_role
                if active is not None:
                    df.loc[mask, 'active'] = 1 if active else 0
                if plan:
                    df.loc[mask, 'plan'] = plan
                if usage_limit is not None:
                    df.loc[mask, 'usage_limit'] = int(usage_limit)
                if email_limit is not None:
                    df.loc[mask, 'email_limit'] = int(email_limit)
                
                # Ensure we are writing back the FULL dataframe
                # Some GSheets connectors behave oddly if you pass a subset or view
                self.conn.update(data=df)
                return True
            except Exception as e:
                print(f"Update Error: {e}")
                st.error(f"Database Error: {str(e)}")
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
                if plan:
                    updates.append("plan = ?")
                    params.append(plan)
                if usage_limit is not None:
                    updates.append("usage_limit = ?")
                    params.append(int(usage_limit))
                if email_limit is not None:
                    updates.append("email_limit = ?")
                    params.append(int(email_limit))
                
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
        # Enhanced result = (password, role, active, openrouter_key, default_provider, smtp_user, smtp_pass, gsheets_creds, plan, usage_count, usage_limit, email_count, email_limit)
        if len(result) >= 13:
            stored_password, role, active, openrouter_key, default_provider, smtp_user, smtp_pass, gsheets_creds, plan, usage_count, usage_limit, email_count, email_limit = result
        else:
            # Fallback for older format (password, role, active, openrouter_key)
            stored_password, role, active, openrouter_key = result[:4]
            default_provider = smtp_user = smtp_pass = gsheets_creds = ""
            plan = "free"
            usage_count = email_count = 0
            usage_limit = 50
            email_limit = 100
        
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
                st.session_state.default_provider = default_provider if default_provider else "openrouter"
                st.session_state.smtp_user = smtp_user if smtp_user else ""
                st.session_state.smtp_pass = smtp_pass if smtp_pass else ""
                try:
                    st.session_state.google_sheets_creds = json.loads(gsheets_creds) if gsheets_creds else None
                except:
                    st.session_state.google_sheets_creds = None
                
                # SaaS Session State
                st.session_state.user_plan = plan if plan else "free"
                
                # Safe conversion function
                def safe_int(val, default=0):
                    try:
                        if pd.isna(val): return default
                        return int(float(val))
                    except: return default

                st.session_state.usage_count = safe_int(usage_count, 0)
                st.session_state.email_count = safe_int(email_count, 0)
                
                if role == 'admin':
                    st.session_state.user_plan = 'enterprise'
                    st.session_state.usage_limit = 1000000
                    st.session_state.email_limit = 1000000
                else:
                    st.session_state.usage_limit = safe_int(usage_limit, 50)
                    st.session_state.email_limit = safe_int(email_limit, 100)
                
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
                    st.session_state.default_provider = default_provider if default_provider else "openrouter"
                    st.session_state.smtp_user = smtp_user if smtp_user else ""
                    st.session_state.smtp_pass = smtp_pass if smtp_pass else ""
                    try:
                        st.session_state.google_sheets_creds = json.loads(gsheets_creds) if gsheets_creds else None
                    except:
                        st.session_state.google_sheets_creds = None
                    
                    # SaaS Session State
                    st.session_state.user_plan = plan if plan else "free"
                    
                    # Safe conversion function
                    def safe_int_mig(val, default=0):
                        try:
                            if pd.isna(val): return default
                            return int(float(val))
                        except: return default

                    st.session_state.usage_count = safe_int_mig(usage_count, 0)
                    st.session_state.email_count = safe_int_mig(email_count, 0)
                    
                    if role == 'admin':
                        st.session_state.user_plan = 'enterprise'
                        st.session_state.usage_limit = 1000000
                        st.session_state.email_limit = 1000000
                    else:
                        st.session_state.usage_limit = safe_int_mig(usage_limit, 50)
                        st.session_state.email_limit = safe_int_mig(email_limit, 100)
                    
                    return "success", role
            print(f"Debug: Password mismatch for {username}")
            
    return "invalid", None

def get_users():
    return db.get_all_users()

def add_user(username, password, role):
    return db.add_user(username, password, role)

def update_user(username, new_password=None, new_role=None, active=None, plan=None, usage_limit=None, email_limit=None):
    return db.update_user(username, new_password, new_role, active, plan, usage_limit, email_limit)

def delete_user(username):
    return db.delete_user(username)

def login_page():
    # ... (rest of the code remains the same)
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
    
    # Enhanced Backup & Restore Area with Google Sheets Support
    st.divider()
    st.subheader("💾 Data Safety & Backups")
    st.info("💡 **Tip:** Before updating your project files or deploying to the cloud, download a backup of your users to ensure no data is lost.")
    
    # User Statistics
    st.subheader("📊 User Statistics")
    if not users_df.empty:
        total_users = len(users_df)
        active_users = len(users_df[users_df['active'] == 1])
        admin_users = len(users_df[users_df['role'] == 'admin'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", total_users)
        with col2:
            st.metric("Active Users", active_users)
        with col3:
            st.metric("Admin Users", admin_users)
        with col4:
            st.metric("Storage Type", "Google Sheets" if db.use_gsheets else "SQLite")
    
    # Google Sheets Backup Section
    if db.use_gsheets:
        st.subheader("☁️ Google Sheets Backup & Export")
        
        col_gs1, col_gs2, col_gs3 = st.columns(3)
        
        with col_gs1:
            if st.button("📥 Download Google Sheets Backup", use_container_width=True):
                try:
                    # Get all users from Google Sheets
                    df = db.conn.read(ttl=0)
                    if not df.empty:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="⬇️ Download Complete Backup",
                            data=csv,
                            file_name=f"gsheets_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime='text/csv',
                            use_container_width=True
                        )
                        st.success("✅ Google Sheets data ready for download!")
                    else:
                        st.warning("No data found in Google Sheets.")
                except Exception as e:
                    st.error(f"Failed to fetch Google Sheets data: {e}")
        
        with col_gs2:
            if st.button("🔄 Refresh Google Sheets Data", use_container_width=True):
                try:
                    df = db.conn.read(ttl=0)
                    st.success(f"✅ Successfully refreshed {len(df)} users from Google Sheets!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to refresh: {e}")
        
        with col_gs3:
            if st.button("📊 View Google Sheets Status", use_container_width=True):
                try:
                    df = db.conn.read(ttl=0)
                    st.info(f"📈 Connected to Google Sheets!")
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"Connection issue: {e}")
        
        # Google Sheets Specific Backup Options
        st.markdown("**🌐 Google Sheets Advanced Options**")
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            # Backup specific columns
            all_columns = ['username', 'role', 'active', 'plan', 'usage_count', 'usage_limit', 'email_count', 'email_limit', 'created_at']
            selected_columns = st.multiselect("Select Columns to Backup", all_columns, default=all_columns)
            
            if st.button("📋 Export Selected Columns", use_container_width=True):
                try:
                    df = db.conn.read(ttl=0)
                    if selected_columns and not df.empty:
                        filtered_df = df[selected_columns]
                        csv = filtered_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="⬇️ Download Filtered Backup",
                            data=csv,
                            file_name=f"gsheets_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime='text/csv',
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Failed to export filtered data: {e}")
        
        with col_adv2:
            # Active users only backup
            if st.button("👥 Backup Active Users Only", use_container_width=True):
                try:
                    df = db.conn.read(ttl=0)
                    if not df.empty:
                        active_df = df[df['active'] == 1]
                        csv = active_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="⬇️ Download Active Users",
                            data=csv,
                            file_name=f"active_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime='text/csv',
                            use_container_width=True
                        )
                        st.success(f"✅ {len(active_df)} active users ready for backup!")
                except Exception as e:
                    st.error(f"Failed to backup active users: {e}")
    
    # General Backup Section (for both SQLite and Google Sheets)
    st.subheader("🔄 General Backup & Restore")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if not users_df.empty:
            csv = users_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Current View Backup (CSV)",
                data=csv,
                file_name=f"user_backup_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                use_container_width=True
            )
    
    with col_b2:
        uploaded_file = st.file_uploader("📤 Restore from Backup", type="csv")
        if uploaded_file is not None:
            try:
                backup_df = pd.read_csv(uploaded_file)
                st.dataframe(backup_df.head())
                
                col_restore1, col_restore2 = st.columns(2)
                with col_restore1:
                    if st.button("🚀 Restore to Google Sheets", use_container_width=True, disabled=not db.use_gsheets):
                        if db.use_gsheets:
                            restored_count = 0
                            skipped_count = 0
                            try:
                                # Get existing users to avoid duplicates
                                existing_df = db.conn.read(ttl=0)
                                existing_users = set(existing_df['username'].values) if not existing_df.empty else set()
                                
                                for _, row in backup_df.iterrows():
                                    if row['username'] not in existing_users:
                                        # Add new user to Google Sheets
                                        new_user_data = {
                                            'username': row['username'],
                                            'password': hash_password("temp123"),  # Default password
                                            'role': row.get('role', 'user'),
                                            'active': bool(row.get('active', 1)),
                                            'created_at': datetime.now().isoformat(),
                                            'plan': row.get('plan', 'free'),
                                            'usage_count': 0,
                                            'usage_limit': int(row.get('usage_limit', 50)),
                                            'email_count': 0,
                                            'email_limit': int(row.get('email_limit', 100))
                                        }
                                        
                                        # Add to Google Sheets
                                        current_df = db.conn.read(ttl=0)
                                        updated_df = pd.concat([current_df, pd.DataFrame([new_user_data])], ignore_index=True)
                                        db.conn.update(data=updated_df)
                                        restored_count += 1
                                    else:
                                        skipped_count += 1
                                
                                st.success(f"✅ Restored {restored_count} users to Google Sheets!")
                                if skipped_count > 0:
                                    st.warning(f"⚠️ Skipped {skipped_count} existing users")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Restore failed: {e}")
                        else:
                            st.warning("⚠️ Google Sheets not connected")
                        
                with col_restore2:
                    if st.button("🔄 Merge with Existing", use_container_width=True):
                        merged_count = 0
                        for _, row in backup_df.iterrows():
                            try:
                                # Update existing user or add new one
                                if db.use_gsheets:
                                    df = db.conn.read(ttl=0)
                                    if row['username'] in df['username'].values:
                                        # Update existing user in Google Sheets
                                        mask = df['username'] == row['username']
                                        df.loc[mask, 'role'] = row.get('role', 'user')
                                        df.loc[mask, 'active'] = bool(row.get('active', 1))
                                        df.loc[mask, 'plan'] = row.get('plan', 'free')
                                        df.loc[mask, 'usage_limit'] = int(row.get('usage_limit', 50))
                                        df.loc[mask, 'email_limit'] = int(row.get('email_limit', 100))
                                        db.conn.update(data=df)
                                    else:
                                        # Add new user to Google Sheets
                                        new_user_data = {
                                            'username': row['username'],
                                            'password': hash_password("temp123"),
                                            'role': row.get('role', 'user'),
                                            'active': bool(row.get('active', 1)),
                                            'created_at': datetime.now().isoformat(),
                                            'plan': row.get('plan', 'free'),
                                            'usage_count': 0,
                                            'usage_limit': int(row.get('usage_limit', 50)),
                                            'email_count': 0,
                                            'email_limit': int(row.get('email_limit', 100))
                                        }
                                        current_df = db.conn.read(ttl=0)
                                        updated_df = pd.concat([current_df, pd.DataFrame([new_user_data])], ignore_index=True)
                                        db.conn.update(data=updated_df)
                                else:
                                    # SQLite fallback
                                    if username in users_df['username'].values:
                                        db.update_user(
                                            row['username'], 
                                            new_role=row.get('role', 'user'),
                                            active=bool(row.get('active', 1)),
                                            plan=row.get('plan', 'free'),
                                            usage_limit=int(row.get('usage_limit', 50)),
                                            email_limit=int(row.get('email_limit', 100))
                                        )
                                    else:
                                        db.add_user(row['username'], "temp123", row.get('role', 'user'))
                                merged_count += 1
                            except Exception as e:
                                st.error(f"Error processing {row.get('username', 'unknown')}: {e}")
                        
                        st.success(f"✅ Successfully merged {merged_count} users!")
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Error processing backup: {e}")
    
    # Google Sheets Sync Status
    if db.use_gsheets:
        st.divider()
        st.subheader("🔄 Google Sheets Sync Status")
        
        try:
            df = db.conn.read(ttl=0)
            col_sync1, col_sync2, col_sync3 = st.columns(3)
            
            with col_sync1:
                st.metric("Total Records", len(df))
            
            with col_sync2:
                active_count = len(df[df['active'] == 1]) if not df.empty else 0
                st.metric("Active Users", active_count)
            
            with col_sync3:
                last_sync = datetime.now().strftime("%H:%M:%S")
                st.metric("Last Sync", last_sync)
                
            # Show sync log
            with st.expander("📋 Sync Details"):
                st.json({
                    "storage_type": "Google Sheets",
                    "total_users": len(df),
                    "active_users": active_count,
                    "connection_status": "Connected",
                    "last_refresh": last_sync
                })
                
        except Exception as e:
            st.error(f"❌ Google Sheets sync error: {e}")
            if st.button("🔄 Reconnect Google Sheets"):
                try:
                    # Force reconnection
                    df = db.conn.read(ttl=0)
                    st.success("✅ Reconnected to Google Sheets!")
                    st.rerun()
                except Exception as e2:
                    st.error(f"Reconnection failed: {e2}")
    
    # Emergency Export Section
    st.divider()
    st.subheader("🚨 Emergency Export")
    st.warning("Use this section if you need to quickly export all user data for migration or emergency backup.")
    
    if st.button("🚨 EMERGENCY: Export All User Data", use_container_width=True):
        try:
            if db.use_gsheets:
                df = db.conn.read(ttl=0)
            else:
                df = users_df
                
            if not df.empty:
                # Create comprehensive backup
                backup_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "storage_type": "Google Sheets" if db.use_gsheets else "SQLite",
                    "total_users": len(df),
                    "user_data": df.to_dict('records')
                }
                
                # Save as JSON
                json_data = json.dumps(backup_data, indent=2, default=str)
                st.download_button(
                    label="⚡ Download Emergency Backup (JSON)",
                    data=json_data,
                    file_name=f"emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime='application/json',
                    use_container_width=True
                )
                
                st.success("🚨 Emergency backup ready!")
            else:
                st.warning("No user data available for export.")
        except Exception as e:
            st.error(f"Emergency export failed: {e}")

def user_panel():
    st.markdown("""
        <div style="background-color: #2c3e50; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: white; margin: 0;">🌍 Google Maps Lead Scraper Pro</h2>
            <p style="color: #bdc3c7;">This is for Ti-Tech Software House Candidates. Generate high-quality business leads with advanced extraction.</p>
        </div>
    """, unsafe_allow_html=True)
    google_maps_scraping()

def more_features_tab():
    st.markdown("""
        <div style="background-color: #2c3e50; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: white; margin: 0;">🚀 More Features</h2>
            <p style="color: #bdc3c7;">Discover advanced features and premium tools for lead generation.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Redirecting to Advanced Features...")
    
    # JavaScript redirect
    st.markdown("""
        <script>
            window.open('https://business-lead-scraper-chka6fcq6jjuemaphapd9n.streamlit.app/', '_blank');
        </script>
    """, unsafe_allow_html=True)
    
    # Fallback button if JavaScript doesn't work
    if st.button("🚀 Open Advanced Features", use_container_width=True):
        st.markdown('[Click here to open Advanced Features](https://business-lead-scraper-chka6fcq6jjuemaphapd9n.streamlit.app/)', unsafe_allow_html=True)

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
            nav_options = ["🏠 Home / Scraper", "� More Features"]
            if st.session_state.user_role == 'admin':
                nav_options.append("🛡️ Admin Panel")
            
            # Find current index
            current_tab = st.session_state.get('current_tab', 'user')
            if current_tab == 'admin':
                default_idx = nav_options.index("🛡️ Admin Panel")
            elif current_tab == 'more_features':
                default_idx = nav_options.index("� More Features")
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
            elif nav_selection == "� More Features":
                st.session_state.current_tab = 'more_features'
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
        elif st.session_state.get('current_tab') == 'more_features':
            more_features_tab()
        else:
            user_panel()

if __name__ == "__main__":
    main()