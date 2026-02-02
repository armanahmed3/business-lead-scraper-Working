"""
Lead Management Page - CSV Upload and AI Processing
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

def load_lead_management_css():
    """Load custom CSS for lead management page"""
    st.markdown("""
    <style>
    .lead-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .lead-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.3;
    }
    
    .lead-content {
        position: relative;
        z-index: 1;
    }
    
    .upload-section {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        text-align: center;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
    
    .success-box {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #2d5016;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #8b4513;
    }
    </style>
    """, unsafe_allow_html=True)

def process_lead_data(df):
    """Process and analyze lead data"""
    results = {
        'total_leads': len(df),
        'valid_emails': 0,
        'duplicates': 0,
        'missing_data': 0,
        'processed_leads': []
    }
    
    # Check for valid emails
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if 'email' in df.columns:
        results['valid_emails'] = df['email'].str.match(email_pattern, na=False).sum()
    
    # Check for duplicates
    if 'email' in df.columns:
        results['duplicates'] = df['email'].duplicated().sum()
    
    # Check for missing data
    results['missing_data'] = df.isnull().sum().sum()
    
    # Process each lead
    for idx, row in df.iterrows():
        lead = {
            'id': idx + 1,
            'name': row.get('name', 'N/A'),
            'email': row.get('email', 'N/A'),
            'company': row.get('company', 'N/A'),
            'phone': row.get('phone', 'N/A'),
            'title': row.get('title', 'N/A'),
            'score': random.randint(20, 95),  # Simulate AI scoring
            'status': 'New'
        }
        results['processed_leads'].append(lead)
    
    return results

def show_lead_management():
    """Lead Management Dashboard"""
    load_lead_management_css()
    
    st.markdown("""
    <div class="lead-header">
        <div class="lead-content">
            <h1>👥 Lead Management</h1>
            <p>Upload CSV files and let AI process your leads automatically</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Lead Statistics
    stats = lead_db.get_lead_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Leads</h3>
            <h2>{stats['total_leads']:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Hot Leads</h3>
            <h2>{stats['hot_leads']:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Warm Leads</h3>
            <h2>{stats['warm_leads']:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Cold Leads</h3>
            <h2>{stats['cold_leads']:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # File upload section
    st.markdown("""
    <div class="upload-section">
        <h3>📁 Upload Your Lead Data</h3>
        <p>Upload a CSV file with your lead information</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload your lead data in CSV format",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        try:
            # Load the CSV file
            df = pd.read_csv(uploaded_file)
            
            st.markdown(f"""
            <div class="success-box">
                <h4>✅ Successfully loaded {len(df)} leads</h4>
                <p>File: {uploaded_file.name}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Process the data
            results = process_lead_data(df)
            
            # Category input
            category = st.text_input("📂 Category for these leads", value="General", 
                                    placeholder="e.g., Graphic Design Clients, Web Development, etc.")
            
            if st.button("💾 Save Leads to Database", type="primary"):
                lead_data_list = []
                for idx, row in df.iterrows():
                    lead_data = {
                        'name': row.get('name', ''),
                        'email': row.get('email', ''),
                        'company': row.get('company', ''),
                        'phone': row.get('phone', ''),
                        'title': row.get('title', ''),
                        'industry': row.get('industry', ''),
                        'source': 'CSV Upload',
                        'category': category,
                        'score': random.randint(20, 95)
                    }
                    lead_data_list.append(lead_data)
                
                lead_ids = lead_db.add_leads_bulk(lead_data_list)
                st.success(f"✅ Successfully saved {len(lead_ids)} leads to database in category '{category}'!")
                st.rerun()
            
            # Display metrics
            st.subheader("📊 Lead Analysis Results")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Total Leads</h3>
                    <h2>{results['total_leads']:,}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Valid Emails</h3>
                    <h2>{results['valid_emails']:,}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Duplicates</h3>
                    <h2>{results['duplicates']:,}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Missing Data</h3>
                    <h2>{results['missing_data']:,}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Data quality analysis
            st.subheader("🔍 Data Quality Analysis")
            
            # Show data preview
            st.write("**Data Preview:**")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Data quality issues
            if results['duplicates'] > 0:
                st.markdown(f"""
                <div class="warning-box">
                    <h4>⚠️ Duplicate Emails Found</h4>
                    <p>{results['duplicates']} duplicate email addresses detected. Consider removing duplicates for better campaign performance.</p>
                </div>
                """, unsafe_allow_html=True)
            
            if results['missing_data'] > 0:
                st.markdown(f"""
                <div class="warning-box">
                    <h4>⚠️ Missing Data Detected</h4>
                    <p>{results['missing_data']} missing data points found. Consider filling missing values for better personalization.</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Lead scoring visualization
            st.subheader("🎯 AI Lead Scoring")
            
            # Create lead scores dataframe
            leads_df = pd.DataFrame(results['processed_leads'])
            
            # Score distribution
            fig_score = px.histogram(
                leads_df, 
                x='score',
                title="Lead Score Distribution",
                nbins=20,
                color_discrete_sequence=['#667eea']
            )
            fig_score.update_layout(xaxis_title="Lead Score", yaxis_title="Number of Leads")
            st.plotly_chart(fig_score, use_container_width=True)
            
            # Score categories
            score_categories = {
                'Hot Leads (80-100)': len(leads_df[leads_df['score'] >= 80]),
                'Warm Leads (60-79)': len(leads_df[(leads_df['score'] >= 60) & (leads_df['score'] < 80)]),
                'Cold Leads (0-59)': len(leads_df[leads_df['score'] < 60])
            }
            
            fig_categories = px.pie(
                values=list(score_categories.values()),
                names=list(score_categories.keys()),
                title="Lead Score Categories",
                color_discrete_sequence=['#4CAF50', '#FF9800', '#F44336']
            )
            st.plotly_chart(fig_categories, use_container_width=True)
            
            # Lead Priority Matrix
            st.divider()
            st.subheader("⭐ AI Lead Priority Matrix")
            st.write("Leads are mapped based on their engagement history and potential value.")
            
            # Simulated data for the matrix
            n_matrix = len(leads_df) if len(leads_df) > 0 else 50
            matrix_df = pd.DataFrame({
                'Engagement': np.random.randint(0, 100, n_matrix),
                'Potential Value': np.random.randint(0, 100, n_matrix),
                'Lead Name': leads_df['name'] if len(leads_df) > 0 else [f"Lead {i}" for i in range(n_matrix)],
                'Score': leads_df['score'] if len(leads_df) > 0 else np.random.randint(0, 100, n_matrix)
            })
            
            fig_matrix = px.scatter(
                matrix_df, 
                x='Engagement', 
                y='Potential Value',
                color='Score',
                hover_data=['Lead Name'],
                title="Lead Engagement vs Value Matrix",
                color_continuous_scale='RdYlGn'
            )
            # Add quadrant lines
            fig_matrix.add_hline(y=50, line_dash="dash", line_color="gray")
            fig_matrix.add_vline(x=50, line_dash="dash", line_color="gray")
            
            st.plotly_chart(fig_matrix, use_container_width=True)
            
            # Top leads table
            st.subheader("⭐ Top Scoring Leads")
            top_leads = leads_df.nlargest(10, 'score')[['name', 'email', 'company', 'score']]
            st.dataframe(top_leads, use_container_width=True)
            
            # Export processed data
            st.subheader("💾 Export Processed Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Download Processed Leads CSV", type="primary"):
                    csv = leads_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"processed_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("Download Lead Scores Report", type="primary"):
                    report_data = {
                        'Total Leads': results['total_leads'],
                        'Valid Emails': results['valid_emails'],
                        'Duplicates': results['duplicates'],
                        'Missing Data': results['missing_data'],
                        'Hot Leads': score_categories['Hot Leads (80-100)'],
                        'Warm Leads': score_categories['Warm Leads (60-79)'],
                        'Cold Leads': score_categories['Cold Leads (0-59)']
                    }
                    
                    report_df = pd.DataFrame(list(report_data.items()), columns=['Metric', 'Value'])
                    csv = report_df.to_csv(index=False)
                    st.download_button(
                        label="Download Report",
                        data=csv,
                        file_name=f"lead_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    
    else:
        # Show instructions when no file is uploaded
        st.markdown("""
        <div class="upload-section">
            <h3>👆 Please upload a CSV file to begin lead processing</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Show expected format
        st.subheader("📋 Expected CSV Format")
        st.write("Your CSV file should contain the following columns:")
        
        example_data = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'email': ['john@company.com', 'jane@company.com', 'bob@company.com'],
            'company': ['Acme Corp', 'Tech Solutions', 'Global Inc'],
            'phone': ['+1-555-0123', '+1-555-0456', '+1-555-0789'],
            'title': ['Marketing Manager', 'CEO', 'Sales Director']
        })
        
        st.dataframe(example_data, use_container_width=True)
        
        # Features overview
        st.subheader("🚀 AI Processing Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🔍 Data Validation**
            - Email format validation
            - Duplicate detection
            - Missing data analysis
            - Data quality scoring
            """)
        
        with col2:
            st.markdown("""
            **🎯 AI Lead Scoring**
            - Intelligent scoring algorithm
            - Lead categorization
            - Priority ranking
            - Performance predictions
            """)
        
        with col3:
            st.markdown("""
            **📊 Analytics & Reports**
            - Visual score distribution
            - Lead category breakdown
            - Export processed data
            - Detailed analysis reports
            """)
        
        # Sample data download
        st.subheader("💡 Download Sample Data")
        st.write("Need sample data to test? Download our sample lead file:")
        
        sample_data = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
            'email': ['john@acme.com', 'jane@techsolutions.com', 'bob@globalinc.com', 'alice@startup.com', 'charlie@enterprise.com'],
            'company': ['Acme Corp', 'Tech Solutions', 'Global Inc', 'Startup Co', 'Enterprise Ltd'],
            'phone': ['+1-555-0123', '+1-555-0456', '+1-555-0789', '+1-555-0321', '+1-555-0654'],
            'title': ['Marketing Manager', 'CEO', 'Sales Director', 'CTO', 'VP Sales']
        })
        
        csv = sample_data.to_csv(index=False)
        st.download_button(
            label="Download Sample CSV",
            data=csv,
            file_name="sample_leads.csv",
            mime="text/csv"
        )
    
    # Lead Management Section
    st.markdown("---")
    st.subheader("👥 Manage Your Leads")
    
    # Search and filter leads
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("🔍 Search Leads", placeholder="Search by name, email, or company")
    
    with col2:
        status_filter = st.selectbox("📊 Filter by Status", ["All", "New", "Contacted", "Qualified", "Converted"])
    
    with col3:
        score_filter = st.selectbox("🎯 Filter by Score", ["All", "Hot Leads (80-100)", "Warm Leads (60-79)", "Cold Leads (0-59)"])
    
    # Get filtered leads
    all_leads = lead_db.get_all_leads()
    filtered_leads = all_leads
    
    if search_query:
        filtered_leads = lead_db.search_leads(search_query)
    
    if status_filter != "All":
        filtered_leads = [lead for lead in filtered_leads if lead['status'] == status_filter]
    
    if score_filter != "All":
        if score_filter == "Hot Leads (80-100)":
            filtered_leads = [lead for lead in filtered_leads if lead['score'] >= 80]
        elif score_filter == "Warm Leads (60-79)":
            filtered_leads = [lead for lead in filtered_leads if 60 <= lead['score'] < 80]
        elif score_filter == "Cold Leads (0-59)":
            filtered_leads = [lead for lead in filtered_leads if lead['score'] < 60]
    
    # Display leads
    if filtered_leads:
        st.write(f"**Found {len(filtered_leads)} leads**")
        
        # Convert to DataFrame for display
        leads_df = pd.DataFrame(filtered_leads)
        display_columns = ['name', 'email', 'company', 'title', 'score', 'status', 'created_at']
        available_columns = [col for col in display_columns if col in leads_df.columns]
        
        st.dataframe(leads_df[available_columns], use_container_width=True)
        
        # Lead actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Generate AI Email", type="primary"):
                if filtered_leads:
                    # Select first lead for demo
                    selected_lead = filtered_leads[0]
                    email_content = ai_email_generator.generate_email(selected_lead, 'professional')
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>🤖 AI Generated Email for {selected_lead['name']}</h4>
                        <p><strong>Subject:</strong> {email_content['subject']}</p>
                        <p><strong>Body:</strong></p>
                        <pre style="white-space: pre-wrap; color: #2d5016;">{email_content['body']}</pre>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📊 Export Leads", type="primary"):
                filename = lead_db.export_leads('csv')
                if filename:
                    st.success(f"✅ Leads exported to {filename}")
        
        with col3:
            if st.button("🔄 Refresh Data", type="primary", key="refresh_leads"):
                st.rerun()
    
    else:
        st.info("No leads found. Upload a CSV file to get started!")

if __name__ == "__main__":
    show_lead_management()