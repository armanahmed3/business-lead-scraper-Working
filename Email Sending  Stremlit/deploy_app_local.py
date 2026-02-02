"""
LeadAI Pro - Local Development Version
Streamlit application optimized for local testing without heavy AI dependencies
"""

import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import asyncio
import threading
import time
import json
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
import re
import os
import warnings
from typing import Dict, List, Optional, Tuple
import urllib.parse
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import schedule
import yagmail
from email_validator import validate_email, EmailNotValidError

# Simple background queue worker with per-user rate limiting
_QUEUE_THREAD = None
_QUEUE_RUNNING = False
_USER_LAST_SEND = {}

def _rate_limit_ok(user_id: int, per_minute: int = 30) -> bool:
    """Allow up to per_minute emails per minute per user."""
    now = time.time()
    window = 60.0
    bucket = _USER_LAST_SEND.setdefault(user_id, [])
    # drop old timestamps
    _USER_LAST_SEND[user_id] = [t for t in bucket if now - t < window]
    # Allow user override from session settings
    override = st.session_state.get("rate_limit_per_minute")
    effective_limit = int(override) if override else per_minute
    if len(_USER_LAST_SEND[user_id]) < effective_limit:
        _USER_LAST_SEND[user_id].append(now)
        return True
    return False

def _process_queue_loop():
    global _QUEUE_RUNNING
    _QUEUE_RUNNING = True
    while _QUEUE_RUNNING:
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, user_id, campaign_id, lead_id, to_email, subject, body, scheduled_at, attempts
                FROM send_queue
                WHERE status = 'queued' AND datetime(scheduled_at) <= datetime('now')
                ORDER BY scheduled_at ASC
                LIMIT 20
                """
            )
            rows = cur.fetchall()
            for row in rows:
                qid, user_id, campaign_id, lead_id, to_email, subject, body, scheduled_at, attempts = row
                # rate limit
                if not _rate_limit_ok(user_id):
                    continue
                try:
                    ok = send_email_simulation(to_email, subject, body)
                    if ok:
                        # mark sent in queue and tracking
                        cur.execute("UPDATE send_queue SET status = 'sent' WHERE id = ?", (qid,))
                        if campaign_id and lead_id:
                            cur.execute('''
                                INSERT INTO email_tracking (campaign_id, lead_id, email, status, sent_at)
                                VALUES (?, ?, ?, 'Sent', CURRENT_TIMESTAMP)
                            ''', (campaign_id, lead_id, to_email))
                        cur.execute("INSERT INTO audit_logs (user_id, action, details) VALUES (?, 'send_email', ?)", (user_id, f'qid={qid}, to={to_email}'))
                    else:
                        raise RuntimeError('send returned False')
                except Exception as e:
                    cur.execute("UPDATE send_queue SET attempts = ?, last_error = ?, status = 'queued' WHERE id = ?", (attempts + 1, str(e), qid))
            conn.commit()
            conn.close()
        except Exception:
            pass
        time.sleep(2)

def ensure_queue_worker_started():
    global _QUEUE_THREAD
    if _QUEUE_THREAD is None or not _QUEUE_THREAD.is_alive():
        _QUEUE_THREAD = threading.Thread(target=_process_queue_loop, daemon=True)
        _QUEUE_THREAD.start()

def ensure_queue_worker_stopped():
    """Signal the background queue loop to stop."""
    global _QUEUE_RUNNING
    _QUEUE_RUNNING = False

# Suppress warnings
warnings.filterwarnings("ignore")

# Configure Streamlit page
st.set_page_config(
    page_title="LeadAI Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables from a local env file if present
def _load_env_from_file() -> None:
    """Load SMTP and other vars from .env or env_example.txt if set locally."""
    candidate_files = [".env", "env", "env_example.txt"]
    for fname in candidate_files:
        if os.path.exists(fname):
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip('"').strip("'")
                            if key and val and key not in os.environ:
                                os.environ[key] = val
            except Exception:
                pass

_load_env_from_file()

# Compatibility mapping for environment keys from older samples
if os.getenv("SMTP_HOST") is None and os.getenv("SMTP_SERVER"):
    os.environ["SMTP_HOST"] = os.getenv("SMTP_SERVER") or ""
if os.getenv("SMTP_USER") is None and os.getenv("SMTP_USERNAME"):
    os.environ["SMTP_USER"] = os.getenv("SMTP_USERNAME") or ""
if os.getenv("SMTP_PASS") is None and os.getenv("SMTP_PASSWORD"):
    os.environ["SMTP_PASS"] = os.getenv("SMTP_PASSWORD") or ""
if os.getenv("SMTP_FROM") is None and os.getenv("FROM_EMAIL"):
    os.environ["SMTP_FROM"] = os.getenv("FROM_EMAIL") or ""

# Database setup
DB_NAME = "leadai_pro.db"

def init_database():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect(DB_NAME)
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
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT,
            phone TEXT,
            title TEXT,
            industry TEXT,
            category TEXT DEFAULT 'General',
            status TEXT DEFAULT 'New',
            score INTEGER DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Campaigns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'Draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_at TIMESTAMP,
            sent_at TIMESTAMP,
            user_id INTEGER,
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
            status TEXT DEFAULT 'Pending',
            sent_at TIMESTAMP,
            opened_at TIMESTAMP,
            clicked_at TIMESTAMP,
            click_count INTEGER DEFAULT 0,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
            FOREIGN KEY (lead_id) REFERENCES leads (id)
        )
    ''')

    # Per-user SMTP/email credentials
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT,
            host TEXT,
            port INTEGER,
            username TEXT,
            password TEXT,
            from_email TEXT,
            use_tls INTEGER DEFAULT 1,
            use_ssl INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Email templates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, name),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Send queue (background worker will process this)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS send_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            campaign_id INTEGER,
            lead_id INTEGER,
            to_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            scheduled_at TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'queued',
            attempts INTEGER DEFAULT 0,
            last_error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
            FOREIGN KEY (lead_id) REFERENCES leads (id)
        )
    ''')

    # Audit log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Suppression list (do not email)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppression_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, email),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

# Custom CSS for 3D cinematic UI
def load_css():
    """Load custom CSS for 3D cinematic UI"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --accent-color: #06b6d4;
        --background-dark: #0f0f23;
        --surface-dark: #1a1a2e;
        --text-primary: #ffffff;
        --text-secondary: #a1a1aa;
        --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --gradient-accent: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    .stApp {
        background: var(--background-dark);
        color: var(--text-primary);
    }
    
    .cinematic-header {
        background: var(--gradient-primary);
        padding: 2rem;
        border-radius: 0 0 2rem 2rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .cinematic-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.3;
    }
    
    .header-content {
        position: relative;
        z-index: 1;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(45deg, #ffffff, #e0e7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: var(--text-secondary);
        text-align: center;
        margin-top: 1rem;
        opacity: 0.9;
    }
    
    .dashboard-card {
        background: var(--surface-dark);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .dashboard-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--gradient-accent);
    }
    
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
        border-color: var(--primary-color);
    }
    
    .metric-card {
        background: var(--gradient-primary);
        border-radius: 0.75rem;
        padding: 1.5rem;
        text-align: center;
        color: white;
        margin: 0.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        transform: scale(0);
        transition: transform 0.5s ease;
    }
    
    .metric-card:hover::before {
        transform: scale(1);
    }
    
    .metric-card:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    .btn-primary {
        background: var(--gradient-primary);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
    }
    
    .sidebar .sidebar-content {
        background: var(--surface-dark);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .sidebar .sidebar-content .stSelectbox > div > div {
        background: var(--surface-dark);
        color: var(--text-primary);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface-dark);
        border-radius: 0.5rem;
        padding: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 0.25rem;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-primary);
        color: white;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.1);
        color: var(--text-primary);
    }
    
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: var(--primary-color);
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .glow {
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--surface-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
    </style>
    """, unsafe_allow_html=True)

# Authentication functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user data"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, email, password_hash, role FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(password, user[3]):
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'role': user[4]
        }
    return None

def register_user(username: str, email: str, password: str, role: str = 'user') -> bool:
    """Register a new user"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, role)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# AI Assistant functions (simplified for local testing)
def generate_email_content(prompt: str, max_length: int = 200) -> str:
    """Generate email content using simple templates (local version)"""
    templates = [
        f"Subject: {prompt}\n\nDear {{name}},\n\nI hope this email finds you well. I wanted to reach out regarding {prompt.lower()}. I believe this could be of great value to {{company}}.\n\nBest regards,\nYour Name",
        f"Subject: Follow-up on {prompt}\n\nHi {{name}},\n\nI hope you're doing well. I wanted to follow up on our previous conversation about {prompt.lower()}. I'd love to discuss how this could benefit {{company}}.\n\nLooking forward to hearing from you.\n\nBest,\nYour Name",
        f"Subject: {prompt} - Quick Question\n\nHello {{name}},\n\nI hope this message finds you in good health. I have a quick question about {prompt.lower()} and how it might relate to {{company}}'s current needs.\n\nWould you be available for a brief call this week?\n\nThanks,\nYour Name"
    ]
    
    import random
    return random.choice(templates)

def generate_subject_line(topic: str) -> str:
    """Generate subject line using simple templates (local version)"""
    subjects = [
        f"Quick question about {topic}",
        f"Following up on {topic}",
        f"{topic} - Let's discuss",
        f"Re: {topic}",
        f"Important: {topic}",
        f"Update on {topic}",
        f"{topic} - Next steps",
        f"Regarding {topic}"
    ]
    
    import random
    return random.choice(subjects)

# Database functions
def get_user_leads(user_id: int) -> pd.DataFrame:
    """Get leads for a specific user"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM leads WHERE user_id = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def add_lead(user_id: int, lead_data: Dict) -> bool:
    """Add a new lead"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO leads (name, email, company, phone, title, industry, category, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead_data['name'],
            lead_data['email'],
            lead_data.get('company', ''),
            lead_data.get('phone', ''),
            lead_data.get('title', ''),
            lead_data.get('industry', ''),
            lead_data.get('category', 'General'),
            user_id
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error adding lead: {str(e)}")
        return False

def get_campaigns(user_id: int) -> pd.DataFrame:
    """Get campaigns for a specific user"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM campaigns WHERE user_id = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def create_campaign(user_id: int, campaign_data: Dict) -> bool:
    """Create a new campaign"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO campaigns (name, subject, content, user_id)
            VALUES (?, ?, ?, ?)
        ''', (
            campaign_data['name'],
            campaign_data['subject'],
            campaign_data['content'],
            user_id
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error creating campaign: {str(e)}")
        return False

def get_analytics(user_id: int) -> Dict:
    """Get analytics data for user"""
    conn = sqlite3.connect(DB_NAME)
    
    # Get lead count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads WHERE user_id = ?", (user_id,))
    lead_count = cursor.fetchone()[0]
    
    # Get campaign count
    cursor.execute("SELECT COUNT(*) FROM campaigns WHERE user_id = ?", (user_id,))
    campaign_count = cursor.fetchone()[0]
    
    # Get email tracking data
    cursor.execute('''
        SELECT 
            COUNT(*) as total_emails,
            SUM(CASE WHEN et.status = 'Sent' THEN 1 ELSE 0 END) as sent_emails,
            SUM(CASE WHEN et.opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened_emails,
            SUM(CASE WHEN et.clicked_at IS NOT NULL THEN 1 ELSE 0 END) as clicked_emails
        FROM email_tracking et
        JOIN campaigns c ON et.campaign_id = c.id
        WHERE c.user_id = ?
    ''', (user_id,))
    
    tracking_data = cursor.fetchone()
    conn.close()
    
    return {
        'lead_count': lead_count,
        'campaign_count': campaign_count,
        'total_emails': tracking_data[0] or 0,
        'sent_emails': tracking_data[1] or 0,
        'opened_emails': tracking_data[2] or 0,
        'clicked_emails': tracking_data[3] or 0
    }

# Email functions
def send_email_simulation(to_email: str, subject: str, content: str) -> bool:
    """Send real email using per-user SMTP if present, else env, else simulate."""
    smtp_host = None
    smtp_port = None
    smtp_user = None
    smtp_pass = None
    smtp_from = None
    use_tls = True
    use_ssl = False

    # Try per-user settings from DB
    try:
        user_id = st.session_state.user['id'] if 'user' in st.session_state and st.session_state.user else None
        if user_id:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT host, port, username, password, from_email, use_tls, use_ssl FROM email_credentials WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, use_tls, use_ssl = row
    except Exception:
        pass

    # Fallback to env if DB not set
    if not smtp_host:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        smtp_from = os.getenv("SMTP_FROM", smtp_user or "")
        use_tls = True
        use_ssl = False

    if smtp_host and smtp_user and smtp_pass and smtp_from:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_from
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(content, "plain"))

            context = ssl.create_default_context()
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
            if use_tls and not use_ssl:
                server.starttls(context=context)
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            st.warning(f"SMTP send failed, falling back to simulation: {e}")

    # Fallback simulate
    print(f"Simulated email sent to {to_email}: {subject}")
    return True

def schedule_email_campaign(campaign_id: int, lead_ids: List[int], delay_minutes: int = 5):
    """Enqueue campaign emails into send_queue with scheduled time."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, subject, content, user_id FROM campaigns WHERE id = ?", (campaign_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        st.error("Campaign not found")
        return
    name, subject, content, user_id = row

    # fetch leads
    if not lead_ids:
        conn.close()
        st.warning("No leads to schedule")
        return
    placeholders = ','.join(['?' for _ in lead_ids])
    cursor.execute(f"SELECT id, name, email, company FROM leads WHERE id IN ({placeholders})", lead_ids)
    leads = cursor.fetchall()

    scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)
    # Respect suppression list
    sup_emails = set()
    cursor.execute("SELECT email FROM suppression_list WHERE user_id = ?", (user_id,))
    sup_emails.update(email for (email,) in cursor.fetchall())

    enqueued = 0
    for lead_id, lead_name, lead_email, lead_company in leads:
        if not lead_email or lead_email in sup_emails:
            continue
        personalized = content.replace('{name}', lead_name).replace('{company}', lead_company or '')
        cursor.execute(
            '''INSERT INTO send_queue (user_id, campaign_id, lead_id, to_email, subject, body, scheduled_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, campaign_id, lead_id, lead_email, subject, personalized, scheduled_at)
        )
        enqueued += 1

    # Update campaign status to Scheduled
    cursor.execute("UPDATE campaigns SET status = 'Scheduled', scheduled_at = ? WHERE id = ?", (scheduled_at, campaign_id))
    cursor.execute("INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)", (user_id, 'enqueue_campaign', f'campaign_id={campaign_id}, emails={enqueued}'))
    conn.commit()
    conn.close()
    st.success(f"Enqueued {enqueued} emails. They will start sending in {delay_minutes} minutes.")

# Main application
def main():
    """Main application entry point"""
    load_css()
    ensure_queue_worker_started()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'
    
    # Header
    st.markdown("""
    <div class="cinematic-header">
        <div class="header-content">
            <h1 class="main-title">🚀 LeadAI Pro</h1>
            <p class="subtitle">AI-Powered Lead Management & Email Marketing Platform</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()

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
                submit_reg = st.form_submit_button("Register", type="primary")
                
                if submit_reg:
                    if new_username and new_email and new_password and confirm_password:
                        if new_password == confirm_password:
                            # auto-assign role: first user becomes admin, others user
                            try:
                                conn = sqlite3.connect(DB_NAME)
                                cur = conn.cursor()
                                cur.execute("SELECT COUNT(*) FROM users")
                                user_count = cur.fetchone()[0]
                                conn.close()
                            except Exception:
                                user_count = 1
                            role_to_assign = 'admin' if user_count == 0 else 'user'
                            if register_user(new_username, new_email, new_password, role_to_assign):
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
        st.markdown(f"### 👋 Welcome, {st.session_state.user['username']}")
        st.markdown(f"**Role:** {st.session_state.user['role'].title()}")
        
        st.markdown("---")
        st.markdown("### 🎯 Navigation")
        
        pages = [
            "Home",
            "Dashboard",
            "Lead Management",
            "Email Campaigns",
            "Email Tracking",
            "Analytics",
            "AI Assistant",
            "Templates",
            "Audit Logs",
            "Settings",
            "About",
            "Contact",
        ]
        # Admin page visible only for admins
        try:
            if st.session_state.user and st.session_state.user.get('role') == 'admin':
                pages.insert(1, "Admin")
        except Exception:
            pass
        current_page = st.selectbox("Choose a page", pages, key="nav_select")
        
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
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
    
    # Main Content
    if current_page == "Home":
        show_home_page()
    elif current_page == "Dashboard":
        show_dashboard()
    elif current_page == "Admin":
        show_admin_panel()
    elif current_page == "Lead Management":
        show_lead_management()
    elif current_page == "Email Campaigns":
        show_email_campaigns()
    elif current_page == "Email Tracking":
        show_email_tracking()
    elif current_page == "Analytics":
        show_analytics()
    elif current_page == "AI Assistant":
        show_ai_assistant()
    elif current_page == "Templates":
        show_templates_page()
    elif current_page == "Audit Logs":
        show_audit_logs()
    elif current_page == "About":
        show_about()
    elif current_page == "Contact":
        show_contact()

def show_home_page():
    """Show home dashboard"""
    st.markdown("## 📊 Dashboard Overview")
    
    # Get analytics
    analytics = get_analytics(st.session_state.user['id'])
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{analytics['lead_count']}</div>
            <div class="metric-label">Total Leads</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        open_rate = (analytics['opened_emails'] / analytics['sent_emails'] * 100) if analytics['sent_emails'] > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{open_rate:.1f}%</div>
            <div class="metric-label">Open Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        click_rate = (analytics['clicked_emails'] / analytics['sent_emails'] * 100) if analytics['sent_emails'] > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{click_rate:.1f}%</div>
            <div class="metric-label">Click Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{analytics['campaign_count']}</div>
            <div class="metric-label">Campaigns</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent Activity
    st.markdown("## 📈 Recent Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="dashboard-card">
            <h3>📊 Lead Distribution</h3>
            <p>Visual representation of your lead categories</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Lead distribution chart
        leads_df = get_user_leads(st.session_state.user['id'])
        if not leads_df.empty:
            category_counts = leads_df['category'].value_counts()
            fig = px.pie(values=category_counts.values, names=category_counts.index, title="Lead Categories")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-card">
            <h3>📧 Email Performance</h3>
            <p>Track your email campaign effectiveness</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Email performance metrics
        if analytics['sent_emails'] > 0:
            performance_data = {
                'Metric': ['Sent', 'Opened', 'Clicked'],
                'Count': [analytics['sent_emails'], analytics['opened_emails'], analytics['clicked_emails']]
            }
            fig = px.bar(performance_data, x='Metric', y='Count', title="Email Performance")
            st.plotly_chart(fig, use_container_width=True)

def show_dashboard():
    """Unified dashboard with CSV upload and bulk scheduling"""
    st.markdown("## 📊 Dashboard")
    
    # Upload + preview
    uploaded_file = st.file_uploader(
        "Upload Clients CSV (name, email, company, ...)",
        type="csv",
        help="Required columns: name, email. Optional: company, phone, title, industry, category"
    )
    df = None
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✅ File uploaded")
            st.markdown("### Preview")
            st.dataframe(df.head(10))
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    
    # Queue metrics and controls
    qm = _queue_metrics()
    colq1, colq2, colq3 = st.columns(3)
    with colq1:
        st.metric("Queued Emails", qm.get("queued", 0))
    with colq2:
        st.metric("Sent (last hour)", qm.get("sent_last_hour", 0))
    with colq3:
        if st.button("🧹 Clear My Queued Emails"):
            n = _clear_user_queue(st.session_state.user['id'])
            st.success(f"Cleared {n} queued emails for your account.")
            st.rerun()

    # Email template
    st.markdown("### ✉️ Email Template")
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Subject", placeholder="e.g., Quick question for {company}")
    with col2:
        delay_min = st.number_input("Delay (minutes)", min_value=1, max_value=60, value=5)
    body = st.text_area("Body", placeholder="Hello {name},\n\nWe’d love to help {company} ...", height=180)
    
    # Schedule bulk send
    if st.button("⏱️ Schedule Bulk Email Send", type="primary"):
        if df is None:
            st.error("Please upload a CSV first")
        elif any(c not in df.columns for c in ["name", "email"]):
            st.error("CSV must include 'name' and 'email' columns")
        elif not subject or not body:
            st.error("Please provide subject and body")
        else:
            # Insert leads and create a one-off campaign, then schedule
            user_id = st.session_state.user['id']
            for _, row in df.iterrows():
                try:
                    validate_email(row['email'])
                    add_lead(user_id, {
                        'name': row['name'],
                        'email': row['email'],
                        'company': row.get('company', ''),
                        'phone': row.get('phone', ''),
                        'title': row.get('title', ''),
                        'industry': row.get('industry', ''),
                        'category': row.get('category', 'General')
                    })
                except Exception:
                    continue
            
            # Create campaign
            create_campaign(user_id, {'name': f"Bulk-{datetime.now().strftime('%H%M%S')}", 'subject': subject, 'content': body})
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT id FROM campaigns WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
            camp_id = cur.fetchone()[0]
            # Select lead ids from uploaded emails
            emails = df['email'].tolist()
            q_marks = ','.join(['?' for _ in emails])
            cur.execute(f"SELECT id FROM leads WHERE user_id = ? AND email IN ({q_marks})", [user_id, *emails])
            lead_ids = [r[0] for r in cur.fetchall()]
            conn.close()
            
            schedule_email_campaign(camp_id, lead_ids, delay_min)
            st.success(f"Scheduled {len(lead_ids)} emails. They will be sent in {delay_min} minutes.")

def show_about():
    st.markdown("## ℹ️ About")
    st.write("LeadAI Pro local version with simplified navigation, template library, queued sending, per-user SMTP, and tracking.")

def show_contact():
    st.markdown("## ✉️ Contact")
    st.write("For support, open an issue or email support@example.com.")

def show_admin_panel():
    """Admin-only: manage users and roles."""
    if not (st.session_state.user and st.session_state.user.get('role') == 'admin'):
        st.error("Admin access required.")
        return
    st.markdown("## 🛡️ Admin Panel")
    st.markdown("Manage users and roles.")

    # List users
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC")
        users = cur.fetchall()
        conn.close()
        if users:
            st.dataframe(pd.DataFrame(users, columns=["id","username","email","role","created_at"]))
        else:
            st.info("No users found.")
    except Exception as e:
        st.error(f"Failed to load users: {e}")

    st.markdown("### 🔁 Change User Role")
    try:
        usernames = [u[1] for u in users] if users else []
        col1, col2 = st.columns(2)
        with col1:
            sel_user = st.selectbox("Select user", usernames) if usernames else None
        with col2:
            new_role = st.selectbox("New role", ["admin", "user"]) if usernames else None
        if st.button("Update Role") and sel_user and new_role:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, sel_user))
                conn.commit()
                conn.close()
                st.success("Role updated. Refresh to see changes.")
            except Exception as e:
                st.error(f"Failed to update role: {e}")
    except Exception:
        pass

def show_lead_management():
    """Show lead management interface"""
    st.markdown("## 👥 Lead Management")
    
    # Upload Section
    st.markdown("""
    <div class="dashboard-card">
        <h3>📁 Upload Lead Data</h3>
        <p>Upload CSV files with lead information for AI processing</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload a CSV file with lead data including names, emails, companies, and phone numbers"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            required_columns = ['name', 'email']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
            else:
                st.success("✅ File uploaded successfully!")
                
                # Show preview
                st.markdown("### 📋 Data Preview")
                st.dataframe(df.head(10))
                
                # Process leads
                if st.button("🚀 Process Leads", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    processed_count = 0
                    for index, row in df.iterrows():
                        try:
                            # Validate email
                            validate_email(row['email'])
                            
                            lead_data = {
                                'name': row['name'],
                                'email': row['email'],
                                'company': row.get('company', ''),
                                'phone': row.get('phone', ''),
                                'title': row.get('title', ''),
                                'industry': row.get('industry', ''),
                                'category': row.get('category', 'General')
                            }
                            
                            # De-duplicate by email (keep latest)
                            try:
                                conn = sqlite3.connect(DB_NAME)
                                cur = conn.cursor()
                                cur.execute("DELETE FROM leads WHERE user_id = ? AND email = ?", (st.session_state.user['id'], lead_data['email']))
                                conn.commit()
                                conn.close()
                            except Exception:
                                pass

                            if add_lead(st.session_state.user['id'], lead_data):
                                processed_count += 1
                            
                            progress_bar.progress((index + 1) / len(df))
                            status_text.text(f"Processing lead {index + 1} of {len(df)}")
                            
                        except EmailNotValidError:
                            st.warning(f"Invalid email for {row['name']}: {row['email']}")
                        except Exception as e:
                            st.warning(f"Error processing {row['name']}: {str(e)}")
                    
                    st.success(f"✅ Successfully processed {processed_count} leads!")
                    progress_bar.empty()
                    status_text.empty()
        
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
    
    # Display existing leads
    st.markdown("## 📋 Your Leads")
    
    leads_df = get_user_leads(st.session_state.user['id'])
    
    if not leads_df.empty:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            categories = ['All'] + list(leads_df['category'].unique())
            selected_category = st.selectbox("Filter by Category", categories)
        with col2:
            statuses = ['All'] + list(leads_df['status'].unique())
            selected_status = st.selectbox("Filter by Status", statuses)
        
        # Apply filters
        filtered_df = leads_df.copy()
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        if selected_status != 'All':
            filtered_df = filtered_df[filtered_df['status'] == selected_status]
        
        # Inline lead scoring and status/category updates
        st.markdown("### ⚖️ Lead Scoring & Updates")
        colsc1, colsc2, colsc3 = st.columns(3)
        with colsc1:
            w_title = st.slider("Weight: Title present", 0, 50, 10)
        with colsc2:
            w_company = st.slider("Weight: Company present", 0, 50, 15)
        with colsc3:
            w_industry = st.slider("Weight: Industry present", 0, 50, 10)

        if st.button("🔢 Recompute Scores"):
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                for _, row in filtered_df.iterrows():
                    base = 50
                    base += w_title if str(row.get('title', '')).strip() else 0
                    base += w_company if str(row.get('company', '')).strip() else 0
                    base += w_industry if str(row.get('industry', '')).strip() else 0
                    score = max(0, min(100, int(base)))
                    cur.execute("UPDATE leads SET score = ? WHERE id = ?", (score, int(row['id'])))
                conn.commit()
                conn.close()
                st.success("Scores updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update scores: {e}")

        st.markdown("### ✏️ Bulk Update Status/Category")
        # Choose subset by names
        select_names = st.multiselect("Select leads to update", filtered_df['name'].tolist())
        new_status = st.selectbox("New Status", ["New", "Contacted", "Qualified", "Won", "Lost"], index=0)
        new_category = st.text_input("New Category (optional)", value="")
        if st.button("💾 Apply Updates") and select_names:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                ids = filtered_df[filtered_df['name'].isin(select_names)]['id'].tolist()
                if new_category.strip():
                    for lid in ids:
                        cur.execute("UPDATE leads SET status = ?, category = ? WHERE id = ?", (new_status, new_category.strip(), int(lid)))
                else:
                    for lid in ids:
                        cur.execute("UPDATE leads SET status = ? WHERE id = ?", (new_status, int(lid)))
                conn.commit()
                conn.close()
                st.success("Leads updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update leads: {e}")

        # Display table
        st.dataframe(filtered_df[['id','name', 'email', 'company', 'category', 'status', 'score']])
        
        # Export button
        if st.button("📥 Export Leads as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No leads found. Upload a CSV file to get started!")

def show_email_campaigns():
    """Show email campaign management"""
    st.markdown("## 📧 Email Campaigns")
    
    # Create new campaign
    st.markdown("""
    <div class="dashboard-card">
        <h3>✍️ Create New Campaign</h3>
        <p>Design and schedule your email campaigns</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("campaign_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            campaign_name = st.text_input("Campaign Name", placeholder="Enter campaign name")
            subject_line = st.text_input("Subject Line", placeholder="Enter email subject")
        
        with col2:
            template_type = st.selectbox("Template Type", ["Newsletter", "Promotional", "Follow-up", "Welcome"])
            send_delay = st.number_input("Send Delay (minutes)", min_value=1, max_value=60, value=5)
        
        # Email content
        email_content = st.text_area(
            "Email Content",
            placeholder="Write your email content here. Use {name} and {company} for personalization.",
            height=200
        )
        
        # AI assistance
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("🤖 Generate Subject Line", type="secondary"):
                if email_content:
                    generated_subject = generate_subject_line(email_content[:100])
                    st.session_state.generated_subject = generated_subject
                else:
                    st.warning("Please enter email content first")
        
        with col2:
            if st.form_submit_button("🤖 Improve Content", type="secondary"):
                if email_content:
                    improved_content = generate_email_content(f"Improve this email: {email_content}")
                    st.session_state.improved_content = improved_content
                else:
                    st.warning("Please enter email content first")
        
        # Use generated content
        if 'generated_subject' in st.session_state:
            subject_line = st.text_input("Subject Line", value=st.session_state.generated_subject, key="subject_input")
        
        if 'improved_content' in st.session_state:
            email_content = st.text_area("Email Content", value=st.session_state.improved_content, height=200, key="content_input")
        
        # Target leads
        leads_df = get_user_leads(st.session_state.user['id'])
        if not leads_df.empty:
            lead_options = leads_df['name'].tolist()
            selected_leads = st.multiselect("Select Target Leads", lead_options)
        else:
            selected_leads = []
            st.warning("No leads available. Please add leads first.")
        
        # Submit campaign
        create_btn = st.form_submit_button("🚀 Create Campaign", type="primary")
        test_btn = st.form_submit_button("🧪 Test Send to My Email")
        if test_btn:
            if subject_line and email_content:
                to_me = st.session_state.user['email'] if st.session_state.user else None
                if to_me:
                    ok = send_email_simulation(to_me, subject_line, email_content.replace('{name}', st.session_state.user['username']))
                    if ok:
                        st.success(f"Test email sent to {to_me} (or simulated)")
                else:
                    st.warning("No user email found.")
        if create_btn:
            if campaign_name and subject_line and email_content and selected_leads:
                campaign_data = {
                    'name': campaign_name,
                    'subject': subject_line,
                    'content': email_content
                }
                
                if create_campaign(st.session_state.user['id'], campaign_data):
                    st.success("Campaign created successfully!")
                    
                    # Schedule emails
                    selected_lead_ids = leads_df[leads_df['name'].isin(selected_leads)]['id'].tolist()
                    
                    # Get the latest campaign ID
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM campaigns WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (st.session_state.user['id'],))
                    campaign_id = cursor.fetchone()[0]
                    conn.close()
                    
                    # Schedule campaign
                    schedule_email_campaign(campaign_id, selected_lead_ids, send_delay)
                    st.info(f"Campaign scheduled to send in {send_delay} minutes!")
            else:
                st.error("Please fill in all fields and select target leads")
    
    # Display existing campaigns
    st.markdown("## 📋 Your Campaigns")
    
    campaigns_df = get_campaigns(st.session_state.user['id'])
    
    if not campaigns_df.empty:
        st.dataframe(campaigns_df[['id','name', 'subject', 'status', 'created_at']])

        # Actions: clone/delete/cancel schedule
        st.markdown("### 🛠️ Campaign Actions")
        target_ids = st.multiselect("Select campaign IDs", campaigns_df['id'].tolist())
        colca1, colca2, colca3 = st.columns(3)
        with colca1:
            if st.button("🧬 Clone Selected") and target_ids:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    for cid in target_ids:
                        cur.execute("SELECT name, subject, content, user_id FROM campaigns WHERE id = ?", (int(cid),))
                        row = cur.fetchone()
                        if row:
                            name, subj, content, uid = row
                            cur.execute("INSERT INTO campaigns (name, subject, content, status, user_id) VALUES (?, ?, ?, 'Draft', ?)", (f"{name} (Copy)", subj, content, uid))
                    conn.commit()
                    conn.close()
                    st.success("Cloned.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Clone failed: {e}")
        with colca2:
            if st.button("🗑️ Delete Selected") and target_ids:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    q = ','.join(['?']*len(target_ids))
                    cur.execute(f"DELETE FROM campaigns WHERE id IN ({q})", list(map(int, target_ids)))
                    conn.commit()
                    conn.close()
                    st.success("Deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete failed: {e}")
        with colca3:
            if st.button("⏹️ Cancel Schedule") and target_ids:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    for cid in target_ids:
                        cur.execute("UPDATE campaigns SET status = 'Draft', scheduled_at = NULL WHERE id = ?", (int(cid),))
                    conn.commit()
                    conn.close()
                    st.success("Schedules canceled.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Cancel failed: {e}")
        st.markdown("### 🔁 Retry Queued Sends (Selected Campaigns)")
        if st.button("♻️ Retry Failed/Queued Now") and target_ids:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                # Bring scheduled_at to now for selected campaign queued items
                q = ','.join(['?']*len(target_ids))
                cur.execute(f"UPDATE send_queue SET scheduled_at = datetime('now'), status = 'queued' WHERE campaign_id IN ({q})", list(map(int, target_ids)))
                conn.commit()
                conn.close()
                st.success("Queued items rescheduled to now.")
            except Exception as e:
                st.error(f"Retry failed: {e}")

        # Export campaigns
        if st.button("📥 Export Campaigns as CSV"):
            csv = campaigns_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"campaigns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No campaigns found. Create your first campaign above!")

def show_email_tracking():
    """Show per-user email tracking with filters and charts"""
    st.markdown("## 📬 Email Tracking")
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        # Join tracking with leads and campaigns for context
        cur.execute(
            """
            SELECT et.id, c.name as campaign_name, l.name as lead_name, et.email, et.status,
                   et.sent_at, et.opened_at, et.clicked_at, et.click_count
            FROM email_tracking et
            JOIN campaigns c ON et.campaign_id = c.id
            LEFT JOIN leads l ON et.lead_id = l.id
            WHERE c.user_id = ?
            ORDER BY et.sent_at DESC NULLS LAST, et.id DESC
            """,
            (st.session_state.user['id'],),
        )
        rows = cur.fetchall()
        conn.close()
        df = pd.DataFrame(
            rows,
            columns=[
                "id",
                "campaign",
                "lead",
                "email",
                "status",
                "sent_at",
                "opened_at",
                "clicked_at",
                "click_count",
            ],
        )
        if df.empty:
            st.info("No email events yet. Schedule a campaign to see tracking here.")
            return

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            sel_campaign = st.selectbox("Campaign", ["All"] + sorted(df["campaign"].dropna().unique().tolist()))
        with col2:
            sel_status = st.selectbox("Status", ["All", "Pending", "Sent", "Opened", "Clicked"]) 
        with col3:
            only_clicked = st.checkbox("Only with clicks > 0", value=False)

        fdf = df.copy()
        if sel_campaign != "All":
            fdf = fdf[fdf["campaign"] == sel_campaign]
        if sel_status != "All":
            if sel_status == "Opened":
                fdf = fdf[fdf["opened_at"].notna()]
            elif sel_status == "Clicked":
                fdf = fdf[fdf["clicked_at"].notna()]
            else:
                fdf = fdf[fdf["status"] == sel_status]
        if only_clicked:
            fdf = fdf[(fdf["click_count"].fillna(0) > 0)]

        st.dataframe(fdf[["id","campaign", "lead", "email", "status", "sent_at", "opened_at", "clicked_at", "click_count"]])

        # Simple KPI
        total = len(df)
        sent = (df["status"] == "Sent").sum()
        opened = df["opened_at"].notna().sum()
        clicked = df["clicked_at"].notna().sum()
        colA, colB, colC, colD = st.columns(4)
        with colA:
            st.metric("Events", total)
        with colB:
            st.metric("Sent", int(sent))
        with colC:
            st.metric("Opened", int(opened))
        with colD:
            st.metric("Clicked", int(clicked))

        st.markdown("### 🧪 Simulate Events")
        sel_ids = st.multiselect("Select tracking IDs", fdf['id'].tolist())
        cola, colb = st.columns(2)
        with cola:
            if st.button("👁️ Mark Opened") and sel_ids:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    for tid in sel_ids:
                        cur.execute("UPDATE email_tracking SET opened_at = CURRENT_TIMESTAMP WHERE id = ?", (int(tid),))
                    conn.commit()
                    conn.close()
                    st.success("Marked opened.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
        with colb:
            if st.button("🖱️ Mark Clicked (+1)") and sel_ids:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    for tid in sel_ids:
                        cur.execute("UPDATE email_tracking SET clicked_at = COALESCE(clicked_at, CURRENT_TIMESTAMP), click_count = COALESCE(click_count, 0) + 1 WHERE id = ?", (int(tid),))
                    conn.commit()
                    conn.close()
                    st.success("Marked clicked.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
    except Exception as e:
        st.error(f"Failed to load tracking: {e}")

def _queue_metrics() -> dict:
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM send_queue WHERE status = 'queued'")
        queued = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM send_queue WHERE status = 'sent' AND datetime(created_at) >= datetime('now','-1 hour')")
        sent_1h = cur.fetchone()[0]
        conn.close()
        return {"queued": queued, "sent_last_hour": sent_1h}
    except Exception:
        return {"queued": 0, "sent_last_hour": 0}

def _clear_user_queue(user_id: int) -> int:
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM send_queue WHERE user_id = ? AND status = 'queued'", (user_id,))
        affected = cur.rowcount if hasattr(cur, 'rowcount') else 0
        conn.commit()
        conn.close()
    except Exception:
        affected = 0
    return affected

def show_analytics():
    """Show analytics dashboard"""
    st.markdown("## 📊 Analytics Dashboard")
    
    analytics = get_analytics(st.session_state.user['id'])
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", analytics['lead_count'])
    with col2:
        st.metric("Total Campaigns", analytics['campaign_count'])
    with col3:
        st.metric("Emails Sent", analytics['sent_emails'])
    with col4:
        open_rate = (analytics['opened_emails'] / analytics['sent_emails'] * 100) if analytics['sent_emails'] > 0 else 0
        st.metric("Open Rate", f"{open_rate:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Lead Distribution")
        leads_df = get_user_leads(st.session_state.user['id'])
        if not leads_df.empty:
            category_counts = leads_df['category'].value_counts()
            fig = px.pie(values=category_counts.values, names=category_counts.index, title="Lead Categories")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📧 Email Performance")
        if analytics['sent_emails'] > 0:
            performance_data = {
                'Metric': ['Sent', 'Opened', 'Clicked'],
                'Count': [analytics['sent_emails'], analytics['opened_emails'], analytics['clicked_emails']]
            }
            fig = px.bar(performance_data, x='Metric', y='Count', title="Email Performance")
            st.plotly_chart(fig, use_container_width=True)

def show_ai_assistant():
    """Show AI assistant interface"""
    st.markdown("## 🤖 AI Assistant")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="dashboard-card">
            <h3>📝 AI Email Writer</h3>
            <p>Generate personalized email content using AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Email generation
        with st.form("ai_email_form"):
            email_prompt = st.text_area(
                "Describe your email",
                placeholder="e.g., Write a follow-up email for a graphic design client who hasn't responded to my proposal",
                height=100
            )
            
            if st.form_submit_button("🤖 Generate Email", type="primary"):
                if email_prompt:
                    with st.spinner("AI is generating your email..."):
                        generated_content = generate_email_content(email_prompt)
                        st.text_area("Generated Email", value=generated_content, height=200)
                else:
                    st.warning("Please enter a description for your email")
    
    with col2:
        st.markdown("""
        <div class="dashboard-card">
            <h3>🎯 Subject Line Generator</h3>
            <p>AI-powered subject line suggestions</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Subject line generation
        with st.form("ai_subject_form"):
            topic = st.text_input("Email Topic", placeholder="e.g., Follow-up on design proposal")
            
            if st.form_submit_button("🎯 Generate Subject", type="primary"):
                if topic:
                    with st.spinner("AI is generating subject lines..."):
                        generated_subject = generate_subject_line(topic)
                        st.text_input("Generated Subject Line", value=generated_subject)
                else:
                    st.warning("Please enter a topic for your email")

def show_templates_page():
    """Manage user templates (CRUD)"""
    st.markdown("## 🧩 Templates")
    with st.form("template_form_full"):
        t_name = st.text_input("Template Name")
        t_subject = st.text_input("Template Subject")
        t_body = st.text_area("Template Body", height=160)
        coltx, colty, coltz = st.columns(3)
        save_t = coltx.form_submit_button("💾 Save/Update")
        del_t = colty.form_submit_button("🗑️ Delete")
        load_t = coltz.form_submit_button("📥 Load to Editor")
        if save_t and t_name and t_subject and t_body:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO templates (user_id, name, subject, body)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, name) DO UPDATE SET subject=excluded.subject, body=excluded.body
                    """,
                    (st.session_state.user['id'], t_name, t_subject, t_body),
                )
                conn.commit()
                conn.close()
                st.success("Template saved.")
            except Exception as e:
                st.error(f"Failed to save template: {e}")
        if del_t and t_name:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("DELETE FROM templates WHERE user_id = ? AND name = ?", (st.session_state.user['id'], t_name))
                conn.commit()
                conn.close()
                st.success("Template deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete template: {e}")
        if load_t and t_name:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("SELECT subject, body FROM templates WHERE user_id = ? AND name = ?", (st.session_state.user['id'], t_name))
                row = cur.fetchone()
                conn.close()
                if row:
                    st.session_state.generated_subject = row[0]
                    st.session_state.improved_content = row[1]
                    st.success("Loaded into email editor fields (in Email Campaigns page).")
                else:
                    st.info("Template not found.")
            except Exception as e:
                st.error(f"Failed to load template: {e}")

    # List templates
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name, subject, created_at FROM templates WHERE user_id = ? ORDER BY created_at DESC", (st.session_state.user['id'],))
        rows = cur.fetchall()
        conn.close()
        if rows:
            st.markdown("#### Your Templates")
            st.dataframe(pd.DataFrame(rows, columns=["name","subject","created_at"]))
        else:
            st.info("No templates yet. Create one above.")
    except Exception:
        pass

def show_audit_logs():
    """Display recent audit logs"""
    st.markdown("## 🛡️ Audit Logs")
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT action, details, created_at FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 200", (st.session_state.user['id'],))
        rows = cur.fetchall()
        conn.close()
        if rows:
            st.dataframe(pd.DataFrame(rows, columns=["action","details","created_at"]))
        else:
            st.info("No audit logs yet.")
    except Exception as e:
        st.error(f"Failed to load logs: {e}")

def show_settings():
    """Show settings page"""
    st.markdown("## ⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👤 User Profile")
        st.text_input("Username", value=st.session_state.user['username'], disabled=True)
        st.text_input("Email", value=st.session_state.user['email'], disabled=True)
        st.text_input("Role", value=st.session_state.user['role'].title(), disabled=True)
    
    with col2:
        st.markdown("### 🔧 System Configuration")
        st.checkbox("Email Notifications", value=True)
        st.checkbox("SMS Notifications", value=False)
        st.slider("Email Send Rate (per minute)", 1, 10, 3)
    
    # Email (per-user SMTP) configuration
    st.markdown("### ✉️ Email (Per-User SMTP)")
    with st.form("smtp_settings_form"):
        colA, colB = st.columns(2)
        with colA:
            host = st.text_input("SMTP Host", os.getenv("SMTP_HOST", ""))
            port = st.number_input("SMTP Port", min_value=1, max_value=65535, value=int(os.getenv("SMTP_PORT", "587")))
            username = st.text_input("SMTP Username", os.getenv("SMTP_USER", ""))
        with colB:
            from_email = st.text_input("From Email", os.getenv("SMTP_FROM", ""))
            use_tls = st.checkbox("Use TLS", value=True)
            use_ssl = st.checkbox("Use SSL", value=False)
        rate_limit = st.number_input("Max emails per minute (per-user)", min_value=1, max_value=300, value=30)
        password = st.text_input("SMTP Password / App Password", type="password")
        save_btn = st.form_submit_button("💾 Save SMTP Settings", type="primary")
        if save_btn:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO email_credentials (user_id, provider, host, port, username, password, from_email, use_tls, use_ssl, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        provider=excluded.provider,
                        host=excluded.host,
                        port=excluded.port,
                        username=excluded.username,
                        password=excluded.password,
                        from_email=excluded.from_email,
                        use_tls=excluded.use_tls,
                        use_ssl=excluded.use_ssl,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        st.session_state.user['id'],
                        "smtp",
                        host,
                        int(port),
                        username,
                        password,
                        from_email,
                        1 if use_tls else 0,
                        1 if use_ssl else 0,
                    ),
                )
                conn.commit()
                conn.close()
                # store rate limit in session for now
                st.session_state["rate_limit_per_minute"] = int(rate_limit)
                st.success("SMTP settings saved for your account.")
            except Exception as e:
                st.error(f"Failed to save SMTP settings: {e}")

    # Send test email
    st.markdown("### ✅ Send Test Email")
    test_to = st.text_input("Test Recipient Email", value=st.session_state.user['email'])
    if st.button("📨 Send Test Email"):
        ok = send_email_simulation(test_to, "LeadAI Pro - Test Email", "This is a test email from your SMTP configuration.")
        if ok:
            st.success("Test email attempted. Check recipient inbox/spam.")
        else:
            st.error("Failed to send test email.")

    # Suppression list management
    st.markdown("### 🚫 Suppression List")
    sup_add = st.text_input("Add email to suppression list")
    colx, coly = st.columns([1,1])
    with colx:
        if st.button("➕ Add") and sup_add:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR IGNORE INTO suppression_list (user_id, email, reason) VALUES (?, ?, ?)",
                    (st.session_state.user['id'], sup_add.strip(), 'manual'),
                )
                conn.commit()
                conn.close()
                st.success("Added to suppression list.")
            except Exception as e:
                st.error(f"Failed to add: {e}")
    with coly:
        if st.button("🗑️ Clear All (Your Account)"):
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("DELETE FROM suppression_list WHERE user_id = ?", (st.session_state.user['id'],))
                conn.commit()
                conn.close()
                st.success("Suppression list cleared for your account.")
            except Exception as e:
                st.error(f"Failed to clear: {e}")
    # List suppressed
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT email, reason, created_at FROM suppression_list WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", (st.session_state.user['id'],))
        rows = cur.fetchall()
        conn.close()
        if rows:
            st.markdown("#### Current Suppressed Emails")
            st.dataframe(pd.DataFrame(rows, columns=["email","reason","created_at"]))
        else:
            st.info("No suppressed emails.")
    except Exception:
        pass

    st.markdown("### 📨 Queue Controls")
    qm = _queue_metrics()
    colq1, colq2, colq3 = st.columns(3)
    with colq1:
        st.metric("Queued Emails", qm.get("queued", 0))
    with colq2:
        st.metric("Sent (last hour)", qm.get("sent_last_hour", 0))
    with colq3:
        if st.button("🧹 Clear My Queued Emails (Settings)"):
            n = _clear_user_queue(st.session_state.user['id'])
            st.success(f"Cleared {n} queued emails for your account.")
            st.rerun()

    # Template library
    st.markdown("### 🧩 Template Library")
    with st.form("template_form"):
        t_name = st.text_input("Template Name")
        t_subject = st.text_input("Template Subject")
        t_body = st.text_area("Template Body", height=160)
        save_t = st.form_submit_button("💾 Save Template")
        if save_t and t_name and t_subject and t_body:
            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO templates (user_id, name, subject, body)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, name) DO UPDATE SET subject=excluded.subject, body=excluded.body
                    """,
                    (st.session_state.user['id'], t_name, t_subject, t_body),
                )
                conn.commit()
                conn.close()
                st.success("Template saved.")
            except Exception as e:
                st.error(f"Failed to save template: {e}")

    # List templates
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name, subject FROM templates WHERE user_id = ? ORDER BY created_at DESC", (st.session_state.user['id'],))
        rows = cur.fetchall()
        conn.close()
        if rows:
            st.markdown("#### Your Templates")
            for name, subj in rows[:10]:
                st.write(f"- {name} — {subj}")
        else:
            st.info("No templates yet. Create one above.")
    except Exception:
        pass

    # About section
    st.markdown("### ℹ️ About LeadAI Pro")
    st.info("""
    **LeadAI Pro** is an AI-powered lead management and email marketing platform.
    
    **Features:**
    - AI-powered email generation
    - Lead management and scoring
    - Email campaign automation
    - Analytics and tracking
    - Free Hugging Face AI models
    
    **Version:** 1.0.0 (Local Development)
    **Deployment:** Ready for Hugging Face Spaces
    """)

if __name__ == "__main__":
    main()
