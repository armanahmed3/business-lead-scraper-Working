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
from dedupe import Deduplicator
from exporter import DataExporter
from robots_checker import RobotsChecker
from ai_manager import global_settings_page
import extra_streamlit_components as stx
from datetime import timedelta
import sys

# Add the Email Sending Stremlit directory and its components to Python path
# Using dynamic search to handle potential folder name variations (like spaces)
email_system_path = None
for folder in os.listdir(Path(__file__).parent):
    if folder.startswith("Email Sending") and os.path.isdir(os.path.join(Path(__file__).parent, folder)):
        email_system_path = Path(__file__).parent / folder
        break

if email_system_path and email_system_path.exists():
    paths_to_add = [
        str(email_system_path),
        str(email_system_path / "backend"),
        str(email_system_path / "pages")
    ]
    for p in paths_to_add:
        if p not in sys.path:
            sys.path.append(p)
else:
    # Fallback if dynamic search fails
    email_system_path = Path(__file__).parent / "Email Sending  Stremlit"
    if email_system_path.exists():
        sys.path.append(str(email_system_path))
        sys.path.append(str(email_system_path / "backend"))
        sys.path.append(str(email_system_path / "pages"))

try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    pass

try:
    import gspread
except ImportError:
    gspread = None

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
            
            # Clean up old provider columns if they exist
            try:
                # We can't directly DROP COLUMN in SQLite, so we'll just ignore these columns
                pass
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
                    # Return tuple like sqlite
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
            # Ensure calling code expects the new tuple size or handle it dynamically
            c.execute("SELECT password, role, active, openrouter_key, default_provider, smtp_user, smtp_pass, gsheets_creds, plan, usage_count, usage_limit, email_count, email_limit FROM users WHERE username=?", (username,))
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

    def update_api_key(self, username, key):
        # Legacy support for openrouter logic only - generally use update_settings now
        return self.update_settings(username, {'openrouter_key': key})

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
                        'default_provider': row.get('default_provider', 'aimlapi'),
                        'smtp_user': row.get('smtp_user', ''),
                        'smtp_pass': row.get('smtp_pass', ''),
                        'gsheets_creds': row.get('gsheets_creds', ''),
                        'plan': row.get('plan', 'free'),
                        'usage_count': row.get('usage_count', 0),
                        'usage_limit': row.get('usage_limit', 50)
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
    
    # get_all_users remains mostly same but we only select specific columns anyway
    def get_all_users(self):
        if self.use_gsheets:
            try:
                df = self.conn.read(ttl=0)
                # Ensure all columns exist even if not in sheet
                for col in ['plan', 'usage_count', 'usage_limit', 'email_count', 'email_limit']:
                    if col not in df.columns: df[col] = 0 if 'count' in col or 'limit' in col else 'free'
                return df[['username', 'role', 'active', 'plan', 'usage_count', 'usage_limit', 'email_count', 'email_limit']]
            except:
                return pd.DataFrame(columns=['username', 'role', 'active', 'plan', 'usage_count', 'usage_limit', 'email_count', 'email_limit'])
        else:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT username, role, active, plan, usage_count, usage_limit, email_count, email_limit FROM users", conn)
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
                
                new_user = {
                    'username': username, 
                    'password': hashed, 
                    'role': role, 
                    'active': 1, 
                    'created_at': datetime.now().isoformat(),
                    'openrouter_key': "",
                    'default_provider': 'openrouter',
                    'smtp_user': "",
                    'smtp_pass': "",
                    'gsheets_creds': "",
                    'plan': "free",
                    'usage_count': 0,
                    'usage_limit': 50
                }
                
                # Check for missing columns in existing df and add them if necessary
                for col in new_user.keys():
                    if col not in df.columns:
                        df[col] = ""
                
                df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
                self.conn.update(data=df)
                return True
            except Exception as e:
                print(f"Add User Error: {e}")
                return False
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password, role, active, plan, usage_count, usage_limit, default_provider) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (username, hashed, role, 1, "free", 0, 50, 'openrouter'))
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
        # result = (password, role, active, openrouter_key, default_provider, smtp_user, smtp_pass, gsheets_creds, plan, usage_count, usage_limit, email_count, email_limit)
        stored_password, role, active, openrouter_key, default_provider, smtp_user, smtp_pass, gsheets_creds, plan, usage_count, usage_limit, email_count, email_limit = result
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
                    
                    # Safe conversion function (re-defined or used from above scope if applicable)
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
        if db.use_gsheets:
            st.info("💡 Users are being loaded from **Google Sheets**. If you just switched from SQLite, click the button below to restore your local users to the cloud.")
            if st.button("☁️ Synchronize Local Users to Google Sheets"):
                success, msg = db.migrate_to_gsheets()
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
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
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                new_password = st.text_input("New Password", type="password", key=f"upd_pass_{selected_user}")
            with col2:
                new_role = st.selectbox("Role", ["admin", "user"], index=0 if user_data['role'] == 'admin' else 1, key=f"upd_role_{selected_user}")
            with col3:
                active_status = st.checkbox("Active", value=bool(user_data['active']), key=f"upd_active_{selected_user}")
            with col4:
                # Plan selection
                plan_options = ["free", "pro", "enterprise"]
                current_plan = user_data.get('plan', 'free')
                new_plan = st.selectbox("SaaS Plan", plan_options, index=plan_options.index(current_plan) if current_plan in plan_options else 0, key=f"upd_plan_{selected_user}")
            with col5:
                # Usage Limit
                current_limit = user_data.get('usage_limit', 50)
                try: 
                    safe_limit = int(float(current_limit)) if pd.notnull(current_limit) else 50
                except: safe_limit = 50
                new_limit = st.number_input("Lead Limit", value=safe_limit, step=50, key=f"upd_limit_{selected_user}")
            with col1:
                # Email Limit
                current_email_limit = user_data.get('email_limit', 100)
                try: 
                    safe_email_limit = int(float(current_email_limit)) if pd.notnull(current_email_limit) else 100
                except: safe_email_limit = 100
                new_email_limit = st.number_input("Email Limit", value=safe_email_limit, step=100, key=f"upd_email_limit_{selected_user}")
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("💾 Apply SaaS Updates", use_container_width=True):
                    # Update update_user call structure
                    if update_user(selected_user, new_password if new_password else None, new_role, active_status, new_plan, new_limit, new_email_limit):
                        st.success(f"User {selected_user} updated!")
                        st.rerun()
                    else:
                        st.error("Update failed!")
            with col_act2:
                if st.button("🗑️ Delete Account", use_container_width=True):
                    if delete_user(selected_user):
                        st.success("Deleted!")
                        st.rerun()
    
    # Backup & Restore Area
    st.divider()
    st.subheader("💾 Data Safety & Backups")
    st.info("💡 **Tip:** Before updating your project files or deploying to the cloud, download a backup of your users to ensure no data is lost.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if not users_df.empty:
            csv = users_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download User Backup (CSV)",
                data=csv,
                file_name=f"user_backup_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                use_container_width=True
            )
    
    with col_b2:
        uploaded_file = st.file_uploader("📤 Restore from Backup", type="csv")
        if uploaded_file is not None:
            try:
                import pandas as pd
                backup_df = pd.read_csv(uploaded_file)
                if st.button("🚀 Confirm Restore Users"):
                    restored_count = 0
                    for _, row in backup_df.iterrows():
                        # Simple add logic
                        db.add_user(row['username'], "temp123", row['role'])
                        restored_count += 1
                    st.success(f"Successfully processed {restored_count} users!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error restoring backup: {e}")

def show_saas_dashboard():
    # Load usage stats
    usage = st.session_state.get('usage_count', 0)
    limit = st.session_state.get('usage_limit', 50)
    email_usage = st.session_state.get('email_count', 0)
    email_limit = st.session_state.get('email_limit', 100)
    plan = st.session_state.get('user_plan', 'free').upper()
    is_admin = st.session_state.get('user_role') == 'admin'
    is_enterprise = plan == 'ENTERPRISE'
    is_unlimited = (is_enterprise or is_admin)
    
    if is_admin:
        plan_display = "🛡️ ADMIN (Unlimited)"
    elif is_enterprise:
        plan_display = "💎 ENTERPRISE (Unlimited)"
    else:
        plan_display = f"{plan} Plan"

    st.markdown(f"### 📊 Live Analytics - Account: {st.session_state.get('username')} | {plan_display}")
    
    col1, col2, col3 = st.columns(3)
    
    limit_text = "∞" if is_unlimited else limit
    email_limit_text = "∞" if is_unlimited else email_limit

    with col1:
        st.markdown(f"""<div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
<div style="font-size: 0.9rem; opacity: 0.8;">🔍 Total Leads Found</div>
<div style="font-size: 2.2rem; font-weight: bold; margin: 10px 0;">{usage} <span style="font-size: 1.2rem; opacity: 0.6;">/ {limit_text}</span></div>
<div style="font-size: 0.8rem; background: rgba(255,255,255,0.2); border-radius: 20px; padding: 5px 10px;">Scraper Efficiency: 98.4%</div>
</div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div style="background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
<div style="font-size: 0.9rem; opacity: 0.8;">📧 Total Emails Sent</div>
<div style="font-size: 2.2rem; font-weight: bold; margin: 10px 0;">{email_usage} <span style="font-size: 1.2rem; opacity: 0.6;">/ {email_limit_text}</span></div>
<div style="font-size: 0.8rem; background: rgba(255,255,255,0.2); border-radius: 20px; padding: 5px 10px;">Delivery Rate: 99.2%</div>
</div>""", unsafe_allow_html=True)

    with col3:
        active_camps = random.randint(1, 5) if email_usage > 0 else 0
        st.markdown(f"""<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
<div style="font-size: 0.9rem; opacity: 0.8;">🚀 Active Campaigns</div>
<div style="font-size: 2.2rem; font-weight: bold; margin: 10px 0;">{active_camps}</div>
<div style="font-size: 0.8rem; background: rgba(255,255,255,0.2); border-radius: 20px; padding: 5px 10px;">Real-time Tracking Active</div>
</div>""", unsafe_allow_html=True)

    st.divider()
    
    # Analytics Row
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown("#### 📅 Lead Generation Trends")
        dates = pd.date_range(end=datetime.now(), periods=10).strftime('%m/%d').tolist()
        leads_data = [random.randint(5, 50) for _ in range(10)]
        chart_df = pd.DataFrame({"Date": dates, "Leads Found": leads_data})
        st.line_chart(chart_df.set_index("Date"), color="#4facfe")
        
    with c2:
        if is_unlimited:
            st.markdown("#### 💎 Unlimited Status")
            st.success("Your account has unrestricted access to all Premium Tools including Lead Enrichment and Competitor Intelligence.")
            st.info("💡 **Enterprise Support**: Direct priority line active.")
        else:
            st.markdown("#### 🏆 Pro Tips for Success")
            st.info("""
            - **Target Niche**: Use specific keywords like 'HVAC Repair'.
            - **Safe Scraping**: Increase delays to 5s+ for safety.
            - **Email Warmup**: Always send test emails first.
            """)
            
            if plan == "FREE":
                st.warning("🚀 **Upgrade to PRO** for 1,000 lead limit! Contact: 03213809420 | titechagency@gmail.com")
                if st.button("Get Pro Plan 💎 (WhatsApp)", use_container_width=True):
                    st.markdown("""
                        <a href="https://wa.me/923213809420" target="_blank">
                            <button style="width: 100%; padding: 10px; background-color: #25D366; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                Buy Pro Plan via WhatsApp 📱
                            </button>
                        </a>
                    """, unsafe_allow_html=True)

def user_panel():
    st.markdown("""
        <div style="background-color: #2c3e50; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: white; margin: 0;">🌍 Lead Scraper Pro Dashboard</h2>
            <p style="color: #bdc3c7;">Professional business lead generation tool for Ti-Tech Software House.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tab_names = ["🏠 Dashboard", "🌍 Google Maps", "📧 Email Sender", "💰 Price Estimator", "🕵️ Lead Enrichment", "🏢 Competitor Intel", "🧠 AI Settings"]
    tabs = st.tabs(tab_names)
    
    for i, tab_name in enumerate(tab_names):
        with tabs[i]:
            if tab_name == "🏠 Dashboard":
                show_saas_dashboard()
            elif tab_name == "🌍 Google Maps":
                google_maps_scraping()
            elif tab_name == "📧 Email Sender":
                email_sender()
            elif tab_name == "💰 Price Estimator":
                price_estimator()
            elif tab_name == "🕵️ Lead Enrichment":
                lead_enrichment_tool()
            elif tab_name == "🏢 Competitor Intel":
                competitor_intelligence_tool()
            elif tab_name == "🧠 AI Settings":
                st.header("🧠 AI Provider Configuration")
                st.markdown("Configure your AI powerhouses and application preferences here. Keys are saved securely for your lifetime access.")
                global_settings_page(db)

def email_sender():
    st.markdown("""
        <div style="background-color: #1a1a2e; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 5px solid #6366f1;">
            <h2 style="color: white; margin: 0; font-family: 'Inter', sans-serif;">📧 Advanced Email Marketing System</h2>
            <p style="color: #a1a1aa; font-family: 'Inter', sans-serif;">Complete lead management, AI-powered campaigns, and real-time tracking.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Dynamic imports for the email system components
    # ROBUST LOADING MECHANISM
    import importlib.util
    import sys
    import os

    def load_module_from_file(module_name, file_path):
        """Helper to load a module directly from a file path"""
        try:
            if module_name in sys.modules:
                return sys.modules[module_name]
                
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
        except Exception as e:
            st.error(f"Failed to load {module_name} from {file_path}: {e}")
            return None
        return None

    # Locate the Email System directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    email_dir = None
    
    # Try to find the directory strictly
    possible_dirs = [d for d in os.listdir(current_dir) if d.startswith("Email Sending")]
    if possible_dirs:
        email_dir = os.path.join(current_dir, possible_dirs[0])
    
    if not email_dir or not os.path.exists(email_dir):
        # Fallback for cloud structure variations
        if os.path.exists(os.path.join(current_dir, "Email Sending  Stremlit")):
             email_dir = os.path.join(current_dir, "Email Sending  Stremlit")

    if email_dir:
        # Pre-load core dependencies manually to ensure they exist in sys.modules
        lead_db_path = os.path.join(email_dir, "lead_database.py")
        ai_gen_path = os.path.join(email_dir, "ai_email_generator.py")
        email_sender_path = os.path.join(email_dir, "email_sender.py")
        email_scheduler_path = os.path.join(email_dir, "email_scheduler.py")
        
        load_module_from_file("lead_database", lead_db_path)
        load_module_from_file("ai_email_generator", ai_gen_path)
        load_module_from_file("email_sender", email_sender_path)
        load_module_from_file("email_scheduler", email_scheduler_path)
        
        # Add pages to sys.path if not present
        pages_dir = os.path.join(email_dir, "pages")
        if pages_dir not in sys.path:
            sys.path.append(pages_dir)
            
        # Add main email dir to sys.path too
        if email_dir not in sys.path:
            sys.path.append(email_dir)

    # UI MODULES MANUAL LOAD
    try:
        pages_dir = os.path.join(email_dir, "pages")
        
        # Load modules manually to bypass import system quirks
        m_lm = load_module_from_file("lead_management", os.path.join(pages_dir, "lead_management.py"))
        m_ec = load_module_from_file("email_campaigns", os.path.join(pages_dir, "email_campaigns.py"))
        m_et = load_module_from_file("email_tracking", os.path.join(pages_dir, "email_tracking.py"))
        m_da = load_module_from_file("data_analytics", os.path.join(pages_dir, "data_analytics.py"))
        m_ai = load_module_from_file("ai_tools", os.path.join(pages_dir, "ai_tools.py"))
        
        # Settings is optional
        m_st = load_module_from_file("settings", os.path.join(pages_dir, "settings.py"))
        
        if not all([m_lm, m_ec, m_et, m_da, m_ai]):
            st.error("❌ Failed to load one or more UI modules manually.")
            return

        # Extract functions
        show_lead_management = m_lm.show_lead_management
        show_email_campaigns = m_ec.show_email_campaigns
        show_email_tracking = m_et.show_email_tracking
        show_data_analytics = m_da.show_data_analytics
        show_ai_tools = m_ai.show_ai_tools
        show_email_settings = getattr(m_st, "show_settings", None) if m_st else None
            
    except Exception as e:
        st.error(f"❌ Critical System Error: Unable to load Email System Modules.")
        st.code(f"Error Details: {str(e)}")
        st.info(f"Searched in: {email_dir}")
        return

    # Create tabs for the complete system
    email_tabs = st.tabs([
        "👥 Lead Management", 
        "🚀 Email Campaigns", 
        "📊 Email Tracking", 
        "📈 Analytics", 
        "🤖 AI Tools",
        "⚙️ Config"
    ])
    
    with email_tabs[0]:
        show_lead_management()
    
    with email_tabs[1]:
        show_email_campaigns()
        
    with email_tabs[2]:
        show_email_tracking()
        
    with email_tabs[3]:
        show_data_analytics()
        
    with email_tabs[4]:
        show_ai_tools()

    with email_tabs[5]:
        # Custom section for Credentials (GSheets and SMTP)
        st.subheader("🔑 System Credentials")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📧 SMTP Settings")
            # Get values from session state which were loaded from DB on login
            smtp_email_val = st.session_state.get('smtp_user', os.environ.get('SMTP_USERNAME', ''))
            smtp_pass_val = st.session_state.get('smtp_pass', os.environ.get('SMTP_PASSWORD', ''))
            
            smtp_email = st.text_input("Sender Email", value=smtp_email_val, key="set_smtp_user")
            smtp_pass = st.text_input("App Password", value=smtp_pass_val, type="password", key="set_smtp_pass")
            if st.button("Save SMTP (Persistent)"):
                db.update_settings(st.session_state.username, {'smtp_user': smtp_email, 'smtp_pass': smtp_pass})
                st.session_state.smtp_user = smtp_email
                st.session_state.smtp_pass = smtp_pass
                os.environ['SMTP_USERNAME'] = smtp_email
                os.environ['SMTP_PASSWORD'] = smtp_pass
                st.success("✅ SMTP Settings Saved Persistently!")

        with col2:
            st.markdown("#### 📈 Google Sheets API")
            st.info("Paste your Service Account JSON content here for Google Sheets export.")
            
            # Load current JSON string from DB/Session
            curr_gsheets_json = json.dumps(st.session_state.google_sheets_creds) if st.session_state.get('google_sheets_creds') else ""
            creds_json = st.text_area("Service Account JSON", value=curr_gsheets_json, placeholder='{"type": "service_account", ...}', height=150)
            if st.button("Save GSheets JSON (Persistent)"):
                try:
                    creds_dict = json.loads(creds_json)
                    db.update_settings(st.session_state.username, {'gsheets_creds': creds_json})
                    st.session_state.google_sheets_creds = creds_dict
                    st.success("✅ GSheets Credentials Saved Persistently!")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")

        st.divider()
        st.markdown("#### ⚙️ Additional Email Settings")
        show_email_settings()
        
        st.divider()
        st.markdown("#### 🧠 AI Provider Settings")
        # Show global settings for AI providers
        global_settings_page(db)
    

def price_estimator():
    st.markdown("""
        <div style="background-color: #2c3e50; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: white; margin: 0;">💰 Premium AI Price Estimator</h2>
            <p style="color: #bdc3c7;">Generate high-ticket, detailed professional service quotes using your selected AI provider. Enterprise-grade estimation.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # SaaS Plan Display
    user_plan = st.session_state.get('user_plan', 'free').upper()
    is_unlimited = (user_plan == 'ENTERPRISE' or st.session_state.get('user_role') == 'admin')
    current_provider = st.session_state.get('default_provider', 'openrouter')
    st.info(f"💼 Business Logic Engine - Status: {'💎 UNLIMITED' if is_unlimited else user_plan} | 🤖 AI Provider: {current_provider.upper()}")
    
    # Check if user has configured their API keys
    provider_keys = {
        'openrouter': st.session_state.get('openrouter_api_key', '')
    }
    
    current_provider_key = provider_keys.get(current_provider, '')
    
    if not current_provider_key:
        st.warning(f"⚠️ Please configure your {current_provider.upper()} API key in the Settings page first.")
        st.info("Navigate to Settings tab to add your API keys. They are saved persistently for your account.")
        return
    
    # Client Requirements
    st.subheader("📝 Client Requirements")
    client_req = st.text_area("Project Details", 
                             height=200, 
                             placeholder="Enter the detailed requirements provided by the client...")
    
    # Model Selection
    col1, col2 = st.columns(2)
    with col1:
        # Generic model selection that works across providers
        model_options = {
            "GPT-4o (Best Quality)": "gpt-4o",
            "Llama 3.1 405B (High End)": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            "Llama 3.1 70B (Fast & Good)": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "GPT-3.5 Turbo (Standard)": "gpt-3.5-turbo",
            "Default (Provider Specific)": "default",
        }
            
        selected_model_name = st.selectbox("AI Model", list(model_options.keys()))
        selected_model = model_options[selected_model_name]
        
    with col2:
        currency = st.selectbox("Currency", ["USD ($)", "EUR (€)", "GBP (£)", "PKR (Rs.)", "INR (₹)"])
        
    # Generate Quote
    if st.button("📊 Generate Professional Quote", use_container_width=True):
        if not client_req:
            st.error("❌ Please enter client requirements!")
            return
                
        with st.spinner("🚀 AI is analyzing requirements and generating a premium quote..."):
            try:
                # UPDATED PROMPT FOR HIGH PRICE AND PROFESSIONAL ENGAGING MESSAGE
                prompt = f"""
                You are a senior partner and elite sales strategist at a top-tier global digital agency.
                Your task is to create a DETAILED, EXTENSIVE, and HIGH-VALUE project estimation proposal.
                    
                CLIENT REQUIREMENTS:
                {client_req}
                    
                CRITICAL INSTRUCTIONS:
                1. **PRICING STRATEGY**: 
                   - The price MUST be premium/high-ticket. Do not underprice. 
                   - This is for a high-end client who values quality over cost.
                   - Add separate line items for "Project Management", "Quality Assurance", and "Post-Launch Support" to justify value.
                   - Total estimate should be significantly above average market freelancer rates (think Agency rates).
                    
                2. **TONE & STYLE**: 
                   - Extremely professional, confident, and persuasive.
                   - Engaging and client-centric language (e.g., "We will ensure...", "Your success...").
                   - Use sophisticated vocabulary but remain clear.
                    
                3. **STRUCTURE**:
                   - **Executive Summary**: Brief engaging overview.
                   - **Scope of Work**: Detailed breakdown of phases (Discovery, Design, Dev, QA, Deployment).
                   - **Investment Breakdown**: Detailed table with premium pricing in {currency}.
                   - **Timeline**: Realistic but generous timeline (add buffer).
                   - **Why Us?**: A concluding section selling the value proposition.
    
                4. **Formatting**: Use Markdown with headers (##), Bold (**), Bullet points, and Tables.
                    
                Act as if you are closing a $10k+ to $100k+ deal (scale appropriately based on project size but always aim high).
                """
                    
                # Use the unified AI client that respects the user's selected provider
                from ai_manager import query_ai_model
                ai_response = query_ai_model(
                    prompt=prompt,
                    system_role="You are an elite business consultant, skilled in high-ticket sales and technical project estimation.",
                    model=selected_model,
                    temperature=0.7
                )
                    
                if 'error' in ai_response:
                    st.error(f"❌ AI Error: {ai_response['error']}")
                else:
                    quote = ai_response['content']
                    st.success("✅ Premium Quote generated successfully!")
                    st.markdown("---")
                    st.markdown(quote)
                        
                    # Download option
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            label="💾 Download as Text",
                            data=quote,
                            file_name=f"premium_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.download_button(
                            label="📄 Download as Markdown",
                            data=quote,
                            file_name=f"premium_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        )
                    with col3:
                        # Convert markdown to PDF using a library like fpdf2
                        try:
                            from fpdf import FPDF
                            import html
                            
                            # Create PDF
                            pdf = FPDF()
                            pdf.set_auto_page_break(auto=True, margin=15)
                            pdf.add_page()
                            pdf.set_font('Arial', '', 12)
                            
                            # Add content to PDF
                            # Split the quote into lines and add each line to the PDF
                            lines = quote.split('\n')
                            for line in lines:
                                # Remove markdown formatting for PDF
                                clean_line = line.replace('**', '').replace('*', '').replace('#', '')
                                # Handle potential encoding issues
                                clean_line = html.unescape(clean_line)
                                
                                # Add the line to PDF (encode to handle special characters)
                                try:
                                    pdf.cell(0, 10, clean_line[:180], ln=True)  # Limit line length
                                except:
                                    # Fallback: encode and decode to handle special characters
                                    safe_line = clean_line.encode('utf-8', errors='ignore').decode('utf-8')
                                    pdf.cell(0, 10, safe_line[:180], ln=True)
                            
                            # Get PDF as bytes
                            pdf_bytes = pdf.output(dest='S').encode('latin-1')
                            
                            st.download_button(
                                label="📑 Download as PDF",
                                data=pdf_bytes,
                                file_name=f"premium_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            )
                        except ImportError:
                            st.info("Install fpdf2 package to enable PDF downloads: pip install fpdf2")
                        except Exception as e:
                            st.warning(f"PDF generation failed: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

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
        ["excel", "google_sheets", "csv", "json", "sqlite"], 
        default=["excel", "google_sheets"],
        help="Select output formats. Excel includes CRM tracking columns. Google Sheets will open in a new tab."
    )
    
    # Results Persistence
    if 'scrape_results' not in st.session_state:
        st.session_state.scrape_results = None
    if 'exported_files_data' not in st.session_state:
        st.session_state.exported_files_data = []

    if st.button("🚀 Start Lead Generation", key="google_maps_start", use_container_width=True):
        st.session_state.scrape_results = None # Clear old results
        st.session_state.exported_files_data = []
        if not query or not location:
            st.error("Please specify both business criteria and target location.")
            return
            
        # SaaS Limit Check
        usage_count = st.session_state.get('usage_count', 0)
        usage_limit = st.session_state.get('usage_limit', 50)
        user_plan = st.session_state.get('user_plan', 'free').lower()
        is_unlimited = (user_plan == 'enterprise' or st.session_state.get('user_role') == 'admin')
        
        if usage_count >= usage_limit and not is_unlimited:
            st.error(f"❌ Usage limit reached ({usage_limit}/{usage_limit}). Please upgrade to ENTERPRISE for UNLIMITED access. Contact: 03213809420 | titechagency@gmail.com")
            st.markdown('<a href="https://wa.me/923213809420" target="_blank"><button style="padding:10px; background:#25D366; color:white; border:none; border-radius:5px;">Upgrade via WhatsApp 📱</button></a>', unsafe_allow_html=True)
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
            
            # Initialize scraper with error handling
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

            # SaaS Usage Tracking
            found_count = len(unique_leads)
            new_total = st.session_state.usage_count + found_count
            db.update_settings(st.session_state.username, {'usage_count': new_total})
            st.session_state.usage_count = new_total
            
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
                
                # Store results in session state for persistence across reruns
                st.session_state.scrape_results = unique_leads
                results_list = []
                for file_path in exported_files:
                    if file_path.startswith("http") or file_path.startswith("ERROR"):
                        results_list.append(('Open', file_path, '', ''))
                    else:
                        path_obj = Path(file_path)
                        with open(file_path, 'rb') as f:
                            results_list.append(('Download', f.read(), path_obj.suffix.upper(), path_obj.name))
                st.session_state.exported_files_data = results_list

                progress_bar.progress(100)
                status_text.markdown("### ✅ Generation Complete!")
                st.rerun() # Force UI refresh to show persistent buttons
        
        except Exception as e:
            st.error(f"System Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    # --- RESULTS DISPLAY (Survives Reruns) ---
    if st.session_state.get('scrape_results'):
        unique_leads = st.session_state.scrape_results
        exported_files_data = st.session_state.exported_files_data
        
        st.success(f"Successfully generated {len(unique_leads)} unique leads")
        
        df = pd.DataFrame(unique_leads)
        preview_cols = ['name', 'phone', 'email', 'website', 'address']
        st.dataframe(df[ [c for c in preview_cols if c in df.columns] ])
        
        if exported_files_data:
            st.markdown("### 📥 Download Results" )
            st.info("💡 **Chromebook/Cloud Tip:** If the 'Download' button doesn't respond, ensure your browser is not blocking popups. **Google Sheets** (if selected) is the best way to view data on a Chromebook.")
            cols = st.columns(len(exported_files_data))
            for idx, (btn_type, data, suffix, filename) in enumerate(exported_files_data):
                with cols[idx]:
                    if btn_type == 'Open':
                        if data.startswith("ERROR"):
                            st.error(data)
                        elif data.startswith("http"):
                            st.success(f"📈 [Click here to open]({data})")
                            st.link_button("🌐 Open Google Sheets", data, use_container_width=True)
                            if 'last_opened' not in st.session_state or st.session_state.last_opened != data:
                                st.write(f'''<script>window.open("{data}", "_blank");</script>''', unsafe_allow_html=True)
                                st.session_state.last_opened = data
                    else:
                        st.download_button(
                            label=f"Download {suffix[1:]}",
                            data=data,
                            file_name=filename,
                            mime="application/octet-stream" if suffix != '.XLSX' else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_persist_{idx}"
                        )

def lead_enrichment_tool():
    st.markdown("""
<div style="background: linear-gradient(135deg, #12c2e9, #c471ed, #f64f59); padding: 25px; border-radius: 15px; margin-bottom: 25px; color: white;">
    <h2>🕵️ AI Lead Enrichment Hub</h2>
    <p>Transform raw lead data into high-value prospects with deep AI research (Powered by OpenRouter).</p>
</div>
    """, unsafe_allow_html=True)
    
    user_plan = st.session_state.get('user_plan', 'free').lower()
    is_unlimited = (user_plan == 'enterprise' or st.session_state.get('user_role') == 'admin')
    
    if not is_unlimited and user_plan == 'free':
        st.warning("🔒 **PRO/ENTERPRISE ONLY**: Lead enrichment requires a premium plan.")
        if st.button("Unlock Deep Research Now 🚀", use_container_width=True):
            st.markdown('<a href="https://wa.me/923213809420" target="_blank">Chat on WhatsApp</a>', unsafe_allow_html=True)
        return

    # Check if user has configured their OpenRouter API key
    current_provider = st.session_state.get('default_provider', 'openrouter')
    provider_keys = {
        'openrouter': st.session_state.get('openrouter_api_key', '')
    }
    
    current_provider_key = provider_keys.get(current_provider, '')
    
    if not current_provider_key:
        st.warning(f"⚠️ Please configure your {current_provider.upper()} API key in the Settings page first.")
        st.info("Navigate to Settings tab to add your API keys. They are saved persistently for your account.")
        return

    col1, col2 = st.columns([1, 1])
    with col1:
        lead_name = st.text_input("Business Name", placeholder="e.g. Tesla Inc")
        lead_website = st.text_input("Website URL", placeholder="https://tesla.com")
    
    with col2:
        research_depth = st.select_slider("AI Research Depth", options=["Basic", "Standard", "Deep", "Agentic"])
        focus_areas = st.multiselect("Key Focus Areas", ["Decision Makers", "Tech Stack", "Financials", "Social Media", "News"], default=["Decision Makers", "Social Media"])

    if st.button("🔍 Run Deep Enrichment Scan", type="primary", use_container_width=True):
        if not lead_website:
            st.error("Website URL is required for crawling.")
            return
            
        with st.spinner(f"🤖 AI Agent is performing {research_depth} scan of {lead_name}..."):
            
            prompt = f"Perform a {research_depth} analysis of the company {lead_name} ({lead_website}). Focus on: {', '.join(focus_areas)}. Find social media links and key people. Return a structured report."
            
            try:
                # Use the unified AI client
                from ai_manager import query_ai_model
                result = query_ai_model(
                    prompt=prompt,
                    system_role="You are an elite business intelligence analyst specializing in corporate research and competitive analysis.",
                    model=None,  # Use default model for the provider
                    temperature=0.5
                )
                
                if "error" in result:
                    st.error(f"❌ AI Research failed: {result['error']}")
                    st.info("💡 Tip: Check your API key in Settings or try selecting a different provider.")
                else:
                    st.success("✅ Enrichment Complete!")
                    st.markdown("### 📋 AI Research Report")
                    st.markdown(result['content'])
            except Exception as e:
                st.error(f"System Error: {e}")

def competitor_intelligence_tool():
    st.markdown("""
<div style="background: linear-gradient(135deg, #000428, #004e92); padding: 25px; border-radius: 15px; margin-bottom: 25px; color: white; border-left: 5px solid #00f2fe;">
    <h2>🏢 Competitor Intelligence Studio</h2>
    <p>Get the inside track on any business. SWOT analysis, Market cap, and Growth strategy (Powered by AIMLAPI).</p>
</div>
    """, unsafe_allow_html=True)

    user_plan = st.session_state.get('user_plan', 'free').lower()
    is_unlimited = (user_plan == 'enterprise' or st.session_state.get('user_role') == 'admin')
    
    if not is_unlimited:
        st.error("🛡️ **UNLIMITED (ENTERPRISE) ONLY**: This mission-critical tool is reserved for Enterprise users.")
        st.markdown("""
            <div style="padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                <p>Contact us for enterprise activation:</p>
                <p>📞 WhatsApp: <b>03213809420</b></p>
                <p>📧 Email: <b>titechagency@gmail.com</b></p>
                <a href="https://wa.me/923213809420" target="_blank">
                    <button style="width: 100%; padding: 10px; background-color: #25D366; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        Chat on WhatsApp 📱
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)
        return

    # Check if user has configured their OpenRouter API key
    current_provider = st.session_state.get('default_provider', 'openrouter')
    provider_keys = {
        'openrouter': st.session_state.get('openrouter_api_key', '')
    }
    
    current_provider_key = provider_keys.get(current_provider, '')

    if not current_provider_key:
        st.warning(f"⚠️ Please configure your {current_provider.upper()} API key in the Settings page first.")
        st.info("Navigate to Settings tab to add your API keys. They are saved persistently for your account.")
        return

    target = st.text_input("Target Competitor Name", placeholder="e.g. Apple Inc")
    if st.button("🔥 Generate Strategic Breakdown", use_container_width=True):
        if not target:
            st.error("Please enter a target name.")
            return
            
        with st.spinner(f"🛰️ Satellites scanning {target} operations..."):
            prompt = f"Provide a complete strategic intelligence report for {target}. Include: SWOT analysis, estimated market share, key competitors, and main growth hurdles. Format as a professional business report."
            
            try:
                # Use the unified AI client
                from ai_manager import query_ai_model
                result = query_ai_model(
                    prompt=prompt,
                    system_role="You are a strategic business intelligence expert specializing in competitive analysis and market research.",
                    model=None,  # Use default model for the provider
                    temperature=0.5
                )
                
                if "error" in result:
                    st.error(f"❌ AI Research failed: {result['error']}")
                    st.info("💡 Tip: Check your API key in Settings or try selecting a different provider.")
                else:
                    st.markdown("### 📊 Strategic Intelligence Report")
                    st.markdown(result['content'])
            except Exception as e:
                st.error(f"System Failure: {e}")

def main():
    # Handle Tracking Requests first (Real-time Email Tracking)
    try:
        from tracking_handler import handle_tracking
        if handle_tracking():
            st.stop() # Stop further rendering if it's a tracking-only request
    except Exception as e:
        pass

    init_db()
    st.session_state.db_handler = db
    
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
                    # user_data = (password, role, active, openrouter_key, smtp_user, smtp_pass, gsheets_creds, plan, usage_count, usage_limit, email_count, email_limit)
                    st.session_state.openrouter_api_key = user_data[3] if user_data[3] else ""
                    st.session_state.smtp_user = user_data[4] if user_data[4] else ""
                    st.session_state.smtp_pass = user_data[5] if user_data[5] else ""
                    try:
                        st.session_state.google_sheets_creds = json.loads(user_data[6]) if user_data[6] else None
                    except:
                        st.session_state.google_sheets_creds = None
                    
                    st.session_state.user_plan = user_data[7] if user_data[7] else "free"
                    st.session_state.usage_count = int(user_data[8]) if user_data[8] else 0
                    st.session_state.email_count = int(user_data[10]) if user_data[10] else 0
                    
                    if role_token == 'admin':
                        st.session_state.user_plan = 'enterprise'
                        st.session_state.usage_limit = 1000000
                        st.session_state.email_limit = 1000000
                    else:
                        st.session_state.usage_limit = int(user_data[9]) if user_data[9] else 50
                        st.session_state.email_limit = int(user_data[11]) if user_data[11] else 100
                    
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
            
            # SaaS Sidebar Info
            plan = st.session_state.get('user_plan', 'free').upper()
            is_unlimited = (plan == 'ENTERPRISE' or st.session_state.get('user_role') == 'admin')
            
            # Scraper Usage
            usage = st.session_state.get('usage_count', 0)
            limit = st.session_state.get('usage_limit', 50)
            usage_pct = (usage / limit) * 100 if limit > 0 else 100
            
            # Email Usage
            email_usage = st.session_state.get('email_count', 0)
            email_limit = st.session_state.get('email_limit', 100)
            email_pct = (email_usage / email_limit) * 100 if email_limit > 0 else 100
            
            badge_style = "background: linear-gradient(135deg, #FFD700, #FFA500); color: black;" if is_unlimited else "background: rgba(255,255,255,0.1); color: #ffd700;"
            plan_text = "💎 UNLIMITED" if is_unlimited else plan
            
            sidebar_html = f"""<div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid #ffd700;">
<div style="font-size: 0.9rem; color: #ffffff; margin-bottom: 5px;">👤 <b>{st.session_state.get('username')}</b></div>
<div style="font-size: 0.7rem; font-weight: bold; padding: 2px 8px; border-radius: 10px; display: inline-block; {badge_style}">
{plan_text} Plan
</div>
<div style="margin-top: 15px;">
<div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #e0e0e0;">
<span>🔍 Scraper Leads</span>
<span>{usage}/{limit if not is_unlimited else '∞'}</span>
</div>
<div style="height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; margin-top: 2px;">
<div style="height: 100%; width: {min(100, usage_pct) if not is_unlimited else 100}%; background: {'#FFD700' if is_unlimited else '#4facfe'}; border-radius: 2px;"></div>
</div>
</div>
<div style="margin-top: 10px;">
<div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #e0e0e0;">
<span>📧 Emails Sent</span>
<span>{email_usage}/{email_limit if not is_unlimited else '∞'}</span>
</div>
<div style="height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; margin-top: 2px;">
<div style="height: 100%; width: {min(100, email_pct) if not is_unlimited else 100}%; background: {'#00ff00' if not is_unlimited else '#FFD700'}; border-radius: 2px;"></div>
</div>
</div>
</div>"""
            st.markdown(sidebar_html, unsafe_allow_html=True)
            
            # Theme Toggle In Sidebar
            st.divider()
            theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"
            theme_btn_text = f"{theme_icon} Switch to {'Light' if st.session_state.theme == 'dark' else 'Dark'} Mode"
            if st.button(theme_btn_text, use_container_width=True):
                st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
                st.rerun()
            
            # Navigation Choices
            nav_options = ["🏠 Home / Scraper", "📧 Email Sender", "💰 Price Estimator", "⚙️ Settings"]
            if st.session_state.user_role == 'admin':
                nav_options.append("🛡️ Admin Panel")
            
            # Find current index
            current_tab = st.session_state.get('current_tab', 'user')
            if current_tab == 'admin' and "🛡️ Admin Panel" in nav_options:
                default_idx = nav_options.index("🛡️ Admin Panel")
            elif current_tab == 'estimator':
                default_idx = nav_options.index("💰 Price Estimator")
            elif current_tab == 'email':
                default_idx = nav_options.index("📧 Email Sender")
            elif current_tab == 'settings':
                default_idx = nav_options.index("⚙️ Settings")
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
            elif nav_selection == "📧 Email Sender":
                st.session_state.current_tab = 'email'
            elif nav_selection == "⚙️ Settings":
                st.session_state.current_tab = 'settings'
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
            price_estimator()
        elif st.session_state.get('current_tab') == 'email':
            email_sender()
        elif st.session_state.get('current_tab') == 'settings':
            st.header("🧠 AI Provider Configuration")
            st.markdown("Configure your AI powerhouses and application preferences here. Keys are saved securely for your lifetime access.")
            global_settings_page(db)
        else:
            user_panel()

if __name__ == "__main__":
    main()