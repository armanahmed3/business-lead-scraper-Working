"""
AI SaaS Platform - Main Streamlit Application
A complete lead management and email marketing platform with AI capabilities
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

# Configure Streamlit page
st.set_page_config(
    page_title="LeadAI Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import custom CSS and components
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

def main():
    """Main application entry point"""
    load_css()
    
    # Header
    st.markdown("""
    <div class="cinematic-header">
        <div class="header-content">
            <h1 class="main-title">🚀 LeadAI Pro</h1>
            <p class="subtitle">AI-Powered Lead Management & Email Marketing Platform</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        page = st.selectbox(
            "Choose a page",
            ["Dashboard", "Lead Management", "Email Campaigns", "Email Tracking", "Data Analytics", "AI Tools", "Settings"],
            key="nav_select"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Leads", "1,234", "↗️ 12%")
        with col2:
            st.metric("Emails", "5,678", "↗️ 8%")
        
        st.markdown("---")
        st.markdown("### 🚀 Quick Actions")
        if st.button("📁 Upload Leads", use_container_width=True):
            st.session_state.nav_select = "Lead Management"
            st.rerun()
        
        if st.button("✍️ Create Campaign", use_container_width=True):
            st.session_state.nav_select = "Email Campaigns"
            st.rerun()
        
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.nav_select = "Data Analytics"
            st.rerun()
    
    # Main Content Area
    if page == "Dashboard":
        show_dashboard()
    elif page == "Lead Management":
        from pages.lead_management import show_lead_management
        show_lead_management()
    elif page == "Email Campaigns":
        from pages.email_campaigns import show_email_campaigns
        show_email_campaigns()
    elif page == "Email Tracking":
        from pages.email_tracking import show_email_tracking
        show_email_tracking()
    elif page == "Data Analytics":
        from pages.data_analytics import show_data_analytics
        show_data_analytics()
    elif page == "AI Tools":
        from pages.ai_tools import show_ai_tools
        show_ai_tools()
    elif page == "Settings":
        from pages.settings import show_settings
        show_settings()

def show_dashboard():
    """Display the main dashboard"""
    st.markdown("## 📊 Dashboard Overview")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">1,234</div>
            <div class="metric-label">Total Leads</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">89%</div>
            <div class="metric-label">Open Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">23%</div>
            <div class="metric-label">Click Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">$12.5K</div>
            <div class="metric-label">Revenue</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Section
    st.markdown("## 📈 Performance Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="dashboard-card">
            <h3>📊 Campaign Performance</h3>
            <p>Real-time analytics and insights</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-card">
            <h3>🎯 Lead Quality Score</h3>
            <p>AI-powered lead scoring analysis</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
