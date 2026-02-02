"""
Settings Page - User Configuration and System Settings
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

def load_settings_css():
    """Load custom CSS for settings page"""
    st.markdown("""
    <style>
    .settings-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .settings-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="settings" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="2" fill="rgba(255,255,255,0.1)"/><path d="M 10 0 L 10 20 M 0 10 L 20 10" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23settings)"/></svg>');
        opacity: 0.3;
    }
    
    .settings-content {
        position: relative;
        z-index: 1;
    }
    
    .settings-card {
        background: var(--surface-dark);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .settings-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .subscription-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .subscription-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="premium" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M 15 0 L 15 30 M 0 15 L 30 15" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/><circle cx="15" cy="15" r="3" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23premium)"/></svg>');
        opacity: 0.3;
    }
    
    .subscription-content {
        position: relative;
        z-index: 1;
    }
    
    .plan-card {
        background: var(--surface-dark);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .plan-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        border-color: var(--primary-color);
    }
    
    .plan-card.selected {
        border-color: var(--primary-color);
        background: rgba(99, 102, 241, 0.1);
    }
    
    .plan-price {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin: 0;
    }
    
    .plan-features {
        list-style: none;
        padding: 0;
        margin: 1rem 0;
    }
    
    .plan-features li {
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .plan-features li:last-child {
        border-bottom: none;
    }
    
    .plan-features li::before {
        content: '✓';
        color: #4CAF50;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    .user-profile {
        background: var(--surface-dark);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .profile-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(45deg, #667eea, #764ba2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        color: white;
        margin: 0 auto 1rem;
    }
    
    .notification-card {
        background: var(--surface-dark);
        border-radius: 0.75rem;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .toggle-switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 34px;
    }
    
    .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }
    
    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
        border-radius: 34px;
    }
    
    .slider:before {
        position: absolute;
        content: "";
        height: 26px;
        width: 26px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
    }
    
    input:checked + .slider {
        background-color: var(--primary-color);
    }
    
    input:checked + .slider:before {
        transform: translateX(26px);
    }
    
    .security-card {
        background: var(--surface-dark);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .api-key {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
        word-break: break-all;
    }
    
    .danger-zone {
        background: linear-gradient(45deg, #F44336, #D32F2F);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
    }
    
    .danger-zone h4 {
        color: white;
        margin-top: 0;
    }
    
    .danger-button {
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .danger-button:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

def show_settings():
    """Main settings interface"""
    load_settings_css()
    
    st.markdown("""
    <div class="settings-header">
        <div class="settings-content">
            <h3>⚙️ Settings & Configuration</h3>
            <p>Manage your account, subscription, and system preferences</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Profile", "💳 Subscription", "🔔 Notifications", "🔒 Security", "⚙️ System"])
    
    with tab1:
        show_profile_settings()
    
    with tab2:
        show_subscription_settings()
    
    with tab3:
        show_notification_settings()
    
    with tab4:
        show_security_settings()
    
    with tab5:
        show_system_settings()

def show_profile_settings():
    """User profile settings"""
    st.markdown("### 👤 User Profile")
    
    # Profile Information
    st.markdown("""
    <div class="user-profile">
        <div class="profile-avatar">JD</div>
        <h4 style="text-align: center; margin: 0;">John Doe</h4>
        <p style="text-align: center; color: var(--text-secondary); margin: 0.5rem 0;">john.doe@example.com</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Profile Form
    st.markdown("#### 📝 Edit Profile Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name", value="John Doe", key="prof_full_name")
        email = st.text_input("Email Address", value="john.doe@example.com", key="prof_email")
        phone = st.text_input("Phone Number", value="+1 (555) 123-4567", key="prof_phone")
    
    with col2:
        company = st.text_input("Company", value="Acme Corporation", key="prof_company")
        job_title = st.text_input("Job Title", value="Marketing Manager", key="prof_job_title")
        timezone = st.selectbox("Timezone", ["UTC-8 (PST)", "UTC-5 (EST)", "UTC+0 (GMT)", "UTC+1 (CET)"])
    
    # Role and Permissions
    st.markdown("#### 🎭 Role & Permissions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        role = st.selectbox("User Role", ["Admin", "Manager", "Client"], index=0)
        subscription_plan = st.selectbox("Subscription Plan", ["Free", "Pro", "Enterprise"], index=1)
    
    with col2:
        account_status = st.selectbox("Account Status", ["Active", "Suspended", "Pending"])
        last_login = st.text_input("Last Login", value="2024-01-15 14:30:25", disabled=True, key="prof_last_login")
    
    # Save Changes
    if st.button("💾 Save Profile Changes", type="primary"):
        st.success("✅ Profile updated successfully!")

def show_subscription_settings():
    """Subscription and billing settings"""
    st.markdown("### 💳 Subscription & Billing")
    
    # Current Subscription
    st.markdown("""
    <div class="subscription-card">
        <div class="subscription-content">
            <h3>🚀 Pro Plan</h3>
            <p>You're currently on the Pro plan with advanced features and higher limits</p>
            <p><strong>Next billing date:</strong> February 15, 2024</p>
            <p><strong>Amount:</strong> $49.00/month</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Subscription Plans
    st.markdown("#### 📋 Available Plans")
    
    plans = [
        {
            "name": "Free",
            "price": "$0",
            "period": "month",
            "description": "Perfect for getting started",
            "features": [
                "Up to 1,000 leads",
                "5 email campaigns",
                "Basic analytics",
                "Email support"
            ],
            "current": False
        },
        {
            "name": "Pro",
            "price": "$49",
            "period": "month",
            "description": "Most popular for growing businesses",
            "features": [
                "Up to 10,000 leads",
                "50 email campaigns",
                "Advanced analytics",
                "AI-powered features",
                "Priority support"
            ],
            "current": True
        },
        {
            "name": "Enterprise",
            "price": "$199",
            "period": "month",
            "description": "For large organizations",
            "features": [
                "Unlimited leads",
                "Unlimited campaigns",
                "Custom analytics",
                "Full AI suite",
                "Dedicated support",
                "Custom integrations"
            ],
            "current": False
        }
    ]
    
    cols = st.columns(3)
    
    for i, plan in enumerate(plans):
        with cols[i]:
            current_class = "selected" if plan['current'] else ""
            st.markdown(f"""
            <div class="plan-card {current_class}">
                <h3>{plan['name']}</h3>
                <div class="plan-price">{plan['price']}<span style="font-size: 1rem; color: var(--text-secondary);">/{plan['period']}</span></div>
                <p style="color: var(--text-secondary);">{plan['description']}</p>
                <ul class="plan-features">
                    {''.join([f'<li>{feature}</li>' for feature in plan['features']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Billing Information
    st.markdown("#### 💳 Billing Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        billing_email = st.text_input("Billing Email", value="billing@example.com", key="bill_email")
        card_number = st.text_input("Card Number", value="**** **** **** 1234", disabled=True, key="bill_card")
    
    with col2:
        billing_address = st.text_area("Billing Address", value="123 Main St\nNew York, NY 10001")
        expiry_date = st.text_input("Expiry Date", value="12/25", disabled=True, key="bill_expiry")
    
    # Billing History
    st.markdown("#### 📊 Billing History")
    
    billing_history = pd.DataFrame({
        'Date': ['2024-01-15', '2023-12-15', '2023-11-15', '2023-10-15'],
        'Amount': ['$49.00', '$49.00', '$49.00', '$49.00'],
        'Status': ['Paid', 'Paid', 'Paid', 'Paid'],
        'Invoice': ['INV-001', 'INV-002', 'INV-003', 'INV-004']
    })
    
    st.dataframe(billing_history, use_container_width=True)
    
    # Plan Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Change Plan", type="primary", use_container_width=True):
            st.info("Plan change functionality would open here")
    
    with col2:
        if st.button("📄 Download Invoice", type="secondary", use_container_width=True):
            st.info("Invoice download would start here")
    
    with col3:
        if st.button("❌ Cancel Subscription", type="secondary", use_container_width=True):
            st.warning("Are you sure you want to cancel your subscription?")

def show_notification_settings():
    """Notification preferences"""
    st.markdown("### 🔔 Notification Preferences")
    
    # Email Notifications
    st.markdown("#### 📧 Email Notifications")
    
    email_notifications = [
        {"name": "New Lead Alerts", "description": "Get notified when new high-quality leads are added", "enabled": True},
        {"name": "Campaign Results", "description": "Receive reports on email campaign performance", "enabled": True},
        {"name": "System Updates", "description": "Important updates about the platform", "enabled": True},
        {"name": "Billing Notifications", "description": "Payment confirmations and billing reminders", "enabled": True},
        {"name": "Weekly Reports", "description": "Weekly summary of your account activity", "enabled": False},
        {"name": "AI Insights", "description": "AI-generated insights and recommendations", "enabled": True}
    ]
    
    for notification in email_notifications:
        st.markdown(f"""
        <div class="notification-card">
            <div>
                <h4>{notification['name']}</h4>
                <p style="color: var(--text-secondary); margin: 0;">{notification['description']}</p>
            </div>
            <div>
                <label class="toggle-switch">
                    <input type="checkbox" {'checked' if notification['enabled'] else ''}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Push Notifications
    st.markdown("#### 📱 Push Notifications")
    
    push_notifications = [
        {"name": "Real-time Alerts", "description": "Instant notifications for important events", "enabled": True},
        {"name": "Mobile App", "description": "Notifications on mobile devices", "enabled": False},
        {"name": "Browser Notifications", "description": "Notifications in your web browser", "enabled": True}
    ]
    
    for notification in push_notifications:
        st.markdown(f"""
        <div class="notification-card">
            <div>
                <h4>{notification['name']}</h4>
                <p style="color: var(--text-secondary); margin: 0;">{notification['description']}</p>
            </div>
            <div>
                <label class="toggle-switch">
                    <input type="checkbox" {'checked' if notification['enabled'] else ''}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Notification Frequency
    st.markdown("#### ⏰ Notification Frequency")
    
    col1, col2 = st.columns(2)
    
    with col1:
        email_frequency = st.selectbox("Email Frequency", ["Immediate", "Hourly", "Daily", "Weekly"])
        quiet_hours = st.time_input("Quiet Hours Start", value=None)
    
    with col2:
        digest_frequency = st.selectbox("Digest Frequency", ["Daily", "Weekly", "Monthly"])
        quiet_hours_end = st.time_input("Quiet Hours End", value=None)
    
    # Save Settings
    if st.button("💾 Save Notification Settings", type="primary"):
        st.success("✅ Notification settings updated successfully!")

def show_security_settings():
    """Security and privacy settings"""
    st.markdown("### 🔒 Security & Privacy")
    
    # Password Settings
    st.markdown("#### 🔑 Password & Authentication")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_password = st.text_input("Current Password", type="password", key="sec_curr_pass")
        new_password = st.text_input("New Password", type="password", key="sec_new_pass")
    
    with col2:
        confirm_password = st.text_input("Confirm New Password", type="password", key="sec_conf_pass")
        password_strength = st.progress(0.7)
        st.text("Password Strength: Strong")
    
    if st.button("🔑 Change Password", type="primary"):
        if new_password == confirm_password:
            st.success("✅ Password changed successfully!")
        else:
            st.error("❌ Passwords do not match")
    
    # Two-Factor Authentication
    st.markdown("#### 🔐 Two-Factor Authentication")
    
    col1, col2 = st.columns(2)
    
    with col1:
        two_fa_enabled = st.checkbox("Enable Two-Factor Authentication", value=True)
        backup_codes = st.text_input("Backup Codes", value="1234-5678-9012", disabled=True, key="sec_backup_codes")
    
    with col2:
        authenticator_app = st.text_input("Authenticator App", value="Google Authenticator", key="sec_auth_app")
        phone_number = st.text_input("Phone Number", value="+1 (555) 123-4567", key="sec_phone")
    
    # API Keys
    st.markdown("#### 🔑 API Keys")
    
    st.markdown("""
    <div class="security-card">
        <h4>API Access</h4>
        <p>Use these API keys to integrate with external applications</p>
        <div class="api-key">
            <strong>API Key:</strong> ak_live_1234567890abcdef1234567890abcdef
        </div>
        <div class="api-key">
            <strong>Secret Key:</strong> sk_live_abcdef1234567890abcdef1234567890
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Regenerate API Keys", type="secondary"):
            st.warning("Are you sure you want to regenerate your API keys? This will invalidate existing keys.")
    
    with col2:
        if st.button("📋 Copy API Key", type="secondary"):
            st.info("API key copied to clipboard")
    
    # Privacy Settings
    st.markdown("#### 🛡️ Privacy Settings")
    
    privacy_options = [
        {"name": "Data Analytics", "description": "Allow usage data to improve the platform", "enabled": True},
        {"name": "Email Tracking", "description": "Track email opens and clicks", "enabled": True},
        {"name": "Lead Scoring", "description": "Use AI to score leads", "enabled": True},
        {"name": "Third-party Integrations", "description": "Allow data sharing with integrated services", "enabled": False}
    ]
    
    for option in privacy_options:
        st.markdown(f"""
        <div class="notification-card">
            <div>
                <h4>{option['name']}</h4>
                <p style="color: var(--text-secondary); margin: 0;">{option['description']}</p>
            </div>
            <div>
                <label class="toggle-switch">
                    <input type="checkbox" {'checked' if option['enabled'] else ''}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Danger Zone
    st.markdown("#### ⚠️ Danger Zone")
    
    st.markdown("""
    <div class="danger-zone">
        <h4>⚠️ Danger Zone</h4>
        <p>These actions are irreversible. Please proceed with caution.</p>
        <div style="margin-top: 1rem;">
            <button class="danger-button">🗑️ Delete Account</button>
            <button class="danger-button">📊 Export All Data</button>
            <button class="danger-button">🔄 Reset All Settings</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_system_settings():
    """System configuration settings"""
    st.markdown("### ⚙️ System Configuration")
    
    # General Settings
    st.markdown("#### 🌐 General Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.selectbox("Language", ["English", "Spanish", "French", "German", "Chinese"])
        date_format = st.selectbox("Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        time_format = st.selectbox("Time Format", ["12-hour", "24-hour"])
    
    with col2:
        currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "CAD", "AUD"])
        number_format = st.selectbox("Number Format", ["1,234.56", "1.234,56", "1 234,56"])
        theme = st.selectbox("Theme", ["Dark", "Light", "Auto"])
    
    # Email Settings
    st.markdown("#### 📧 Email Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com", key="sys_smtp_server")
        smtp_port = st.number_input("SMTP Port", value=587, key="sys_smtp_port")
        smtp_username = st.text_input("SMTP Username", value="your-email@gmail.com", key="sys_smtp_user")
    
    with col2:
        smtp_password = st.text_input("SMTP Password", type="password", value="your-app-password", key="sys_smtp_pass")
        from_email = st.text_input("From Email", value="noreply@yourcompany.com", key="sys_from_email")
        from_name = st.text_input("From Name", value="Your Company", key="sys_from_name")
    
    # Rate Limiting
    st.markdown("#### 🚦 Rate Limiting")
    
    col1, col2 = st.columns(2)
    
    with col1:
        email_delay = st.slider("Email Send Delay (seconds)", 10, 120, 20)
        max_emails_hour = st.slider("Max Emails per Hour", 50, 1000, 100)
    
    with col2:
        max_emails_day = st.slider("Max Emails per Day", 500, 10000, 1000)
        retry_attempts = st.slider("Retry Attempts", 1, 5, 3)
    
    # AI Settings
    st.markdown("#### 🤖 AI Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ai_scoring = st.checkbox("Enable AI Lead Scoring", value=True)
        ai_optimization = st.checkbox("Enable AI Email Optimization", value=True)
        ai_insights = st.checkbox("Enable AI Insights", value=True)
    
    with col2:
        openai_api_key = st.text_input("OpenAI API Key", type="password", value="sk-...", key="sys_openai_key")
        ai_model = st.selectbox("AI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        ai_confidence = st.slider("AI Confidence Threshold", 0.0, 1.0, 0.7, 0.1)
    
    # Data Management
    st.markdown("#### 💾 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        data_retention = st.selectbox("Data Retention Period", ["1 year", "2 years", "5 years", "Forever"])
        auto_backup = st.checkbox("Enable Automatic Backups", value=True)
        backup_frequency = st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
    
    with col2:
        data_export = st.checkbox("Allow Data Export", value=True)
        data_anonymization = st.checkbox("Enable Data Anonymization", value=False)
        gdpr_compliance = st.checkbox("GDPR Compliance Mode", value=True)
    
    # Integration Settings
    st.markdown("#### 🔗 Integration Settings")
    
    integrations = [
        {"name": "CRM Integration", "description": "Connect with your CRM system", "enabled": True},
        {"name": "Email Marketing", "description": "Integrate with email marketing tools", "enabled": False},
        {"name": "Analytics", "description": "Connect with analytics platforms", "enabled": True},
        {"name": "Webhooks", "description": "Enable webhook notifications", "enabled": False}
    ]
    
    for integration in integrations:
        st.markdown(f"""
        <div class="notification-card">
            <div>
                <h4>{integration['name']}</h4>
                <p style="color: var(--text-secondary); margin: 0;">{integration['description']}</p>
            </div>
            <div>
                <label class="toggle-switch">
                    <input type="checkbox" {'checked' if integration['enabled'] else ''}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Save Settings
    if st.button("💾 Save System Settings", type="primary"):
        st.success("✅ System settings updated successfully!")
    
    # Reset Settings
    if st.button("🔄 Reset to Defaults", type="secondary"):
        st.warning("Are you sure you want to reset all settings to their default values?")
