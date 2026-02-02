"""
Email Tracking Endpoint
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def show_tracking():
    """Handle email tracking requests"""
    
    # Get query parameters
    query_params = st.query_params
    
    if 'track' in query_params:
        track_type = query_params['track']
        
        if track_type == 'open':
            # Handle email open tracking
            email_id = query_params.get('email_id', '')
            if email_id:
                try:
                    from email_sender import email_sender
                    email_sender.track_email_open(email_id)
                    st.success(f"Email {email_id} opened and tracked!")
                except Exception as e:
                    st.error(f"Tracking error: {e}")
                
                # Return a 1x1 transparent pixel
                st.markdown("""
                <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" 
                     width="1" height="1" style="display:none;">
                """, unsafe_allow_html=True)
                return
        
        elif track_type == 'click':
            # Handle email click tracking
            email_id = query_params.get('email_id', '')
            url = query_params.get('url', '')
            if email_id and url:
                try:
                    from email_sender import email_sender
                    email_sender.track_email_click(email_id, url)
                    st.success(f"Click on {email_id} tracked! Redirecting to {url}")
                except Exception as e:
                    st.error(f"Tracking error: {e}")
                
                # Redirect to the actual URL
                st.markdown(f"""
                <script>
                    window.location.href = "{url}";
                </script>
                """, unsafe_allow_html=True)
                return
    
    # Default response
    st.title("📧 Email Tracking")
    st.info("This is the email tracking endpoint. Emails will automatically track opens and clicks here.")

if __name__ == "__main__":
    show_tracking()
