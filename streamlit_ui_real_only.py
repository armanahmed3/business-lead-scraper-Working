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
        paths_to_add = [
            str(email_system_path),
            str(email_system_path / "backend"),
            str(email_system_path / "pages")
        ]
        for p in paths_to_add:
            if p not in sys.path:
                sys.path.append(p)

# Import email system components if available
try:
    from backend.database import get_db_connection
    from backend.services.lead_service import LeadService
    from backend.models import Lead
except ImportError:
    get_db_connection = None
    LeadService = None
    Lead = None
    st.warning("Email system components not available. Some features may be limited.")

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0
if 'scrape_results' not in st.session_state:
    st.session_state.scrape_results = []
if 'exported_files_data' not in st.session_state:
    st.session_state.exported_files_data = []

# Configure page
st.set_page_config(
    page_title="Business Lead Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def authenticate_user(username, password):
    """Authenticate user against database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT username, api_keys, settings FROM users 
            WHERE username = ? AND password = ?
        """, (username, hashed_password))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            username, api_keys_json, settings_json = result
            api_keys = json.loads(api_keys_json) if api_keys_json else {}
            settings = json.loads(settings_json) if settings_json else {}
            
            return True, username, api_keys, settings
        else:
            return False, None, None, None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False, None, None, None

def register_user(username, password):
    """Register new user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Default settings
        default_settings = {
            'usage_count': 0,
            'max_daily_usage': 100,
            'subscription_type': 'free',
            'last_reset_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        cursor.execute("""
            INSERT INTO users (username, password, api_keys, settings)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_password, '{}', json.dumps(default_settings)))
        
        conn.commit()
        conn.close()
        
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False

def update_usage(username, increment=1):
    """Update user's usage count."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT settings FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            settings = json.loads(result[0])
            settings['usage_count'] = settings.get('usage_count', 0) + increment
            settings['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(
                "UPDATE users SET settings = ? WHERE username = ?",
                (json.dumps(settings), username)
            )
            conn.commit()
        
        conn.close()
    except Exception as e:
        st.error(f"Usage update error: {str(e)}")

def main():
    st.title("🔍 Business Lead Scraper")
    st.markdown("---")
    
    # Authentication
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.header("🔐 Login")
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                
                if submitted:
                    if username and password:
                        success, user, api_keys, settings = authenticate_user(username, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.username = user
                            st.session_state.usage_count = settings.get('usage_count', 0)
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.error("Please enter both username and password")
            
            st.markdown("---")
            st.header("📝 Register")
            
            with st.form("register_form"):
                new_username = st.text_input("New Username", key="reg_username")
                new_password = st.text_input("New Password", type="password", key="reg_password")
                reg_submitted = st.form_submit_button("Register")
                
                if reg_submitted:
                    if new_username and new_password:
                        if len(new_password) < 6:
                            st.error("Password must be at least 6 characters")
                        else:
                            success = register_user(new_username, new_password)
                            if success:
                                st.success("Registration successful! Please login.")
                            else:
                                st.error("Username already exists")
                    else:
                        st.error("Please enter both username and password")
    else:
        # Main app
        st.sidebar.title(f"Welcome, {st.session_state.username}! 👋")
        st.sidebar.markdown(f"**Usage today:** {st.session_state.usage_count}")
        
        # Navigation
        pages = ["Lead Generator", "Analytics", "Settings"]
        page = st.sidebar.selectbox("Navigation", pages)
        
        if page == "Lead Generator":
            lead_generator_page()
        elif page == "Analytics":
            analytics_page()
        elif page == "Settings":
            settings_page()
        
        # Logout button
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.usage_count = 0
            st.session_state.scrape_results = []
            st.session_state.exported_files_data = []
            st.rerun()

def lead_generator_page():
    st.header("🏢 Business Lead Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        query = st.text_input("Business Type", placeholder="e.g., restaurants, dentists, hotels")
        location = st.text_input("Location", placeholder="e.g., New York, London, Birmingham, AL")
    
    with col2:
        max_leads = st.number_input("Max Leads", min_value=1, max_value=100, value=20, step=1)
        delay = st.slider("Delay (seconds)", min_value=0.5, max_value=5.0, value=1.0, step=0.1)
    
    formats = st.multiselect(
        "Export Formats",
        ["CSV", "JSON", "Excel", "SQLite"],
        default=["CSV", "JSON"]
    )
    
    if st.button("🚀 Generate Leads", type="primary"):
        if not query or not location:
            st.error("Please enter both business type and location")
            return
        
        # Status containers
        status_text = st.empty()
        progress_bar = st.progress(0)
        results_container = st.container()
        
        status_text.markdown("### 🔧 Setting Up Configuration...")
        progress_bar.progress(5)
        
        # Create config
        config = Config()
        
        # Update config based on user settings
        config._config['scraping']['max_leads_per_session'] = max_leads
        
        # Add Google Sheets credentials if available
        if 'google_sheets_creds' in st.session_state:
            config._config['google_sheets_creds'] = st.session_state.google_sheets_creds
        
        logger = setup_logging(config)
        
        status_text.markdown("### 🔄 Initializing Advanced Scraper...")
        
        # Initialize scraper with error handling - NO DEMO FALLBACK
        try:
            # Always use headless mode for seamless experience - no visible browser opens
            scraper = SeleniumScraper(
                config=config,
                headless=True,  # Always headless for automated scraping
                guest_mode=True,
                delay=delay
            )
            
            # Check if scraper is properly initialized
            if not hasattr(scraper, 'chrome_available') or not scraper.chrome_available:
                status_text.markdown("### ⚠️ Chrome Not Available - Cannot scrape real data")
                st.error("🌐 **Chrome browser not available in this environment**\n\n"
                       "Real data scraping requires Chrome to be installed and accessible.\n\n"
                       "**Requirements:**\n"
                       "- Run locally with Chrome installed\n"
                       "- Ensure ChromeDriver is accessible\n"
                       "- Or use a compatible deployment environment")
                st.stop()  # Stop execution if Chrome is not available
        except Exception as e:
            status_text.markdown("### ⚠️ Scraper Initialization Failed")
            st.error(f"Failed to initialize scraper: {str(e)}")
            st.error("Cannot proceed with real data scraping. Please ensure Chrome is installed and accessible.")
            st.stop()  # Stop execution if initialization fails

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
        
        # Deduplicate - ensure maximum uniqueness
        deduplicator = Deduplicator(config)
        unique_leads = deduplicator.deduplicate(leads)
        
        # SaaS Usage Tracking
        found_count = len(unique_leads)
        new_total = st.session_state.usage_count + found_count
        update_usage(st.session_state.username, found_count)
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
                formats=[f.lower() for f in formats],
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

def analytics_page():
    st.header("📊 Analytics Dashboard")
    
    if st.session_state.scrape_results:
        df = pd.DataFrame(st.session_state.scrape_results)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Leads", len(df))
        
        with col2:
            social_media_count = df[['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'tiktok']].notna().any(axis=1).sum()
            st.metric("With Social Media", social_media_count)
        
        with col3:
            contact_count = df[['phone', 'email', 'website']].notna().any(axis=1).sum()
            st.metric("With Contact Info", contact_count)
        
        with col4:
            unique_locations = df['address'].dropna().apply(lambda x: ', '.join(x.split(',')[-2:]) if pd.notna(x) else '').nunique()
            st.metric("Locations Covered", unique_locations)
        
        st.subheader("Lead Distribution")
        if 'category' in df.columns:
            category_counts = df['category'].value_counts()
            st.bar_chart(category_counts)
        
        st.subheader("Leads Data")
        st.dataframe(df)
    else:
        st.info("No data available. Generate leads first.")

def settings_page():
    st.header("⚙️ Settings")
    
    # Global settings page
    global_settings_page(st.session_state.username)

if __name__ == "__main__":
    main()