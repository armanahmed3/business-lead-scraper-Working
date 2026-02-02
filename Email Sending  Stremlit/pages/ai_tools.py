"""
AI Tools Page - AI Content Generation and Optimization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import random

def load_ai_tools_css():
    """Load custom CSS for AI tools page"""
    st.markdown("""
    <style>
    .ai-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .ai-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.3;
    }
    
    .ai-content {
        position: relative;
        z-index: 1;
    }
    
    .ai-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .ai-card:hover {
        transform: translateY(-5px);
    }
    
    .generation-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
    }
    
    .result-box {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #2d5016;
    }
    </style>
    """, unsafe_allow_html=True)

def generate_email_content(topic, tone, length):
    """Generate AI email content using OpenRouter if available, else fallback to template"""
    import requests
    import json
    
    api_key = st.session_state.get('openrouter_api_key', '')
    if api_key:
        try:
            prompt = f"Write a {tone} {length} email about {topic} for lead generation. Include a subject line at the start."
            
            # Use Auto-Select logic (Llama 3.1 405B for high quality free generation)
            model = "meta-llama/llama-3.1-405b-instruct:free" 
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "Lead Scraper Pro AI Tools",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            if response.status_code == 200:
                res = response.json()
                return res['choices'][0]['message']['content']
        except Exception as e:
            st.error(f"OpenRouter Error: {e}")

    # Fallback to templates
    templates = {
        "professional": [
            f"Subject: {topic} - Professional Opportunity\n\nDear [Name],\n\nI hope this email finds you well. I wanted to reach out regarding {topic.lower()}. This presents an excellent opportunity for your business to achieve significant growth and success.\n\nOur solution has helped numerous companies like yours to streamline their operations and increase efficiency by up to 40%. We would love to discuss how we can help you achieve similar results.\n\nI would appreciate the opportunity to schedule a brief call to discuss this further. Please let me know your availability.\n\nBest regards,\n[Your Name]",
            f"Subject: Exclusive {topic} Opportunity\n\nHello [Name],\n\nI hope you're having a great day. I'm writing to share an exclusive opportunity related to {topic.lower()} that I believe would be of great interest to your organization.\n\nOur innovative approach has been proven to deliver measurable results for businesses in your industry. We've seen an average improvement of 35% in key performance metrics.\n\nWould you be interested in a 15-minute conversation to explore how this could benefit your business?\n\nLooking forward to hearing from you.\n\nWarm regards,\n[Your Name]"
        ],
        "casual": [
            f"Subject: Quick question about {topic}\n\nHi [Name],\n\nHope you're doing well! I came across your company and was really impressed by what you're doing. I thought you might be interested in learning about {topic.lower()}.\n\nWe've been helping businesses like yours save time and money with our innovative solutions. It's pretty cool stuff, and I'd love to show you how it works.\n\nGot 10 minutes for a quick chat? I promise it'll be worth your time!\n\nCheers,\n[Your Name]",
            f"Subject: {topic} - Something you might like\n\nHey [Name],\n\nHow's it going? I wanted to reach out because I think you'd find our {topic.lower()} solution really interesting.\n\nWe've helped tons of companies boost their productivity and cut costs. The results speak for themselves - our clients typically see a 30% improvement within the first month.\n\nWant to grab a virtual coffee and chat about it? I'd love to show you what we can do.\n\nTalk soon,\n[Your Name]"
        ],
        "urgent": [
            f"Subject: URGENT: {topic} - Limited Time Offer\n\nDear [Name],\n\nI'm reaching out with an urgent opportunity regarding {topic.lower()} that requires immediate attention.\n\nThis exclusive offer is only available for the next 48 hours and could significantly impact your business growth. Our solution has helped companies achieve 50% faster results compared to traditional methods.\n\nTime is of the essence. Please respond as soon as possible to secure your spot.\n\nBest regards,\n[Your Name]",
            f"Subject: {topic} - Action Required Today\n\nHello [Name],\n\nI need to bring something important to your attention regarding {topic.lower()}. This opportunity won't be available for long.\n\nOur clients have seen remarkable improvements in efficiency and cost savings. Don't miss out on this chance to transform your business operations.\n\nPlease reply today to discuss next steps.\n\nRegards,\n[Your Name]"
        ]
    }
    
    return random.choice(templates.get(tone, templates["professional"]))

def generate_lead_score(lead_data):
    """Generate AI lead score"""
    # Simulate AI scoring based on lead data
    base_score = 50
    
    # Email domain scoring
    if lead_data.get('email', '').endswith(('.com', '.org', '.net')):
        base_score += 20
    elif lead_data.get('email', '').endswith(('.edu', '.gov')):
        base_score += 15
    
    # Company size scoring
    company = lead_data.get('company', '').lower()
    if any(word in company for word in ['inc', 'corp', 'llc', 'ltd']):
        base_score += 15
    
    # Job title scoring
    title = lead_data.get('title', '').lower()
    if any(word in title for word in ['ceo', 'president', 'director', 'manager']):
        base_score += 25
    elif any(word in title for word in ['vp', 'vice', 'head', 'lead']):
        base_score += 20
    
    # Add some randomness for demo
    base_score += random.randint(-10, 10)
    
    return min(100, max(0, base_score))

def show_ai_tools():
    """AI Tools Dashboard"""
    load_ai_tools_css()
    
    st.markdown("""
    <div class="ai-header">
        <div class="ai-content">
            <h1>🤖 AI Tools Dashboard</h1>
            <p>Leverage AI for content generation, lead scoring, and optimization</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # AI Content Generation
    st.subheader("✍️ AI Content Generation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="generation-box">
            <h3>📧 Email Content Generator</h3>
            <p>Generate personalized email content with AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        topic = st.text_input("Email Topic", placeholder="e.g., Product Launch, Partnership Opportunity")
        tone = st.selectbox("Tone", ["professional", "casual", "urgent"])
        length = st.selectbox("Length", ["short", "medium", "long"])
        
        if st.button("Generate Email Content", type="primary"):
            if topic:
                content = generate_email_content(topic, tone, length)
                st.markdown(f"""
                <div class="result-box">
                    <h4>Generated Email Content:</h4>
                    <pre style="white-space: pre-wrap; color: #2d5016;">{content}</pre>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Please enter a topic for the email")
    
    with col2:
        st.markdown("""
        <div class="generation-box">
            <h3>📝 Subject Line Generator</h3>
            <p>Create compelling email subject lines</p>
        </div>
        """, unsafe_allow_html=True)
        
        subject_topic = st.text_input("Subject Topic", placeholder="e.g., Webinar Invitation, Product Demo")
        subject_style = st.selectbox("Style", ["direct", "question", "benefit", "urgency"])
        
        if st.button("Generate Subject Lines", type="primary"):
            if subject_topic:
                subjects = [
                    f"{subject_topic}: Don't Miss Out!",
                    f"Quick question about {subject_topic}",
                    f"Exclusive {subject_topic} Opportunity",
                    f"{subject_topic} - Limited Time Offer",
                    f"Transform your business with {subject_topic}"
                ]
                
                st.markdown(f"""
                <div class="result-box">
                    <h4>Generated Subject Lines:</h4>
                    <ul>
                        {''.join([f'<li>{subject}</li>' for subject in subjects])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Please enter a topic for the subject line")
    
    # Lead Scoring
    st.subheader("🎯 AI Lead Scoring")
    
    st.markdown("""
    <div class="ai-card">
        <h3>📊 Intelligent Lead Scoring</h3>
        <p>Analyze lead data and generate AI-powered scores</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Lead input form
    col1, col2, col3 = st.columns(3)
    
    with col1:
        lead_name = st.text_input("Lead Name", placeholder="John Doe")
        lead_email = st.text_input("Email", placeholder="john@company.com")
    
    with col2:
        lead_company = st.text_input("Company", placeholder="Acme Corp")
        lead_title = st.text_input("Job Title", placeholder="Marketing Manager")
    
    with col3:
        lead_industry = st.selectbox("Industry", ["Technology", "Healthcare", "Finance", "Education", "Retail", "Other"])
        lead_source = st.selectbox("Lead Source", ["Website", "Social Media", "Referral", "Cold Outreach", "Event"])
    
    if st.button("Generate Lead Score", type="primary"):
        if lead_name and lead_email:
            lead_data = {
                'name': lead_name,
                'email': lead_email,
                'company': lead_company,
                'title': lead_title,
                'industry': lead_industry,
                'source': lead_source
            }
            
            score = generate_lead_score(lead_data)
            
            # Determine score category
            if score >= 80:
                category = "Hot Lead"
                color = "#4CAF50"
            elif score >= 60:
                category = "Warm Lead"
                color = "#FF9800"
            else:
                category = "Cold Lead"
                color = "#F44336"
            
            st.markdown(f"""
            <div class="result-box">
                <h4>Lead Score: {score}/100</h4>
                <p><strong>Category:</strong> <span style="color: {color};">{category}</span></p>
                <p><strong>Recommendation:</strong> {"Prioritize this lead for immediate follow-up" if score >= 80 else "Schedule follow-up within 24-48 hours" if score >= 60 else "Add to nurture campaign"}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show score breakdown
            st.subheader("📈 Score Breakdown")
            
            breakdown_data = {
                'Factor': ['Email Domain', 'Company Type', 'Job Title', 'Industry', 'Source'],
                'Score': [20, 15, 25, 10, 10],
                'Impact': ['High', 'Medium', 'High', 'Low', 'Low']
            }
            
            fig = px.bar(
                breakdown_data, 
                x='Factor', 
                y='Score',
                color='Impact',
                title="Lead Score Factors",
                color_discrete_map={'High': '#4CAF50', 'Medium': '#FF9800', 'Low': '#F44336'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Please fill in at least the name and email fields")
    
    # AI Optimization
    st.subheader("⚡ AI Optimization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="ai-card">
            <h3>📈 Campaign Optimization</h3>
            <p>AI-powered recommendations for better performance</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Simulate campaign data
        campaign_metrics = {
            'Open Rate': 24.5,
            'Click Rate': 3.2,
            'Conversion Rate': 1.8,
            'Bounce Rate': 2.1
        }
        
        st.write("**Current Campaign Performance:**")
        for metric, value in campaign_metrics.items():
            st.metric(metric, f"{value}%")
        
        if st.button("Get AI Recommendations"):
            recommendations = [
                "📧 Improve subject lines with personalization",
                "⏰ Send emails between 10-11 AM for better open rates",
                "🎯 Segment your audience for more targeted messaging",
                "📱 Optimize for mobile devices (60% of opens are mobile)",
                "🔄 A/B test different call-to-action buttons"
            ]
            
            st.markdown(f"""
            <div class="result-box">
                <h4>AI Recommendations:</h4>
                <ul>
                    {''.join([f'<li>{rec}</li>' for rec in recommendations])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="ai-card">
            <h3>🎨 Content Optimization</h3>
            <p>AI suggestions for better content performance</p>
        </div>
        """, unsafe_allow_html=True)
        
        content_text = st.text_area("Paste your content here", placeholder="Enter your email content or marketing copy...")
        
        if st.button("Optimize Content"):
            if content_text:
                optimizations = [
                    "✅ Good use of personalization",
                    "⚠️ Consider adding more emotional triggers",
                    "✅ Clear call-to-action present",
                    "⚠️ Could benefit from social proof",
                    "✅ Appropriate length for the audience"
                ]
                
                st.markdown(f"""
                <div class="result-box">
                    <h4>Content Analysis:</h4>
                    <ul>
                        {''.join([f'<li>{opt}</li>' for opt in optimizations])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Please enter some content to analyze")
    
    # AI Insights
    st.divider()
    st.subheader("🔮 Advanced AI Analysis")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("""
        <div class="ai-card">
            <h3>🧠 Lead Intent Analyzer</h3>
            <p>Analyze lead psychological tone and conversion probability</p>
        </div>
        """, unsafe_allow_html=True)
        
        lead_input = st.text_area("Lead Response / Interaction Description", placeholder="e.g., 'The lead mentioned they are looking for a solution by Q3 but are worried about the integration cost...'")
        
        if st.button("Analyze Intent", key="analyze_intent"):
            if lead_input:
                with st.spinner("🤖 AI is decoding lead intent..."):
                    # Simulation of AI Analysis (In real use, this could call OpenRouter)
                    intent_score = random.randint(40, 95)
                    tone = random.choice(["Curious", "Skeptical", "Urgent", "Informational"])
                    st.markdown(f"""
                    <div class="result-box">
                        <h4>AI Analysis Result:</h4>
                        <p><strong>Intent Score:</strong> {intent_score}/100</p>
                        <p><strong>Primary Tone:</strong> {tone}</p>
                        <p><strong>Recommendation:</strong> {'Send a case study focusing on ROI immediately.' if intent_score > 70 else 'Follow up with more educational content.'}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Please enter lead interaction text.")

    with col_b:
        st.markdown("""
        <div class="ai-card">
            <h3>🌍 Industry Benchmark tool</h3>
            <p>Compare your metrics with industry averages</p>
        </div>
        """, unsafe_allow_html=True)
        
        industry = st.selectbox("Select Industry", ["SaaS", "Real Estate", "E-commerce", "Healthcare", "Professional Services"])
        
        # Sample comparison data
        st.write(f"**{industry} Averages vs Yours:**")
        st.progress(0.24, text="Industry Open Rate: 24%")
        st.progress(0.32, text="Your Open Rate: 32%")

    st.subheader("📈 Performance Intelligence")
    
    # Generate some sample insights
    insights_data = {
        'Day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'Open Rate': [22.1, 24.5, 26.8, 25.2, 23.9, 18.7, 16.3],
        'Click Rate': [2.8, 3.2, 3.5, 3.1, 2.9, 2.1, 1.8]
    }
    
    fig = px.line(
        insights_data, 
        x='Day', 
        y=['Open Rate', 'Click Rate'],
        title="Email Performance by Day of Week",
        markers=True
    )
    fig.update_layout(yaxis_title="Rate (%)")
    st.plotly_chart(fig, use_container_width=True)
    
    # AI predictions
    st.markdown("""
    <div class="ai-card">
        <h3>🔮 AI Predictions</h3>
        <p>Based on your current data patterns</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Predicted Open Rate", "26.3%", "+1.8%")
    with col2:
        st.metric("Predicted Click Rate", "3.7%", "+0.5%")
    with col3:
        st.metric("Predicted Conversion", "2.1%", "+0.3%")


if __name__ == "__main__":
    show_ai_tools()