"""
LeadAI Pro - Demo Data Generator
Generates sample data for demonstrating all platform features
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random

def generate_sample_leads(n_leads=1000):
    """Generate sample lead data for demonstration"""
    np.random.seed(42)
    
    # Sample data
    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Jessica', 
                   'William', 'Ashley', 'James', 'Amanda', 'Christopher', 'Jennifer', 'Daniel']
    
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson']
    
    companies = ['TechCorp', 'DataSoft', 'CloudSystems', 'AI Solutions', 'Digital Dynamics',
                 'InnovateLab', 'FutureTech', 'SmartData', 'CyberCore', 'QuantumLeap']
    
    industries = ['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing', 'Education', 'Consulting']
    
    job_titles = ['CEO', 'CTO', 'VP Marketing', 'Director', 'Manager', 'Senior Developer', 
                  'Data Scientist', 'Product Manager', 'Sales Director', 'Marketing Manager']
    
    sources = ['Website', 'Social Media', 'Referral', 'Cold Outreach', 'Event', 'Paid Ads', 'Email Campaign']
    
    # Generate leads
    leads = []
    for i in range(n_leads):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        company = random.choice(companies)
        industry = random.choice(industries)
        
        # Generate realistic email
        email_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', f'{company.lower()}.com']
        email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(email_domains)}"
        
        # Generate phone number
        phone = f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
        
        # Generate AI score based on realistic factors
        ai_score = np.random.beta(2, 5)  # Beta distribution for scores 0-1
        
        # Adjust score based on factors
        if industry in ['Technology', 'Finance']:
            ai_score += 0.1
        if 'CEO' in job_titles or 'CTO' in job_titles:
            ai_score += 0.15
        if '@' + company.lower() + '.com' in email:
            ai_score += 0.1
        
        ai_score = min(ai_score, 1.0)
        
        lead = {
            'id': i + 1,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'company': company,
            'phone': phone,
            'job_title': random.choice(job_titles),
            'industry': industry,
            'source': random.choice(sources),
            'ai_score': round(ai_score, 3),
            'lead_quality': 'High' if ai_score > 0.7 else 'Medium' if ai_score > 0.4 else 'Low',
            'status': random.choice(['New', 'Contacted', 'Qualified', 'Converted']),
            'created_date': datetime.now() - timedelta(days=random.randint(0, 365)),
            'notes': f'Lead from {random.choice(sources)} - {industry} industry'
        }
        leads.append(lead)
    
    return pd.DataFrame(leads)

def generate_sample_campaigns(n_campaigns=20):
    """Generate sample email campaign data"""
    np.random.seed(42)
    
    campaign_types = ['Newsletter', 'Promotional', 'Follow-up', 'Welcome', 'Nurturing']
    statuses = ['Draft', 'Scheduled', 'Sending', 'Sent', 'Paused']
    
    campaigns = []
    for i in range(n_campaigns):
        campaign_type = random.choice(campaign_types)
        status = random.choice(statuses)
        
        # Generate realistic metrics
        total_recipients = random.randint(50, 2000)
        open_rate = np.random.uniform(0.15, 0.45)
        click_rate = open_rate * np.random.uniform(0.2, 0.4)
        bounce_rate = np.random.uniform(0.02, 0.08)
        unsubscribe_rate = np.random.uniform(0.01, 0.05)
        
        opened_count = int(total_recipients * open_rate)
        clicked_count = int(total_recipients * click_rate)
        bounced_count = int(total_recipients * bounce_rate)
        unsubscribed_count = int(total_recipients * unsubscribe_rate)
        
        campaign = {
            'id': i + 1,
            'name': f'{campaign_type} Campaign {i + 1}',
            'subject': f'Exciting {campaign_type.lower()} update for you!',
            'template_type': campaign_type.lower(),
            'status': status,
            'total_recipients': total_recipients,
            'opened_count': opened_count,
            'clicked_count': clicked_count,
            'bounced_count': bounced_count,
            'unsubscribed_count': unsubscribed_count,
            'open_rate': round(open_rate * 100, 2),
            'click_rate': round(click_rate * 100, 2),
            'bounce_rate': round(bounce_rate * 100, 2),
            'unsubscribe_rate': round(unsubscribe_rate * 100, 2),
            'created_date': datetime.now() - timedelta(days=random.randint(0, 90)),
            'sent_date': datetime.now() - timedelta(days=random.randint(0, 30)) if status == 'Sent' else None
        }
        campaigns.append(campaign)
    
    return pd.DataFrame(campaigns)

def generate_sample_emails(n_emails=5000):
    """Generate sample email data for analytics"""
    np.random.seed(42)
    
    emails = []
    for i in range(n_emails):
        # Generate realistic email metrics
        is_opened = np.random.choice([0, 1], p=[0.3, 0.7])
        is_clicked = np.random.choice([0, 1], p=[0.85, 0.15]) if is_opened else 0
        is_bounced = np.random.choice([0, 1], p=[0.95, 0.05])
        is_unsubscribed = np.random.choice([0, 1], p=[0.98, 0.02])
        
        sent_date = datetime.now() - timedelta(hours=random.randint(0, 720))
        opened_date = sent_date + timedelta(hours=random.randint(1, 48)) if is_opened else None
        clicked_date = opened_date + timedelta(hours=random.randint(1, 24)) if is_clicked else None
        
        email = {
            'id': i + 1,
            'campaign_id': random.randint(1, 20),
            'lead_id': random.randint(1, 1000),
            'recipient_email': f'lead{random.randint(1, 1000)}@example.com',
            'subject': f'Campaign {random.randint(1, 20)} - Update',
            'sent_at': sent_date,
            'opened_at': opened_date,
            'clicked_at': clicked_date,
            'is_opened': bool(is_opened),
            'is_clicked': bool(is_clicked),
            'is_bounced': bool(is_bounced),
            'is_unsubscribed': bool(is_unsubscribed),
            'clicked_link': f'https://example.com/cta{random.randint(1, 5)}' if is_clicked else None
        }
        emails.append(email)
    
    return pd.DataFrame(emails)

def generate_sample_analytics():
    """Generate sample analytics data"""
    np.random.seed(42)
    
    # Daily performance data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    daily_data = []
    
    for date in dates:
        # Generate realistic daily metrics
        leads_added = random.randint(5, 50)
        emails_sent = random.randint(20, 200)
        emails_opened = int(emails_sent * np.random.uniform(0.15, 0.45))
        emails_clicked = int(emails_opened * np.random.uniform(0.2, 0.4))
        revenue = random.randint(1000, 10000)
        
        daily_data.append({
            'date': date,
            'leads_added': leads_added,
            'emails_sent': emails_sent,
            'emails_opened': emails_opened,
            'emails_clicked': emails_clicked,
            'revenue': revenue,
            'open_rate': round(emails_opened / emails_sent * 100, 2) if emails_sent > 0 else 0,
            'click_rate': round(emails_clicked / emails_sent * 100, 2) if emails_sent > 0 else 0
        })
    
    return pd.DataFrame(daily_data)

def create_demo_files():
    """Create demo CSV files for testing"""
    print("🎯 Creating demo data files...")
    
    # Generate sample data
    leads_df = generate_sample_leads(1000)
    campaigns_df = generate_sample_campaigns(20)
    emails_df = generate_sample_emails(5000)
    analytics_df = generate_sample_analytics()
    
    # Save to CSV files
    leads_df.to_csv('demo_leads.csv', index=False)
    campaigns_df.to_csv('demo_campaigns.csv', index=False)
    emails_df.to_csv('demo_emails.csv', index=False)
    analytics_df.to_csv('demo_analytics.csv', index=False)
    
    print("✅ Demo files created:")
    print("   - demo_leads.csv (1000 leads)")
    print("   - demo_campaigns.csv (20 campaigns)")
    print("   - demo_emails.csv (5000 email records)")
    print("   - demo_analytics.csv (365 days of analytics)")
    
    # Create sample email templates
    templates = {
        'newsletter': {
            'subject': 'Weekly Update from {company}',
            'content': '''
            <h2>Hello {name}!</h2>
            <p>Thank you for your interest in {company}.</p>
            <p>Here's what's new this week:</p>
            <ul>
                <li>New features and updates</li>
                <li>Industry insights and trends</li>
                <li>Upcoming events and webinars</li>
            </ul>
            <p>Best regards,<br>The {company} Team</p>
            '''
        },
        'promotional': {
            'subject': 'Special Offer for {name} - Limited Time!',
            'content': '''
            <h2>Hi {name}!</h2>
            <p>We have an exclusive offer for you at {company}!</p>
            <div style="background-color: #f0f0f0; padding: 20px; margin: 20px 0; text-align: center; border-radius: 8px;">
                <h3>🎉 Special Discount</h3>
                <p>Get 20% off your first order!</p>
                <a href="#" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Claim Offer</a>
            </div>
            <p>Don't miss out on this limited-time deal.</p>
            <p>Best regards,<br>The {company} Team</p>
            '''
        },
        'follow_up': {
            'subject': 'Following up on our conversation',
            'content': '''
            <h2>Hi {name}!</h2>
            <p>I wanted to follow up on our recent conversation about {company}.</p>
            <p>Do you have any questions I can help with?</p>
            <p>I'd love to schedule a brief call to discuss how we can help your business grow.</p>
            <p>Best regards,<br>The {company} Team</p>
            '''
        }
    }
    
    with open('demo_templates.json', 'w') as f:
        json.dump(templates, f, indent=2)
    
    print("   - demo_templates.json (email templates)")
    
    return True

def main():
    """Main function to generate all demo data"""
    print("🚀 LeadAI Pro - Demo Data Generator")
    print("=" * 50)
    
    try:
        create_demo_files()
        print("\n🎉 Demo data generation completed successfully!")
        print("\n📁 You can now use these files to test the platform:")
        print("   - Upload demo_leads.csv to test lead management")
        print("   - Use demo_campaigns.csv for campaign analytics")
        print("   - View demo_analytics.csv for performance trends")
        print("   - Import demo_templates.json for email templates")
        
    except Exception as e:
        print(f"❌ Error generating demo data: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
