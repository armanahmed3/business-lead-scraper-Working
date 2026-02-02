"""
Email Campaigns Page - Campaign Management and Tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from lead_database import lead_db
from ai_email_generator import ai_email_generator
from email_sender import email_sender
from email_scheduler import email_scheduler

def load_campaign_css():
    """Load custom CSS for email campaigns page"""
    st.markdown("""
    <style>
    .campaign-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .campaign-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.3;
    }
    
    .campaign-content {
        position: relative;
        z-index: 1;
    }
    
    .campaign-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .campaign-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .form-section {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: #2d5016;
    }
    
    .success-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #2d5016;
    }
    </style>
    """, unsafe_allow_html=True)

def generate_campaign_metrics():
    """Generate sample campaign metrics"""
    return {
        'total_campaigns': random.randint(15, 25),
        'active_campaigns': random.randint(3, 8),
        'total_emails_sent': random.randint(5000, 15000),
        'open_rate': round(random.uniform(20, 35), 1),
        'click_rate': round(random.uniform(2, 5), 1),
        'conversion_rate': round(random.uniform(1, 3), 1),
        'bounce_rate': round(random.uniform(1, 3), 1)
    }

def show_email_campaigns():
    """Email Campaigns Dashboard"""
    load_campaign_css()
    
    st.markdown("""
    <div class="campaign-header">
        <div class="campaign-content">
            <h1>📧 Email Campaigns</h1>
            <p>Create, manage, and track your email marketing campaigns</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Real Campaign Metrics
    st.subheader("📊 Campaign Overview")
    
    # Get real email statistics
    all_emails = email_sender.get_all_emails()
    total_emails = len(all_emails)
    sent_emails = len([e for e in all_emails if e['status'] in ['sent', 'opened', 'clicked', 'replied']])
    opened_emails = len([e for e in all_emails if e['status'] in ['opened', 'clicked', 'replied']])
    clicked_emails = len([e for e in all_emails if e['status'] in ['clicked', 'replied']])
    
    open_rate = (opened_emails / sent_emails * 100) if sent_emails > 0 else 0
    click_rate = (clicked_emails / opened_emails * 100) if opened_emails > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Emails</h3>
            <h2>{total_emails:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Delivered</h3>
            <h2>{sent_emails:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Opened</h3>
            <h2>{opened_emails:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Clicked</h3>
            <h2>{clicked_emails:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Open Rate", f"{open_rate:.1f}%")
    with col2:
        st.metric("Click Rate", f"{click_rate:.1f}%")
    with col3:
        delivery_rate = (sent_emails / total_emails * 100) if total_emails > 0 else 0
        st.metric("Delivery Rate", f"{delivery_rate:.1f}%")
    
    # Create new campaign
    st.subheader("🚀 Create New Campaign")
    
    st.markdown("""
    <div class="form-section">
        <h3>📝 Campaign Details</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        campaign_name = st.text_input("Campaign Name", placeholder="e.g., Product Launch 2024")
        enable_ab_test = st.checkbox("🧪 Enable A/B Testing for Subject", help="Test two different subject lines to see which performs better.")
        
        if enable_ab_test:
            subject_a = st.text_input("Subject Line (Variant A)", value=st.session_state.get('subject_a', ''), placeholder="e.g., Exciting New Product Launch!")
            subject_b = st.text_input("Subject Line (Variant B)", value=st.session_state.get('subject_b', ''), placeholder="e.g., You won't believe what we just launched...")
            subject_line = subject_a # Default for display
        else:
            subject_line = st.text_input("Subject Line", placeholder="e.g., Exciting New Product Launch!")
            
        sender_name = st.text_input("Sender Name", placeholder="e.g., John Doe")
        sender_email = st.text_input("Sender Email", placeholder="e.g., john@company.com")
    
    with col2:
        campaign_type = st.selectbox("Campaign Type", ["Newsletter", "Promotional", "Transactional", "Welcome Series", "Re-engagement"])
        st.markdown("#### ⚡ Advanced Campaign Settings")
        smart_optimization = st.checkbox("🧠 Smart Auto-Optimization", value=True, help="AI will automatically adjust send times and wording for higher engagement.")
        anti_spam_shield = st.checkbox("🛡️ Enhanced Anti-Spam Shield", value=True, help="Uses human-like behavior patterns to avoid spam filters.")
        
    # Lead selection dropdown
    all_leads = lead_db.get_all_leads()
    if all_leads:
        # Get all categories
        categories = lead_db.get_all_categories()
        
        # Lead selection options
        lead_options = ["All Leads", "Hot Leads (80-100)", "Warm Leads (60-79)", "Cold Leads (0-59)", "Custom Selection"]
        
        # Add category options
        if categories:
            lead_options.extend([f"Category: {cat}" for cat in categories])
        
        target_audience = st.selectbox("Target Audience", lead_options)
        
        # Custom lead selection
        if target_audience == "Custom Selection":
            lead_names = [f"{lead['name']} ({lead['company']}) - Score: {lead['score']}" for lead in all_leads]
            selected_lead_names = st.multiselect("Select Specific Leads", lead_names)
            selected_leads = []
            for name in selected_lead_names:
                for lead in all_leads:
                    if f"{lead['name']} ({lead['company']}) - Score: {lead['score']}" == name:
                        selected_leads.append(lead)
                        break
        elif target_audience.startswith("Category: "):
            category_name = target_audience.replace("Category: ", "")
            selected_leads = lead_db.get_leads_by_category(category_name)
        else:
            selected_leads = []
            if target_audience == "Hot Leads (80-100)":
                selected_leads = lead_db.get_hot_leads()
            elif target_audience == "Warm Leads (60-79)":
                selected_leads = lead_db.get_warm_leads()
            elif target_audience == "Cold Leads (0-59)":
                selected_leads = lead_db.get_cold_leads()
            elif target_audience == "All Leads":
                selected_leads = all_leads
    else:
        st.warning("No leads found. Please upload leads first in the Lead Management page.")
        target_audience = "No Leads Available"
        selected_leads = []
        
        send_time = st.time_input("Send Time", value=datetime.now().time())
        send_date = st.date_input("Send Date", value=datetime.now().date())
    
    # Email content
    st.subheader("📄 Email Content")
    
    # AI Email Generation
    col1, col2 = st.columns(2)
    
    with col1:
        email_tone = st.selectbox("Email Tone", ["professional", "casual", "urgent"])
        use_ai_generation = st.checkbox("🤖 Use AI Email Generation", value=True)
    
    with col2:
        if st.button("🎯 Generate AI Email", type="primary"):
            if selected_leads:
                with st.spinner("🤖 AI is crafting your personalized email..."):
                    # Generate email for first lead as example
                    sample_lead = selected_leads[0]
                    api_key = st.session_state.get('openrouter_api_key')
                    ai_email = ai_email_generator.generate_email(sample_lead, email_tone, api_key=api_key)
                    
                    st.session_state['ai_generated_subject'] = ai_email['subject']
                    st.session_state['ai_generated_body'] = ai_email['body']
                    st.success("✨ AI Email Generated!")
            else:
                st.warning("Please select leads first to generate AI email")
    
    # Display AI generated content
    if 'ai_generated_subject' in st.session_state and 'ai_generated_body' in st.session_state:
        st.markdown("""
        <div class="success-box">
            <h4>🤖 AI Generated Email Content</h4>
        </div>
        """, unsafe_allow_html=True)
        
        ai_subject = st.text_input("AI Generated Subject", value=st.session_state.get('ai_generated_subject', ''))
        ai_body = st.text_area("AI Generated Body", value=st.session_state.get('ai_generated_body', ''), height=200)
        
        if st.button("✅ Use AI Generated Content"):
            email_content = ai_body
            subject_line = ai_subject
            st.success("AI generated content applied!")
    
    # Manual email content
    if not use_ai_generation:
        email_content = st.text_area(
            "Email Body",
            placeholder="Enter your email content here...\n\nYou can use placeholders like:\n- {name} for recipient name\n- {company} for company name\n- {title} for job title",
            height=200
        )
    else:
        email_content = st.session_state.get('ai_generated_body', '')
    
    # Show selected leads preview
    if selected_leads:
        st.subheader("👥 Selected Leads Preview")
        st.write(f"**{len(selected_leads)} leads selected for this campaign**")
        
        # Show first few leads
        preview_leads = selected_leads[:5]
        for lead in preview_leads:
            st.write(f"• {lead['name']} ({lead['company']}) - Score: {lead['score']}")
        
        if len(selected_leads) > 5:
            st.write(f"... and {len(selected_leads) - 5} more leads")
    
    # Campaign settings
    st.subheader("⚙️ Campaign Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        track_opens = st.checkbox("Track Opens", value=True)
        track_clicks = st.checkbox("Track Clicks", value=True)
    
    with col2:
        auto_reply = st.checkbox("Auto Reply", value=False)
        unsubscribe_link = st.checkbox("Include Unsubscribe Link", value=True)
    
    with col3:
        send_limit = st.number_input("Daily Send Limit", min_value=1, max_value=10000, value=1000)
        delay_between_emails = st.number_input("Delay Between Emails (seconds)", min_value=1, max_value=300, value=20)
    
    # Scheduling options
    st.subheader("⏰ Email Scheduling")
    
    col1, col2 = st.columns(2)
    
    with col1:
        send_option = st.radio("Send Option", ["Send Now", "Schedule for Later"], horizontal=True)
    
    with col2:
        if send_option == "Schedule for Later":
            send_date = st.date_input("Send Date", value=datetime.now().date())
            send_time = st.time_input("Send Time", value=datetime.now().time())
            send_datetime = datetime.combine(send_date, send_time)
        else:
            send_datetime = datetime.now()
    
    # Create campaign button
    button_text = "🚀 Send Now" if send_option == "Send Now" else "⏰ Schedule Campaign"
    if st.button(button_text, type="primary"):
        # SaaS Limit Check
        email_count = st.session_state.get('email_count', 0)
        email_limit = st.session_state.get('email_limit', 100)
        user_plan = st.session_state.get('user_plan', 'free').lower()
        is_unlimited = (user_plan == 'enterprise' or st.session_state.get('user_role') == 'admin')
        
        needed = len(selected_leads)
        if not is_unlimited and (email_count + needed > email_limit):
            st.error(f"❌ Email limit reached! You have {email_limit - email_count} remaining, but tried to send {needed}. Upgrade to ENTERPRISE for UNLIMITED emails.")
            return

        if campaign_name and subject_line and email_content and selected_leads:
            # Check if email credentials are configured
            if not email_sender.sender_email or not email_sender.sender_password:
                st.error("❌ Email credentials not configured. Please set up SMTP settings in your .env file.")
                st.info("Required: SMTP_USERNAME, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT")
                return
            
            # Calculate campaign metrics
            total_leads = len(selected_leads)
            hot_leads = len([lead for lead in selected_leads if lead['score'] >= 80])
            warm_leads = len([lead for lead in selected_leads if 60 <= lead['score'] < 80])
            cold_leads = len([lead for lead in selected_leads if lead['score'] < 60])
            
            # Generate campaign ID
            campaign_id = f"{campaign_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if send_option == "Send Now":
                # Send emails immediately
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    results = []
                    sent_count = 0
                    total_to_send = len(selected_leads)
                    
                    sub_b = subject_b if enable_ab_test else None
                    
                    for result in email_sender.send_bulk_emails_generator(
                        recipients=selected_leads,
                        subject=subject_line,
                        body=email_content,
                        campaign_id=campaign_id,
                        delay_seconds=delay_between_emails,
                        subject_b=sub_b
                    ):
                        results.append(result)
                        sent_count += 1
                        progress = sent_count / total_to_send
                        progress_bar.progress(progress)
                        variant_info = f" [Variant {result['ab_variant']}]" if enable_ab_test else ""
                        status_text.text(f"📧 Sending email {sent_count}/{total_to_send}{variant_info} to {result['recipient_email']}...")
                        
                        # Update SaaS Usage Tracking in real-time if successful
                        if result['status'] == 'sent':
                            st.session_state.email_count += 1
                            if 'db_handler' in st.session_state:
                                st.session_state.db_handler.update_settings(st.session_state.username, {'email_count': st.session_state.email_count})
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Campaign execution finished!")
                    
                    # Calculate results
                    successful = len([r for r in results if r['status'] == 'sent'])
                    failed = len([r for r in results if r['status'] == 'failed'])
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>✅ Campaign Finished!</h4>
                        <p><strong>Campaign:</strong> {campaign_name}</p>
                        <p><strong>Status:</strong> {successful} Sent, {failed} Failed</p>
                        <p><strong>Lead Breakdown:</strong> {hot_leads} Hot, {warm_leads} Warm, {cold_leads} Cold</p>
                        <p><strong>Campaign ID:</strong> {campaign_id}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if failed > 0:
                        st.warning(f"⚠️ {failed} emails failed to send. Check the Email Tracking page for details.")
                        
                except Exception as e:
                    st.error(f"❌ Error sending campaign: {str(e)}")
                    progress_bar.progress(0)
                    status_text.text("❌ Campaign failed")
            
            else:
                # Schedule emails for later
                try:
                    campaign_id = email_scheduler.schedule_campaign(
                        campaign_name=campaign_name,
                        recipients=selected_leads,
                        subject=subject_line,
                        body=email_content,
                        send_time=send_datetime,
                        delay_seconds=delay_between_emails
                    )
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>⏰ Campaign Scheduled Successfully!</h4>
                        <p><strong>Campaign:</strong> {campaign_name}</p>
                        <p><strong>Type:</strong> {campaign_type}</p>
                        <p><strong>Target:</strong> {target_audience}</p>
                        <p><strong>Total Leads:</strong> {total_leads}</p>
                        <p><strong>Lead Breakdown:</strong> {hot_leads} Hot, {warm_leads} Warm, {cold_leads} Cold</p>
                        <p><strong>Scheduled For:</strong> {send_datetime.strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Campaign ID:</strong> {campaign_id}</p>
                        <p><strong>Status:</strong> Scheduled - Emails will be sent automatically</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show countdown
                    time_until_send = send_datetime - datetime.now()
                    if time_until_send.total_seconds() > 0:
                        hours = int(time_until_send.total_seconds() // 3600)
                        minutes = int((time_until_send.total_seconds() % 3600) // 60)
                        st.info(f"⏰ Emails will be sent in {hours} hours and {minutes} minutes")
                    
                except Exception as e:
                    st.error(f"❌ Error scheduling campaign: {str(e)}")
            
            # Show email preview for first lead
            if selected_leads:
                sample_lead = selected_leads[0]
                preview_subject = subject_line.format(
                    name=sample_lead['name'],
                    company=sample_lead['company'],
                    title=sample_lead['title']
                )
                preview_body = email_content.format(
                    name=sample_lead['name'],
                    company=sample_lead['company'],
                    title=sample_lead['title']
                )
                
                st.subheader("📧 Email Preview (First Lead)")
                st.write(f"**To:** {sample_lead['email']}")
                st.write(f"**Subject:** {preview_subject}")
                st.write(f"**Body:**")
                st.text_area("Email Content", value=preview_body, height=150, disabled=True, label_visibility="collapsed")
            
            # Link to tracking page
            st.subheader("📊 Track Your Campaign")
            st.info("Go to the **Email Tracking** page to monitor delivery, opens, clicks, and replies in real-time!")
            
        else:
            missing_fields = []
            if not campaign_name:
                missing_fields.append("Campaign Name")
            if not subject_line:
                missing_fields.append("Subject Line")
            if not email_content:
                missing_fields.append("Email Content")
            if not selected_leads:
                missing_fields.append("Target Leads")
            
            st.warning(f"Please fill in: {', '.join(missing_fields)}")
    
    # Real Campaign Performance
    st.subheader("📈 Real Campaign Performance")
    
    if all_emails:
        # Get unique campaign IDs
        campaign_ids = set([email.get('campaign_id') for email in all_emails if email.get('campaign_id')])
        
        if campaign_ids:
            # Campaign performance table
            campaign_data = []
            for campaign_id in campaign_ids:
                stats = email_sender.get_campaign_stats(campaign_id)
                campaign_data.append({
                    'Campaign ID': campaign_id,
                    'Total Sent': stats['total_sent'],
                    'Delivered': stats['delivered'],
                    'Opened': stats['opened'],
                    'Clicked': stats['clicked'],
                    'Replied': stats['replied'],
                    'Delivery Rate': f"{stats['delivery_rate']:.1f}%",
                    'Open Rate': f"{stats['open_rate']:.1f}%",
                    'Click Rate': f"{stats['click_rate']:.1f}%",
                    'Reply Rate': f"{stats['reply_rate']:.1f}%"
                })
            
            campaigns_df = pd.DataFrame(campaign_data)
            st.dataframe(campaigns_df, use_container_width=True)
            
            # Performance chart
            if len(campaign_data) > 1:
                fig = px.bar(
                    campaigns_df,
                    x='Campaign ID',
                    y=['Delivery Rate', 'Open Rate', 'Click Rate', 'Reply Rate'],
                    title="Campaign Performance Comparison",
                    barmode='group'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No campaign data available yet. Send your first campaign to see performance metrics here!")
    else:
        st.info("No emails sent yet. Create and send your first campaign to see performance data!")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Email Tracking", type="primary"):
            st.info("Go to the **Email Tracking** page to see detailed email status and analytics!")
    
    with col2:
        if st.button("🔄 Refresh Data", type="primary", key="refresh_campaigns"):
            st.rerun()
    
    with col3:
        if st.button("📧 Send Test Email", type="primary"):
            st.info("Use the campaign form above to send real emails to your leads!")

if __name__ == "__main__":
    show_email_campaigns()