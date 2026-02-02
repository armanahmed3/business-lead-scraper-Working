"""
Email Tracking Handler - Handle email opens and clicks
"""

import streamlit as st
from email_sender import email_sender
import sys
import os

def handle_tracking():
    """Handle email tracking requests and return True if processed"""
    
    # Get query parameters safely
    try:
        query_params = st.query_params
    except:
        return False
    
    if not query_params:
        return False
        
    if 'track' in query_params:
        track_type = query_params['track']
        
        if track_type == 'open':
            # Handle email open tracking
            email_id = query_params.get('email_id')
            if email_id:
                email_sender.track_email_open(email_id)
                # Return a 1x1 transparent pixel in markdown
                st.markdown("""
                <div style="position: fixed; top: 0; left: 0; width: 1px; height: 1px; opacity: 0;">
                <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" 
                     width="1" height="1">
                </div>
                """, unsafe_allow_html=True)
                return True
        
        elif track_type == 'click':
            # Handle email click tracking
            email_id = query_params.get('email_id')
            url = query_params.get('url')
            if email_id and url:
                email_sender.track_email_click(email_id, url)
                # Redirect to the actual URL
                st.markdown(f"""
                <script>
                    window.location.href = "{url}";
                </script>
                <div style="text-align: center; padding: 20px;">
                    <h3>Redirecting you to your destination...</h3>
                    <p>If you are not redirected, <a href="{url}">click here</a>.</p>
                </div>
                """, unsafe_allow_html=True)
                return True
    
    return False
    
    # Default response
    st.write("Email tracking endpoint")

if __name__ == "__main__":
    handle_tracking()
