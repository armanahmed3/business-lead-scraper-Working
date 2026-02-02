"""
Simplified LeadAI Pro - Main Application
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Configure Streamlit page
st.set_page_config(
    page_title="LeadAI Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
        color: white;
        text-align: center;
    }
    
    .nav-button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        margin: 0.5rem;
        cursor: pointer;
        font-size: 1.1rem;
        font-weight: 600;
        transition: transform 0.3s ease;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
    }
    
    .metric-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    load_css()
    
    # Header
    st.markdown("""
    <div class="header">
        <h1>🚀 LeadAI Pro</h1>
        <p>AI-Powered Lead Management & Email Marketing Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    st.subheader("📋 Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 Lead Management", key="nav_lead", use_container_width=True):
            st.session_state.page = "lead_management"
            st.rerun()
        
        if st.button("📧 Email Campaigns", key="nav_campaign", use_container_width=True):
            st.session_state.page = "email_campaigns"
            st.rerun()
    
    with col2:
        if st.button("📊 Email Tracking", key="nav_tracking", use_container_width=True):
            st.session_state.page = "email_tracking"
            st.rerun()
        
        if st.button("📈 Data Analytics", key="nav_analytics", use_container_width=True):
            st.session_state.page = "data_analytics"
            st.rerun()
    
    with col3:
        if st.button("🤖 AI Tools", key="nav_ai", use_container_width=True):
            st.session_state.page = "ai_tools"
            st.rerun()
        
        if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
            st.session_state.page = "settings"
            st.rerun()
    
    # Initialize page state
    if 'page' not in st.session_state:
        st.session_state.page = "dashboard"
    
    # Page content
    if st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "lead_management":
        from pages.lead_management import show_lead_management
        show_lead_management()
    elif st.session_state.page == "email_campaigns":
        from pages.email_campaigns import show_email_campaigns
        show_email_campaigns()
    elif st.session_state.page == "email_tracking":
        from pages.email_tracking import show_email_tracking
        show_email_tracking()
    elif st.session_state.page == "data_analytics":
        from pages.data_analytics import show_data_analytics
        show_data_analytics()
    elif st.session_state.page == "ai_tools":
        from pages.ai_tools import show_ai_tools
        show_ai_tools()
    elif st.session_state.page == "settings":
        from pages.settings import show_settings
        show_settings()

def show_dashboard():
    """Display the main dashboard"""
    st.subheader("📊 Dashboard Overview")
    
    # Get real data
    try:
        from lead_database import lead_db
        from email_sender import email_sender
        
        # Lead statistics
        lead_stats = lead_db.get_lead_statistics()
        
        # Email statistics
        all_emails = email_sender.get_all_emails()
        total_emails = len(all_emails)
        sent_emails = len([e for e in all_emails if e['status'] in ['sent', 'opened', 'clicked', 'replied']])
        opened_emails = len([e for e in all_emails if e['status'] in ['opened', 'clicked', 'replied']])
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{lead_stats['total_leads']}</div>
                <div class="metric-label">Total Leads</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_emails}</div>
                <div class="metric-label">Emails Sent</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            open_rate = (opened_emails / sent_emails * 100) if sent_emails > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{open_rate:.1f}%</div>
                <div class="metric-label">Open Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            delivery_rate = (sent_emails / total_emails * 100) if total_emails > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{delivery_rate:.1f}%</div>
                <div class="metric-label">Delivery Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("📁 **Upload Leads**: Go to Lead Management to upload CSV files with customer data")
        
        with col2:
            st.info("📧 **Send Emails**: Create campaigns and send personalized emails to your leads")
        
        with col3:
            st.info("📊 **Track Results**: Monitor email delivery, opens, and engagement in real-time")
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.info("Please make sure all required files are in place.")

if __name__ == "__main__":
    main()
