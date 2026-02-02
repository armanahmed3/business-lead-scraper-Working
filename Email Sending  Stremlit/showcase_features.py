"""
LeadAI Pro - Feature Showcase
Demonstrates all platform capabilities with interactive examples
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import json

def showcase_lead_management():
    """Showcase lead management features"""
    st.markdown("## 👥 Lead Management Showcase")
    
    # Sample lead data
    np.random.seed(42)
    n_leads = 100
    
    leads_data = {
        'Name': [f"Lead {i+1}" for i in range(n_leads)],
        'Email': [f"lead{i+1}@example.com" for i in range(n_leads)],
        'Company': [f"Company {i+1}" for i in range(n_leads)],
        'Industry': np.random.choice(['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing'], n_leads),
        'AI Score': np.random.uniform(0.1, 0.9, n_leads),
        'Quality': ['High' if x > 0.7 else 'Medium' if x > 0.4 else 'Low' for x in np.random.uniform(0.1, 0.9, n_leads)],
        'Status': np.random.choice(['New', 'Contacted', 'Qualified', 'Converted'], n_leads)
    }
    
    leads_df = pd.DataFrame(leads_data)
    
    st.markdown("### 📊 Lead Analytics Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", len(leads_df))
    with col2:
        high_quality = len(leads_df[leads_df['Quality'] == 'High'])
        st.metric("High Quality", high_quality)
    with col3:
        avg_score = leads_df['AI Score'].mean()
        st.metric("Avg AI Score", f"{avg_score:.2f}")
    with col4:
        converted = len(leads_df[leads_df['Status'] == 'Converted'])
        st.metric("Converted", converted)
    
    # Lead Quality Distribution
    st.markdown("### 🎯 Lead Quality Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        quality_counts = leads_df['Quality'].value_counts()
        fig = px.pie(
            values=quality_counts.values,
            names=quality_counts.index,
            color_discrete_map={
                'High': '#4CAF50',
                'Medium': '#FF9800',
                'Low': '#F44336'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        industry_counts = leads_df['Industry'].value_counts()
        fig = px.bar(
            x=industry_counts.index,
            y=industry_counts.values,
            color=industry_counts.values,
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Lead Table
    st.markdown("### 📋 Lead List")
    st.dataframe(leads_df.head(20), use_container_width=True)

def showcase_email_campaigns():
    """Showcase email campaign features"""
    st.markdown("## 📧 Email Campaigns Showcase")
    
    # Sample campaign data
    campaigns_data = {
        'Campaign': [f"Campaign {i+1}" for i in range(10)],
        'Subject': [f"Exciting update {i+1}!" for i in range(10)],
        'Recipients': np.random.randint(100, 1000, 10),
        'Opened': np.random.randint(50, 800, 10),
        'Clicked': np.random.randint(10, 200, 10),
        'Open Rate': np.random.uniform(0.15, 0.45, 10),
        'Click Rate': np.random.uniform(0.02, 0.15, 10)
    }
    
    campaigns_df = pd.DataFrame(campaigns_data)
    campaigns_df['Open Rate'] = (campaigns_df['Open Rate'] * 100).round(2)
    campaigns_df['Click Rate'] = (campaigns_df['Click Rate'] * 100).round(2)
    
    st.markdown("### 📊 Campaign Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_recipients = campaigns_df['Recipients'].sum()
        st.metric("Total Recipients", f"{total_recipients:,}")
    with col2:
        total_opens = campaigns_df['Opened'].sum()
        st.metric("Total Opens", f"{total_opens:,}")
    with col3:
        avg_open_rate = campaigns_df['Open Rate'].mean()
        st.metric("Avg Open Rate", f"{avg_open_rate:.1f}%")
    with col4:
        avg_click_rate = campaigns_df['Click Rate'].mean()
        st.metric("Avg Click Rate", f"{avg_click_rate:.1f}%")
    
    # Campaign Performance Chart
    st.markdown("### 📈 Campaign Performance Comparison")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Open Rate',
        x=campaigns_df['Campaign'],
        y=campaigns_df['Open Rate'],
        marker_color='#667eea'
    ))
    
    fig.add_trace(go.Bar(
        name='Click Rate',
        x=campaigns_df['Campaign'],
        y=campaigns_df['Click Rate'],
        marker_color='#764ba2'
    ))
    
    fig.update_layout(
        title="Campaign Performance Metrics",
        xaxis_title="Campaign",
        yaxis_title="Rate (%)",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Campaign Table
    st.markdown("### 📋 Campaign Details")
    st.dataframe(campaigns_df, use_container_width=True)

def showcase_ai_features():
    """Showcase AI features"""
    st.markdown("## 🤖 AI Features Showcase")
    
    # AI Lead Scoring
    st.markdown("### 🎯 AI Lead Scoring")
    
    # Generate sample scoring data
    np.random.seed(42)
    n_leads = 50
    
    scoring_data = {
        'Lead': [f"Lead {i+1}" for i in range(n_leads)],
        'AI Score': np.random.beta(2, 5, n_leads),
        'Industry': np.random.choice(['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing'], n_leads),
        'Company Size': np.random.choice(['Startup', 'Small', 'Medium', 'Large', 'Enterprise'], n_leads),
        'Job Title': np.random.choice(['CEO', 'CTO', 'Manager', 'Director', 'VP'], n_leads)
    }
    
    scoring_df = pd.DataFrame(scoring_data)
    scoring_df['Quality'] = ['High' if x > 0.7 else 'Medium' if x > 0.4 else 'Low' for x in scoring_df['AI Score']]
    
    # AI Score Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.histogram(
            scoring_df,
            x='AI Score',
            nbins=20,
            title="AI Score Distribution",
            color_discrete_sequence=['#667eea']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        quality_counts = scoring_df['Quality'].value_counts()
        fig = px.pie(
            values=quality_counts.values,
            names=quality_counts.index,
            color_discrete_map={
                'High': '#4CAF50',
                'Medium': '#FF9800',
                'Low': '#F44336'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # AI Content Generation
    st.markdown("### ✍️ AI Content Generation")
    
    st.markdown("#### 📧 AI-Generated Email Subject Lines")
    
    ai_subjects = [
        "Exclusive offer for {name} - Limited time!",
        "Don't miss this {industry} opportunity",
        "Quick question about your {company} goals",
        "Special discount for {name} at {company}",
        "Last chance: {industry} solution you need"
    ]
    
    for i, subject in enumerate(ai_subjects, 1):
        st.markdown(f"**Option {i}:** {subject}")
    
    st.markdown("#### 📝 AI-Generated Email Content")
    
    ai_content = """
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 10px 0;">
        <h3>🤖 AI-Generated Email Template</h3>
        <h4>Subject: Exclusive offer for {name} - Limited time!</h4>
        <hr>
        <p><strong>Hi {name}!</strong></p>
        <p>I hope this email finds you well. I wanted to reach out regarding an exciting opportunity for {company}.</p>
        <p>We've been helping {industry} businesses like yours achieve remarkable growth, and I believe we can do the same for you.</p>
        <div style="background: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 5px;">
            <h4>🎯 What We Offer</h4>
            <ul>
                <li>Proven solutions for {industry} challenges</li>
                <li>Expert guidance tailored to your needs</li>
                <li>Measurable results and ROI</li>
            </ul>
        </div>
        <p>Would you be interested in a brief 15-minute call to discuss how we can help {company} achieve its goals?</p>
        <p>Best regards,<br>The Team</p>
    </div>
    """
    
    st.markdown(ai_content, unsafe_allow_html=True)

def showcase_analytics():
    """Showcase analytics features"""
    st.markdown("## 📊 Analytics Showcase")
    
    # Generate time series data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    n_days = len(dates)
    
    # Simulate realistic trends
    base_leads = 50
    leads_trend = base_leads + np.cumsum(np.random.normal(0, 2, n_days)) + np.sin(np.arange(n_days) * 2 * np.pi / 30) * 10
    
    base_revenue = 5000
    revenue_trend = base_revenue + np.cumsum(np.random.normal(0, 200, n_days)) + np.sin(np.arange(n_days) * 2 * np.pi / 30) * 1000
    
    # Performance Trends
    st.markdown("### 📈 Performance Trends")
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Daily Leads', 'Daily Revenue'),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=leads_trend,
            mode='lines',
            name='Leads',
            line=dict(color='#667eea', width=3)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=revenue_trend,
            mode='lines',
            name='Revenue',
            line=dict(color='#764ba2', width=3)
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        title="Performance Trends Over Time"
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Leads", row=1, col=1)
    fig.update_yaxes(title_text="Revenue ($)", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 3D Analytics
    st.markdown("### 🎯 3D Analytics Visualization")
    
    # Generate 3D data
    x = np.random.randn(100)
    y = np.random.randn(100)
    z = np.random.randn(100)
    
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode='markers',
        marker=dict(
            size=5,
            color=z,
            colorscale='Viridis',
            opacity=0.8
        )
    )])
    
    fig_3d.update_layout(
        title="3D Lead Distribution",
        scene=dict(
            xaxis_title='Lead Score',
            yaxis_title='Engagement',
            zaxis_title='Conversion Probability'
        ),
        height=500
    )
    
    st.plotly_chart(fig_3d, use_container_width=True)

def main():
    """Main showcase function"""
    st.set_page_config(
        page_title="LeadAI Pro - Feature Showcase",
        page_icon="🚀",
        layout="wide"
    )
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 1rem; margin: 1rem 0; color: white;">
        <h1>🚀 LeadAI Pro - Feature Showcase</h1>
        <p>Experience the power of AI-driven lead management and email marketing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Lead Management", "📧 Email Campaigns", "🤖 AI Features", "📊 Analytics"])
    
    with tab1:
        showcase_lead_management()
    
    with tab2:
        showcase_email_campaigns()
    
    with tab3:
        showcase_ai_features()
    
    with tab4:
        showcase_analytics()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; margin-top: 2rem; background: var(--surface-dark); border-radius: 1rem;">
        <h3>🎉 Ready to Get Started?</h3>
        <p>Launch LeadAI Pro and transform your lead management with AI-powered automation!</p>
        <p><strong>Run:</strong> <code>python run.py</code></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
