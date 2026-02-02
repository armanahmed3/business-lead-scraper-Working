import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import smtplib
import time
import json
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email_validator import validate_email, EmailNotValidError
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from sklearn.cluster import KMeans
import schedule
import threading
import yagmail
import requests
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False
    def st_autorefresh(*args, **kwargs):
        pass
import concurrent.futures
from tenacity import retry, stop_after_attempt, wait_exponential
import urllib.parse

# Lead Generation imports (with error reporting)
import sys
import os
try:
    # Ensure current directory is on sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    
    from lead_generation_orchestrator import LeadGenerationOrchestrator
    from lead_database_enhanced import LeadDatabase
    LEAD_GENERATION_AVAILABLE = True
except Exception as e:
    LEAD_GENERATION_AVAILABLE = False
    st.error(f"Lead generation unavailable: {e}")
    st.error(f"Current directory: {current_dir}")
    st.error(f"Python path: {sys.path[:3]}...")

# Optional transformers import (commented out in requirements.txt)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except (ImportError, ValueError, OSError) as e:
    TRANSFORMERS_AVAILABLE = False
    # Create dummy classes for fallback
    class pipeline:
        def __init__(self, *args, **kwargs):
            pass
    class AutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return None
    class AutoModelForCausalLM:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return None

# Page configuration
st.set_page_config(
    page_title="Lead Generation & Email Marketing Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .dashboard-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
def init_database():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Leads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            company TEXT,
            title TEXT,
            industry TEXT,
            city TEXT,
            country TEXT,
            website TEXT,
            source TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Campaigns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_at TIMESTAMP,
            sent_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Email tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            lead_id INTEGER,
            email TEXT NOT NULL,
            status TEXT DEFAULT 'sent',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            opened_at TIMESTAMP,
            clicked_at TIMESTAMP,
            bounced_at TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
            FOREIGN KEY (lead_id) REFERENCES leads (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def _ensure_db_schema():
    """Ensure core application tables exist"""
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    # Create core tables if they don't exist
    tables = ['users', 'leads', 'campaigns', 'email_tracking']
    for table in tables:
        if table == 'users':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        elif table == 'leads':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    company TEXT,
                    title TEXT,
                    industry TEXT,
                    city TEXT,
                    country TEXT,
                    website TEXT,
                    source TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
        elif table == 'campaigns':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scheduled_at TIMESTAMP,
                    sent_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
        elif table == 'email_tracking':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    lead_id INTEGER,
                    email TEXT NOT NULL,
                    status TEXT DEFAULT 'sent',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    opened_at TIMESTAMP,
                    clicked_at TIMESTAMP,
                    bounced_at TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
                    FOREIGN KEY (lead_id) REFERENCES leads (id)
                )
            ''')
    
    conn.commit()
    conn.close()

# Authentication functions
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password, role='user'):
    """Register a new user"""
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticate user login"""
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute('''
        SELECT id, username, email, role FROM users
        WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'role': user[3]
        }
    return None

# Email configuration functions
def save_email_config(user_id, config):
    """Save email configuration for user"""
    config_file = f'email_config_{user_id}.json'
    with open(config_file, 'w') as f:
        json.dump(config, f)

def load_email_config(user_id):
    """Load email configuration for user"""
    config_file = f'email_config_{user_id}.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

# Lead management functions
def add_lead(user_id, name, email, phone=None, company=None, title=None, industry=None, city=None, country=None, website=None, source='manual'):
    """Add a new lead"""
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO leads (user_id, name, email, phone, company, title, industry, city, country, website, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, email, phone, company, title, industry, city, country, website, source))
    
    conn.commit()
    conn.close()

def get_leads(user_id, limit=100):
    """Get leads for user"""
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, email, phone, company, title, industry, city, country, website, source, status, created_at
        FROM leads WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    ''', (user_id, limit))
    
    leads = cursor.fetchall()
    conn.close()
    
    return [{
        'id': lead[0],
        'name': lead[1],
        'email': lead[2],
        'phone': lead[3],
        'company': lead[4],
        'title': lead[5],
        'industry': lead[6],
        'city': lead[7],
        'country': lead[8],
        'website': lead[9],
        'source': lead[10],
        'status': lead[11],
        'created_at': lead[12]
    } for lead in leads]

# Campaign management functions
def create_campaign(user_id, name, subject, content):
    """Create a new campaign"""
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO campaigns (user_id, name, subject, content)
        VALUES (?, ?, ?, ?)
    ''', (user_id, name, subject, content))
    
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return campaign_id

def get_campaigns(user_id):
    """Get campaigns for user"""
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, subject, content, status, created_at, scheduled_at, sent_at
        FROM campaigns WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    
    campaigns = cursor.fetchall()
    conn.close()
    
    return [{
        'id': campaign[0],
        'name': campaign[1],
        'subject': campaign[2],
        'content': campaign[3],
        'status': campaign[4],
        'created_at': campaign[5],
        'scheduled_at': campaign[6],
        'sent_at': campaign[7]
    } for campaign in campaigns]

# Analytics functions
def get_analytics(user_id):
    """Get analytics data for user"""
    _ensure_db_schema()
    
    conn = sqlite3.connect('lead_gen.db')
    cursor = conn.cursor()
    
    try:
        # Lead count
        cursor.execute("SELECT COUNT(*) FROM leads WHERE user_id = ?", (user_id,))
        lead_count = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        lead_count = 0
        
    try:
        # Campaign count
        cursor.execute("SELECT COUNT(*) FROM campaigns WHERE user_id = ?", (user_id,))
        campaign_count = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        campaign_count = 0

    # Email tracking aggregates
    total_emails = sent_emails = opened_emails = clicked_emails = 0
    
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM email_tracking et
            JOIN campaigns c ON et.campaign_id = c.id
            WHERE c.user_id = ?
        ''', (user_id,))
        total_emails = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM email_tracking et
            JOIN campaigns c ON et.campaign_id = c.id
            WHERE c.user_id = ? AND et.status = 'sent'
        ''', (user_id,))
        sent_emails = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM email_tracking et
            JOIN campaigns c ON et.campaign_id = c.id
            WHERE c.user_id = ? AND et.opened_at IS NOT NULL
        ''', (user_id,))
        opened_emails = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM email_tracking et
            JOIN campaigns c ON et.campaign_id = c.id
            WHERE c.user_id = ? AND et.clicked_at IS NOT NULL
        ''', (user_id,))
        clicked_emails = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        pass
    
    conn.close()
    
    return {
        'lead_count': lead_count,
        'campaign_count': campaign_count,
        'total_emails': total_emails,
        'sent_emails': sent_emails,
        'opened_emails': opened_emails,
        'clicked_emails': clicked_emails
    }

# Email sending functions
def load_suppression_list(user_id):
    """Load suppression list for user"""
    sup_file = f'suppression_list_{user_id}.txt'
    if os.path.exists(sup_file):
        with open(sup_file, 'r') as f:
            return set(line.strip().lower() for line in f)
    return set()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def send_email_simulation(to_email, subject, content, user_id, from_email=None):
    """Send email with retry logic and rate limiting"""
    # Load suppression list
    sup_list = load_suppression_list(user_id)
    if to_email.strip().lower() in sup_list:
        print(f"Suppressed email skipped: {to_email}")
        return True

    # Load email configuration
    cfg = load_email_config(user_id)
    
    if not cfg or not cfg.get('smtp_username') or not cfg.get('smtp_password'):
        print(f"Simulated email sent to {to_email}: {subject}")
        return True

    smtp_server = cfg.get('smtp_server', 'smtp.gmail.com')
    smtp_port = int(cfg.get('smtp_port', 587))
    smtp_username = cfg.get('smtp_username')
    smtp_password = cfg.get('smtp_password')
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email or smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add content
    msg.attach(MIMEText(content, 'html'))
    
    # Add unsubscribe footer
    unsubscribe_url = f"https://yourapp.com/unsubscribe?email={urllib.parse.quote(to_email)}"
    footer = f"<br><br><hr><p style='font-size: 12px; color: #666;'>If you no longer wish to receive these emails, <a href='{unsubscribe_url}'>click here to unsubscribe</a>.</p>"
    msg.attach(MIMEText(footer, 'html'))
    
    try:
        # Connect to server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(smtp_username, to_email, text)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        raise

# Real-time counters
def render_realtime_counters(user_id):
    """Render real-time counters with WebSocket connection"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Try to connect to WebSocket for real-time updates
    try:
        # This would connect to your FastAPI backend WebSocket
        # For now, we'll use auto-refresh as fallback
        st_autorefresh(interval=3000, key="realtime_refresh")
        
        # Get current analytics
        analytics = get_analytics(user_id)
        
        with col1:
            st.metric("📧 Total Emails", analytics['total_emails'])
        with col2:
            st.metric("📤 Sent", analytics['sent_emails'])
        with col3:
            st.metric("👁️ Opened", analytics['opened_emails'])
        with col4:
            st.metric("🖱️ Clicked", analytics['clicked_emails'])
            
    except Exception as e:
        st.error(f"Real-time updates unavailable: {e}")
        # Fallback to static display
        analytics = get_analytics(user_id)
        with col1:
            st.metric("📧 Total Emails", analytics['total_emails'])
        with col2:
            st.metric("📤 Sent", analytics['sent_emails'])
        with col3:
            st.metric("👁️ Opened", analytics['opened_emails'])
        with col4:
            st.metric("🖱️ Clicked", analytics['clicked_emails'])

# Lead Generation Page
def show_lead_generation():
    """Show lead generation page"""
    st.markdown("## 🎯 Lead Generation")
    
    if not LEAD_GENERATION_AVAILABLE:
        st.error("Lead generation features are not available. Please ensure all dependencies are installed.")
        st.markdown("""
        **Required files:**
        - `lead_generation_orchestrator.py`
        - `lead_database_enhanced.py`
        - `scrapers/` folder with all scraper files
        
        **Required dependencies:**
        - `beautifulsoup4`
        - `lxml`
        - `fake-useragent`
        - `tqdm`
        - `tenacity`
        """)
        return
    
    # Initialize orchestrator
    try:
        if 'lead_orchestrator' not in st.session_state:
            st.session_state.lead_orchestrator = LeadGenerationOrchestrator()
        
        orchestrator = st.session_state.lead_orchestrator
        
        if not orchestrator.db:
            st.warning("Lead database is not available. Some features may not work.")
    except Exception as e:
        st.error(f"Failed to initialize lead generation: {e}")
        return
    
    # Input form
    with st.form("lead_generation_form"):
        st.markdown("### 📝 Lead Generation Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("City", placeholder="e.g., New York")
            country = st.text_input("Country", placeholder="e.g., USA")
            niche = st.text_input("Niche/Industry", placeholder="e.g., Restaurants")
        
        with col2:
            business_name = st.text_input("Business Name (Optional)", placeholder="e.g., Joe's Pizza")
            address = st.text_input("Address (Optional)", placeholder="e.g., 123 Main St")
            num_leads = st.number_input("Number of Leads", min_value=1, max_value=1000, value=10)
        
        # Data sources
        st.markdown("### 🔍 Data Sources")
        available_sources = orchestrator.get_available_sources()
        selected_sources = st.multiselect(
            "Select data sources",
            available_sources,
            default=['Test Scraper'] if 'Test Scraper' in available_sources else available_sources[:1]
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            deduplicate = st.checkbox("Remove duplicates", value=True)
            export_csv = st.checkbox("Export to CSV", value=True)
            free_sources_only = st.checkbox("Free sources only", value=True)
        
        submitted = st.form_submit_button("🚀 Generate Leads", type="primary")
    
    if submitted:
        if not selected_sources:
            st.error("Please select at least one data source.")
            return
        
        if not city or not country or not niche:
            st.error("Please fill in City, Country, and Niche fields.")
            return
        
        # Generate leads
        with st.spinner("Generating leads..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            progress_state = {'v': 0.0}

            def progress_callback(message: str):
                try:
                    status_text.text(message)
                    progress_state['v'] = min(1.0, progress_state['v'] + 0.1)
                    progress_bar.progress(progress_state['v'])
                except Exception:
                    pass
            
            try:
                results = orchestrator.generate_leads(
                    city=city,
                    country=country,
                    niche=niche,
                    business_name=business_name if business_name else None,
                    address=address if address else None,
                    limit=num_leads,
                    sources=selected_sources,
                    deduplicate=deduplicate,
                    user_id=st.session_state.user['id'],
                    progress_callback=progress_callback
                )
                
                progress_bar.progress(1.0)
                status_text.success("Lead generation completed!")
                
                # Display results
                st.markdown("### 📊 Results Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Found", results.get('total_found', 0))
                with col2:
                    st.metric("Duplicates Removed", results.get('duplicates_removed', 0))
                with col3:
                    st.metric("Successfully Inserted", results.get('inserted', 0))
                with col4:
                    st.metric("Sources Used", len(results.get('sources_used', [])))
                
                # Show recent results
                if results.get('inserted', 0) > 0:
                    st.markdown("### 📋 Recent Lead Generation Results")
                    recent_leads = orchestrator.get_lead_stats()
                    if recent_leads:
                        st.dataframe(recent_leads, use_container_width=True)
                
                # Export option
                if export_csv and results.get('inserted', 0) > 0:
                    csv_data = orchestrator.export_leads(user_id=st.session_state.user['id'])
                    if csv_data:
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=f"leads_{city}_{country}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
            except Exception as e:
                st.error(f"Error generating leads: {e}")
                progress_bar.empty()
                status_text.error("Lead generation failed!")
    
    # Lead statistics
    st.markdown("### 📈 Lead Statistics")
    try:
        stats = orchestrator.get_lead_stats()
        if stats:
            st.dataframe(stats, use_container_width=True)
        else:
            st.info("No leads found in database.")
    except Exception as e:
        st.error(f"Error loading lead statistics: {e}")
    
    # Export all leads
    if st.button("📤 Export All Leads to CSV"):
        try:
            csv_data = orchestrator.export_leads(user_id=st.session_state.user['id'])
            if csv_data:
                st.download_button(
                    label="📥 Download All Leads CSV",
                    data=csv_data,
                    file_name=f"all_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No leads to export.")
        except Exception as e:
            st.error(f"Error exporting leads: {e}")

# Main pages
def show_home_page():
    """Show home page with dashboard"""
    st.markdown("## 🏠 Dashboard")
    
    # Quick Stats
    analytics = get_analytics(st.session_state.user['id'])
    st.markdown("### 📊 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Leads", analytics['lead_count'])
    with col2:
        st.metric("Campaigns", analytics['campaign_count'])
    
    st.markdown("---")
    st.markdown("### ⏱️ Real-time Counters")
    render_realtime_counters(st.session_state.user['id'])

def show_login_page():
    """Show login/register page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div class="dashboard-card">
                <h2 style="text-align: center; margin-bottom: 2rem;">🔐 Authentication</h2>
            </div>
        """, unsafe_allow_html=True)
    
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Login", type="primary")
                
                if submit:
                    if username and password:
                        user = authenticate_user(username, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user = user
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Please fill in all fields")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username", placeholder="Choose a username", key="reg_username")
                new_email = st.text_input("Email", placeholder="Enter your email", key="reg_email")
                new_password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="reg_confirm")
                role = st.selectbox("Role", ["User", "Admin"], key="reg_role")
                submit_reg = st.form_submit_button("Register", type="primary")
                
                if submit_reg:
                    if new_username and new_email and new_password and confirm_password:
                        if new_password == confirm_password:
                            if register_user(new_username, new_email, new_password, role.lower()):
                                st.success("Registration successful! Please login.")
                            else:
                                st.error("Username or email already exists")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please fill in all fields")

def show_main_app():
    """Show main application after authentication"""
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        current_page = st.selectbox(
            "Select Page",
            ["Home", "Lead Management", "Email Campaigns", "Analytics", "Settings", "Lead Generation"],
            key="page_selector"
        )
        
        st.markdown("---")
        
        # Quick Stats
        analytics = get_analytics(st.session_state.user['id'])
        st.markdown("### 📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Leads", analytics['lead_count'])
        with col2:
            st.metric("Campaigns", analytics['campaign_count'])
        
        st.markdown("---")
        st.markdown("### ⏱️ Real-time Counters")
        render_realtime_counters(st.session_state.user['id'])
    
    # Logout button
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()
    
    # Main Content
    if current_page == "Home":
        show_home_page()
    elif current_page == "Lead Generation":
        show_lead_generation()
    elif current_page == "Lead Management":
        st.markdown("## 👥 Lead Management")
        st.info("Lead management features coming soon!")
    elif current_page == "Email Campaigns":
        st.markdown("## 📧 Email Campaigns")
        st.info("Email campaign features coming soon!")
    elif current_page == "Analytics":
        st.markdown("## 📊 Analytics")
        st.info("Analytics features coming soon!")
    elif current_page == "Settings":
        st.markdown("## ⚙️ Settings")
        st.info("Settings features coming soon!")

# Main application
def main():
    """Main application function"""
    # Initialize database
    init_database()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Show appropriate page
    if st.session_state.authenticated:
        show_main_app()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
