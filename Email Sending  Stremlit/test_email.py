"""
Test Email Function - Send test emails for tracking
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_email_tracking():
    """Send a test email to verify tracking works"""
    
    st.title("📧 Test Email Tracking")
    
    # Get email credentials
    st.subheader("📧 Email Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_email = st.text_input("Your Email Address", placeholder="your-email@gmail.com")
        sender_name = st.text_input("Your Name", placeholder="Your Name")
    
    with col2:
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587)
    
    smtp_username = st.text_input("SMTP Username", placeholder="your-email@gmail.com")
    smtp_password = st.text_input("SMTP Password", type="password", placeholder="your-app-password")
    
    if st.button("📧 Send Test Email", type="primary"):
        if not all([test_email, smtp_username, smtp_password, sender_name]):
            st.error("Please fill in all required fields")
            return
        
        try:
            from email_sender import email_sender
            
            # Set credentials
            email_sender.smtp_server = smtp_server
            email_sender.smtp_port = smtp_port
            email_sender.sender_email = smtp_username
            email_sender.sender_password = smtp_password
            email_sender.sender_name = sender_name
            
            # Create test lead
            test_lead = {
                'name': 'Test User',
                'email': test_email,
                'company': 'Test Company',
                'title': 'Test Title'
            }
            
            # Send test email
            result = email_sender.send_email(
                recipient_email=test_email,
                recipient_name='Test User',
                subject='Test Email - Tracking Verification',
                body=f"""Hello Test User,

This is a test email to verify that email tracking is working correctly.

The email contains:
- Open tracking pixel
- Click tracking for links

Click this link to test click tracking: https://www.google.com

Best regards,
{sender_name}""",
                campaign_id='test_campaign'
            )
            
            if result['status'] == 'sent':
                st.success("✅ Test email sent successfully!")
                st.info(f"📧 Email ID: {result['id']}")
                st.info("📊 Check the Email Tracking page to see if opens and clicks are recorded")
                
                # Show tracking URL
                st.subheader("🔗 Tracking URLs")
                st.code(f"Open tracking: http://localhost:8501/tracking?track=open&email_id={result['id']}")
                st.code(f"Click tracking: http://localhost:8501/tracking?track=click&email_id={result['id']}&url=https://www.google.com")
                
            else:
                st.error(f"❌ Failed to send email: {result.get('error_message', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Instructions
    st.subheader("📋 How to Test Email Tracking")
    
    st.markdown("""
    1. **Fill in your email credentials** above
    2. **Click "Send Test Email"** to send a test email to yourself
    3. **Check your email** and open it
    4. **Click any link** in the email
    5. **Go to Email Tracking page** to see if opens and clicks are recorded
    6. **Refresh the tracking page** to see updated data
    """)
    
    st.info("💡 **Tip**: Make sure to use an App Password for Gmail, not your regular password!")

if __name__ == "__main__":
    test_email_tracking()
