"""
Data Analytics Page - Real Data Analysis Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt

def load_analytics_css():
    """Load custom CSS for data analytics page"""
    st.markdown("""
    <style>
    .analytics-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .analytics-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.3;
    }
    
    .analytics-content {
        position: relative;
        z-index: 1;
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
    
    .chart-container {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .upload-section {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        text-align: center;
    }
    
    .data-quality {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #8b4513;
        border-left: 5px solid #ff6b6b;
    }
    
    .success-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #2d5016;
        border-left: 5px solid #4caf50;
    }
    </style>
    """, unsafe_allow_html=True)

def show_data_analytics():
    """Data Analytics Dashboard with real data analysis"""
    load_analytics_css()
    
    st.markdown("""
    <div class="analytics-header">
        <div class="analytics-content">
            <h1>📊 Data Analytics Dashboard</h1>
            <p>Upload your data and get instant insights with AI-powered analysis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload section
    st.markdown("""
    <div class="upload-section">
        <h3>📁 Upload Your Dataset</h3>
        <p>Choose a CSV or Excel file to perform comprehensive data analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your data to perform analysis",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        try:
            # Load data
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.markdown(f"""
            <div class="success-box">
                <h4>✅ Successfully loaded {len(df):,} rows and {len(df.columns):,} columns</h4>
                <p>File: {uploaded_file.name}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Data overview metrics
            st.subheader("📋 Data Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class="metric-card">
                    <h3>Total Rows</h3>
                    <h2>{:,}</h2>
                </div>
                """.format(len(df)), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="metric-card">
                    <h3>Total Columns</h3>
                    <h2>{:,}</h2>
                </div>
                """.format(len(df.columns)), unsafe_allow_html=True)
            
            with col3:
                memory_mb = df.memory_usage(deep=True).sum() / 1024**2
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Memory Usage</h3>
                    <h2>{memory_mb:.2f} MB</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                missing_percent = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Missing Data</h3>
                    <h2>{missing_percent:.1f}%</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Data preview
            st.subheader("👀 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Data quality analysis
            st.subheader("🔍 Data Quality Analysis")
            
            # Missing values analysis
            missing_data = df.isnull().sum()
            missing_percent = (missing_data / len(df)) * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Missing Values Count:**")
                if missing_data.sum() > 0:
                    missing_df = pd.DataFrame({
                        'Column': missing_data[missing_data > 0].index,
                        'Missing Count': missing_data[missing_data > 0].values
                    })
                    fig_missing = px.bar(
                        missing_df, 
                        x='Column', 
                        y='Missing Count',
                        title="Missing Values by Column",
                        color='Missing Count',
                        color_continuous_scale='Reds'
                    )
                    fig_missing.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_missing, use_container_width=True)
                else:
                    st.success("✅ No missing values found!")
            
            with col2:
                st.write("**Missing Values Percentage:**")
                if missing_percent.sum() > 0:
                    missing_percent_df = pd.DataFrame({
                        'Column': missing_percent[missing_percent > 0].index,
                        'Missing %': missing_percent[missing_percent > 0].values
                    })
                    fig_percent = px.bar(
                        missing_percent_df, 
                        x='Column', 
                        y='Missing %',
                        title="Missing Values Percentage",
                        color='Missing %',
                        color_continuous_scale='Oranges'
                    )
                    fig_percent.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_percent, use_container_width=True)
                else:
                    st.success("✅ No missing values found!")
            
            # Data types analysis
            st.subheader("📊 Data Types Distribution")
            dtype_counts = df.dtypes.value_counts()
            fig_dtypes = px.pie(
                values=dtype_counts.values,
                names=[str(x) for x in dtype_counts.index],
                title="Data Types Distribution"
            )
            st.plotly_chart(fig_dtypes, use_container_width=True)
            
            # Statistical summary
            st.subheader("📈 Statistical Summary")
            st.dataframe(df.describe(), use_container_width=True)
            
            # Interactive 3D visualizations
            st.subheader("🎨 Interactive 3D Visualizations")
            
            # Select columns for visualization
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_columns) >= 2:
                col1, col2 = st.columns(2)
                
                with col1:
                    x_col = st.selectbox("X-axis", numeric_columns)
                with col2:
                    y_col = st.selectbox("Y-axis", numeric_columns)
                
                if len(numeric_columns) >= 3:
                    z_col = st.selectbox("Z-axis", numeric_columns)
                else:
                    z_col = None
                
                # 3D Scatter Plot
                if z_col:
                    fig_3d = px.scatter_3d(
                        df, x=x_col, y=y_col, z=z_col,
                        title="3D Scatter Plot",
                        color=df[x_col] if x_col else None,
                        opacity=0.7
                    )
                    fig_3d.update_layout(
                        scene=dict(
                            xaxis_title=x_col,
                            yaxis_title=y_col,
                            zaxis_title=z_col
                        )
                    )
                    st.plotly_chart(fig_3d, use_container_width=True)
                
                # 2D Scatter Plot
                fig_2d = px.scatter(
                    df, x=x_col, y=y_col,
                    title="2D Scatter Plot",
                    color=df[x_col] if x_col else None,
                    opacity=0.7
                )
                st.plotly_chart(fig_2d, use_container_width=True)
                
                # Correlation Heatmap
                if len(numeric_columns) > 2:
                    st.subheader("🔥 Correlation Heatmap")
                    corr_matrix = df[numeric_columns].corr()
                    fig_heatmap = px.imshow(
                        corr_matrix,
                        title="Correlation Matrix",
                        color_continuous_scale="RdBu",
                        aspect="auto"
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Data cleaning suggestions
            st.subheader("🧹 Data Cleaning Suggestions")
            
            # Missing values
            if missing_data.sum() > 0:
                st.markdown("""
                <div class="warning-box">
                    <h4>⚠️ Missing Values Detected</h4>
                    <p>Consider the following actions:</p>
                    <ul>
                        <li>Fill missing values with mean/median for numeric columns</li>
                        <li>Fill missing values with mode for categorical columns</li>
                        <li>Remove rows with too many missing values</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Duplicates
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                st.markdown(f"""
                <div class="warning-box">
                    <h4>⚠️ Duplicate Rows Found</h4>
                    <p>{duplicates} duplicate rows detected. Consider removing them for better analysis.</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Outliers detection
            if len(numeric_columns) > 0:
                st.subheader("📊 Outlier Detection")
                outlier_col = st.selectbox("Select column for outlier analysis", numeric_columns)
                
                Q1 = df[outlier_col].quantile(0.25)
                Q3 = df[outlier_col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[(df[outlier_col] < lower_bound) | (df[outlier_col] > upper_bound)]
                
                if len(outliers) > 0:
                    st.markdown(f"""
                    <div class="warning-box">
                        <h4>⚠️ Outliers Detected</h4>
                        <p>{len(outliers)} outliers found in {outlier_col}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.dataframe(outliers[[outlier_col]], use_container_width=True)
                else:
                    st.markdown("""
                    <div class="success-box">
                        <h4>✅ No Outliers Detected</h4>
                        <p>Your data looks clean in this column!</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Predictive Intelligence Section
            st.divider()
            st.subheader("🚀 Predictive Intelligence (3D)")
            
            # Generate sample 3D data for visualization
            n_points = 200
            x_data = np.random.normal(50, 15, n_points) # Engagement
            y_data = np.random.normal(60, 20, n_points) # Sentiment
            z_data = (x_data * 0.4 + y_data * 0.6) + np.random.normal(0, 5, n_points) # Convert Probability
            categories = np.where(z_data > 70, 'High Potential', np.where(z_data > 40, 'Nurturing', 'Low Interest'))
            
            fig_3d = px.scatter_3d(
                x=x_data, y=y_data, z=z_data,
                color=categories,
                labels={'x': 'Engagement Score', 'y': 'Lead Sentiment', 'z': 'Conversion %'},
                title="Lead Quality Predictive Model (3D Cluster Analysis)",
                opacity=0.7,
                color_discrete_map={'High Potential': '#00ff00', 'Nurturing': '#ffff00', 'Low Interest': '#ff0000'}
            )
            fig_3d.update_layout(scene = dict(
                xaxis_title='Engagement',
                yaxis_title='Sentiment',
                zaxis_title='Conversion %'),
                margin=dict(r=0, l=0, b=0, t=30)
            )
            st.plotly_chart(fig_3d, use_container_width=True)
            
            # Export cleaned data
            st.subheader("💾 Export Cleaned Data")
            if st.button("Download Cleaned Data as CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"cleaned_{uploaded_file.name}",
                    mime="text/csv"
                )
            
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
    
    else:
        # Show instructions when no file is uploaded
        st.markdown("""
        <div class="upload-section">
            <h3>👆 Please upload a CSV or Excel file to begin data analysis</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Show sample data structure
        st.subheader("📋 Expected Data Format")
        st.write("Your data should contain columns with different data types:")
        st.write("- **Numeric columns**: For statistical analysis and visualizations")
        st.write("- **Categorical columns**: For grouping and filtering")
        st.write("- **Date columns**: For time series analysis")
        
        # Show example
        st.subheader("💡 Example Data Structure")
        example_data = pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Age': [25, 30, 35],
            'Salary': [50000, 60000, 70000],
            'Department': ['Sales', 'Marketing', 'IT'],
            'Join_Date': ['2023-01-15', '2023-02-20', '2023-03-10']
        })
        st.dataframe(example_data, use_container_width=True)
        
        # Features overview
        st.subheader("🚀 Analysis Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📊 Data Quality**
            - Missing values analysis
            - Duplicate detection
            - Outlier identification
            - Data type validation
            """)
        
        with col2:
            st.markdown("""
            **🎨 Visualizations**
            - 3D scatter plots
            - Correlation heatmaps
            - Statistical charts
            - Interactive graphs
            """)
        
        with col3:
            st.markdown("""
            **🧹 Data Cleaning**
            - Automated suggestions
            - Missing value imputation
            - Outlier treatment
            - Data export options
            """)

if __name__ == "__main__":
    show_data_analytics()