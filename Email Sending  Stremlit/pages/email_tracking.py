"""
Email Tracking Dashboard - Real-time email status and analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from email_sender import email_sender

def load_tracking_css():
    """Load custom CSS for email tracking page"""
    st.markdown("""
    <style>
    .tracking-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .tracking-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.3;
    }
    
    .tracking-content {
        position: relative;
        z-index: 1;
    }
    
    .status-card {
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .status-card:hover {
        transform: translateY(-5px);
    }
    
    .status-sent {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    .status-delivered {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        color: white;
    }
    
    .status-opened {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
    }
    
    .status-clicked {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: #2d5016;
    }
    
    .status-replied {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        color: #8b4513;
    }
    
    .status-failed {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        color: #8b4513;
    }
    
    .status-bounced {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
    }
    
    .email-table {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .filter-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def show_email_tracking():
    """Email Tracking Dashboard"""
    load_tracking_css()
    
    st.markdown("""
    <div class="tracking-header">
        <div class="tracking-content">
            <h1>📧 Email Tracking Dashboard</h1>
            <p>Real-time email delivery, open, and engagement tracking</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all email logs
    all_emails = email_sender.get_all_emails()
    
    if not all_emails:
        st.info("No emails sent yet. Create and send campaigns to see tracking data here.")
        return
    
    # Overall Statistics
    st.subheader("📊 Overall Email Statistics")
    
    # Calculate overall stats
    total_emails = len(all_emails)
    sent_emails = len([e for e in all_emails if e['status'] in ['sent', 'opened', 'clicked', 'replied']])
    opened_emails = len([e for e in all_emails if e['status'] in ['opened', 'clicked', 'replied']])
    clicked_emails = len([e for e in all_emails if e['status'] in ['clicked', 'replied']])
    replied_emails = len([e for e in all_emails if e['status'] == 'replied'])
    failed_emails = len([e for e in all_emails if e['status'] == 'failed'])
    bounced_emails = len([e for e in all_emails if e['status'] == 'bounced'])
    
    # Live Activity Feed
    st.subheader("⚡ Live Activity Feed")
    recent_logs = sorted(all_emails, key=lambda x: x.get('updated_at', ''), reverse=True)[:10]
    
    if recent_logs:
        for log in recent_logs:
            status = log.get('status', 'unknown')
            icon = "📧"
            color = "#4facfe"
            if status == 'opened': 
                icon = "👁️"
                color = "#fa709a"
            elif status == 'clicked': 
                icon = "🔗"
                color = "#a8edea"
            elif status == 'sent': 
                icon = "🚀"
                color = "#4facfe"
                
            time_str = log.get('updated_at', 'unknown').replace('T', ' ').split('.')[0]
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 10px 15px; border-radius: 10px; border-left: 4px solid {color}; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.2rem; margin-right: 15px;">{icon}</span>
                    <div>
                        <div style="font-size: 0.9rem; font-weight: bold;">{log.get('recipient_name', 'Lead')} ({log.get('recipient_email')})</div>
                        <div style="font-size: 0.75rem; opacity: 0.7;">{log.get('subject', 'No Subject')}</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.8rem; font-weight: bold; color: {color}; text-transform: uppercase;">{status}</div>
                    <div style="font-size: 0.7rem; opacity: 0.6;">{time_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent activity detected.")

    st.divider()
    
    # Overview Statistics
    st.subheader("📊 Performance Overview")
    
    # Status cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="status-card status-sent">
            <h3>Total Sent</h3>
            <h2>{total_emails:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="status-card status-delivered">
            <h3>Delivered</h3>
            <h2>{sent_emails:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="status-card status-opened">
            <h3>Opened</h3>
            <h2>{opened_emails:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="status-card status-clicked">
            <h3>Clicked</h3>
            <h2>{clicked_emails:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Additional metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Replies", replied_emails)
    with col2:
        st.metric("Failed", failed_emails)
    with col3:
        st.metric("Bounced", bounced_emails)
    
    # Performance rates
    st.subheader("📈 Performance Rates")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delivery_rate = (sent_emails / total_emails * 100) if total_emails > 0 else 0
        st.metric("Delivery Rate", f"{delivery_rate:.1f}%")
    
    with col2:
        open_rate = (opened_emails / sent_emails * 100) if sent_emails > 0 else 0
        st.metric("Open Rate", f"{open_rate:.1f}%")
    
    with col3:
        click_rate = (clicked_emails / opened_emails * 100) if opened_emails > 0 else 0
        st.metric("Click Rate", f"{click_rate:.1f}%")
    
    with col4:
        reply_rate = (replied_emails / sent_emails * 100) if sent_emails > 0 else 0
        st.metric("Reply Rate", f"{reply_rate:.1f}%")
    
    # Filters
    st.markdown("""
    <div class="filter-section">
        <h3>🔍 Filter & Search Emails</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", 
                                   ["All", "Sent", "Delivered", "Opened", "Clicked", "Replied", "Failed", "Bounced"])
    
    with col2:
        search_email = st.text_input("Search by Email", placeholder="Enter email address")
    
    with col3:
        date_filter = st.date_input("Filter by Date", value=datetime.now().date())
    
    # Filter emails
    filtered_emails = all_emails
    
    if status_filter != "All":
        filtered_emails = [e for e in filtered_emails if e['status'] == status_filter.lower()]
    
    if search_email:
        filtered_emails = [e for e in filtered_emails if search_email.lower() in e['recipient_email'].lower()]
    
    # Convert to DataFrame for display
    if filtered_emails:
        df = pd.DataFrame(filtered_emails)
        
        # Select columns to display
        display_columns = ['recipient_name', 'recipient_email', 'subject', 'status', 'sent_at', 'opened_at', 'clicked_at', 'replied_at']
        available_columns = [col for col in display_columns if col in df.columns]
        
        # Format the dataframe
        display_df = df[available_columns].copy()
        
        # Format timestamps
        for col in ['sent_at', 'opened_at', 'clicked_at', 'replied_at']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: x[:19] if x else 'Not tracked')
        
        # Rename columns for better display
        display_df.columns = ['Name', 'Email', 'Subject', 'Status', 'Sent At', 'Opened At', 'Clicked At', 'Replied At']
        
        st.subheader(f"📋 Email Details ({len(filtered_emails)} emails)")
        st.dataframe(display_df, use_container_width=True)
        
        # Email actions
        st.subheader("⚡ Email Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Data", type="primary", key="refresh_tracking"):
                st.rerun()
        
        with col2:
            if st.button("📊 Export Data", type="primary"):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"email_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("🗑️ Clear All Data", type="primary"):
                if st.button("⚠️ Confirm Delete", type="secondary"):
                    email_sender.email_logs = []
                    email_sender.save_email_logs()
                    st.success("All email data cleared!")
                    st.rerun()
    
    else:
        st.info("No emails found matching your filters.")
    
    # Status distribution chart
    st.subheader("📊 Status Distribution")
    
    status_counts = {}
    for email in all_emails:
        status = email['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    if status_counts:
        fig = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title="Email Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Timeline chart
    st.subheader("📈 Email Timeline")
    
    # Group emails by date
    daily_counts = {}
    for email in all_emails:
        if email.get('sent_at'):
            date = email['sent_at'][:10]  # Get date part
            daily_counts[date] = daily_counts.get(date, 0) + 1
    
    if daily_counts:
        dates = sorted(daily_counts.keys())
        counts = [daily_counts[date] for date in dates]
        
        fig = px.line(
            x=dates,
            y=counts,
            title="Emails Sent Over Time",
            labels={'x': 'Date', 'y': 'Number of Emails'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Campaign performance (if campaign IDs exist)
    st.subheader("🎯 Campaign Performance")
    
    campaign_ids = set([email.get('campaign_id') for email in all_emails if email.get('campaign_id')])
    
    if campaign_ids:
        campaign_stats = []
        for campaign_id in campaign_ids:
            stats = email_sender.get_campaign_stats(campaign_id)
            stats['campaign_id'] = campaign_id
            campaign_stats.append(stats)
        
        if campaign_stats:
            campaign_df = pd.DataFrame(campaign_stats)
            
            # Display campaign metrics
            st.dataframe(campaign_df, use_container_width=True)
            
            # Campaign performance chart
            fig = px.bar(
                campaign_df,
                x='campaign_id',
                y=['delivery_rate', 'open_rate', 'click_rate', 'reply_rate'],
                title="Campaign Performance Rates",
                barmode='group'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No campaign data available. Campaigns will be tracked when you send emails through the Email Campaigns page.")

if __name__ == "__main__":
    show_email_tracking()
