"""
Real Email Sending System with Tracking
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
import time
import threading
from dotenv import load_dotenv

load_dotenv()

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SMTP_USERNAME', '')
        self.sender_password = os.getenv('SMTP_PASSWORD', '')
        self.sender_name = os.getenv('SENDER_NAME', 'LeadAI Pro')
        
        # Email tracking database
        self.tracking_file = "email_tracking.json"
        self.email_logs = self.load_email_logs()
    
    def load_email_logs(self) -> List[Dict]:
        """Load email tracking logs"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_email_logs(self):
        """Save email tracking logs"""
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(self.email_logs, f, indent=2, ensure_ascii=False)
    
    def send_email(self, recipient_email: str, recipient_name: str, subject: str, 
                   body: str, campaign_id: str = None) -> Dict[str, Any]:
        """Send a single email with tracking"""
        
        email_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create email log entry
        email_log = {
            'id': email_id,
            'campaign_id': campaign_id,
            'recipient_email': recipient_email,
            'recipient_name': recipient_name,
            'subject': subject,
            'body': body,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'status': 'pending',
            'sent_at': None,
            'delivered_at': None,
            'opened_at': None,
            'clicked_at': None,
            'replied_at': None,
            'bounced_at': None,
            'error_message': None,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            
            # Add tracking pixel (for open tracking)
            # IMPORTANT: Streamlit handles query params at the root URL
            tracking_pixel = f'<img src="http://localhost:8501/?track=open&email_id={email_id}" width="1" height="1" style="display:none; visibility:hidden;">'
            
            # Add click tracking to links
            body_with_tracking = body.replace('href="', f'href="http://localhost:8501/?track=click&email_id={email_id}&url=')
            
            # Create HTML version with tracking
            html_body = f"""
            <html>
            <body>
                {body_with_tracking.replace(chr(10), '<br>')}
                {tracking_pixel}
            </body>
            </html>
            """
            
            # Create text version
            text_part = MIMEText(body, "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            # Update status
            email_log['status'] = 'sent'
            email_log['sent_at'] = datetime.now().isoformat()
            email_log['updated_at'] = datetime.now().isoformat()
            
        except Exception as e:
            # Update status with error
            email_log['status'] = 'failed'
            email_log['error_message'] = str(e)
            email_log['updated_at'] = datetime.now().isoformat()
        
        # Save to logs
        self.email_logs.append(email_log)
        self.save_email_logs()
        
        return email_log
    
    def send_bulk_emails_generator(self, recipients: List[Dict], subject: str, body: str, 
                                 campaign_id: str = None, delay_seconds: int = 20, 
                                 subject_b: str = None):
        """Generator that sends bulk emails and yields results one by one (Supports A/B testing)"""
        for i, recipient in enumerate(recipients):
            try:
                # Select subject (Alternate A/B if subject_b is provided)
                current_subject = subject
                variant = "A"
                if subject_b and i % 2 != 0:
                    current_subject = subject_b
                    variant = "B"
                
                # Personalize email content
                personalized_subject = current_subject.format(
                    name=recipient.get('name', ''),
                    company=recipient.get('company', ''),
                    title=recipient.get('title', '')
                )
                
                personalized_body = body.format(
                    name=recipient.get('name', ''),
                    company=recipient.get('company', ''),
                    title=recipient.get('title', '')
                )
                
                # Send email
                result = self.send_email(
                    recipient_email=recipient.get('email', ''),
                    recipient_name=recipient.get('name', ''),
                    subject=personalized_subject,
                    body=personalized_body,
                    campaign_id=campaign_id
                )
                
                # Tag result with variant
                result['ab_variant'] = variant
                
                yield result
                
                # Add randomized delay between emails (except for last email)
                if i < len(recipients) - 1:
                    import random
                    # Enhanced Anti-Spam: Add more variance
                    actual_delay = delay_seconds + random.randint(-5, 10) if delay_seconds > 10 else delay_seconds + random.randint(-2, 3)
                    time.sleep(max(1, actual_delay))
                    
            except Exception as e:
                # Log error for this recipient
                error_log = {
                    'id': str(uuid.uuid4()),
                    'campaign_id': campaign_id,
                    'recipient_email': recipient.get('email', ''),
                    'recipient_name': recipient.get('name', ''),
                    'subject': subject,
                    'body': body,
                    'status': 'failed',
                    'error_message': str(e),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                self.email_logs.append(error_log)
                yield error_log

    def send_bulk_emails(self, recipients: List[Dict], subject: str, body: str, 
                        campaign_id: str = None, delay_seconds: int = 20) -> List[Dict]:
        """Send bulk emails and return results as a list (legacy compatibility)"""
        results = []
        for result in self.send_bulk_emails_generator(recipients, subject, body, campaign_id, delay_seconds):
            results.append(result)
        
        self.save_email_logs()
        return results
    
    def get_email_status(self, email_id: str) -> Optional[Dict]:
        """Get status of a specific email"""
        for log in self.email_logs:
            if log['id'] == email_id:
                return log
        return None
    
    def update_email_status(self, email_id: str, status: str, additional_data: Dict = None):
        """Update email status (for tracking)"""
        for log in self.email_logs:
            if log['id'] == email_id:
                log['status'] = status
                log['updated_at'] = datetime.now().isoformat()
                
                if additional_data:
                    log.update(additional_data)
                
                self.save_email_logs()
                break
    
    def track_email_open(self, email_id: str):
        """Track email open"""
        self.update_email_status(email_id, 'opened', {
            'opened_at': datetime.now().isoformat()
        })
    
    def track_email_click(self, email_id: str, url: str):
        """Track email click"""
        self.update_email_status(email_id, 'clicked', {
            'clicked_at': datetime.now().isoformat(),
            'clicked_url': url
        })
    
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get statistics for a campaign"""
        campaign_emails = [log for log in self.email_logs if log.get('campaign_id') == campaign_id]
        
        if not campaign_emails:
            return {
                'total_sent': 0,
                'delivered': 0,
                'opened': 0,
                'clicked': 0,
                'replied': 0,
                'bounced': 0,
                'failed': 0,
                'delivery_rate': 0,
                'open_rate': 0,
                'click_rate': 0,
                'reply_rate': 0
            }
        
        total_sent = len(campaign_emails)
        delivered = len([e for e in campaign_emails if e['status'] in ['sent', 'opened', 'clicked', 'replied']])
        opened = len([e for e in campaign_emails if e['status'] in ['opened', 'clicked', 'replied']])
        clicked = len([e for e in campaign_emails if e['status'] in ['clicked', 'replied']])
        replied = len([e for e in campaign_emails if e['status'] == 'replied'])
        bounced = len([e for e in campaign_emails if e['status'] == 'bounced'])
        failed = len([e for e in campaign_emails if e['status'] == 'failed'])
        
        return {
            'total_sent': total_sent,
            'delivered': delivered,
            'opened': opened,
            'clicked': clicked,
            'replied': replied,
            'bounced': bounced,
            'failed': failed,
            'delivery_rate': (delivered / total_sent * 100) if total_sent > 0 else 0,
            'open_rate': (opened / delivered * 100) if delivered > 0 else 0,
            'click_rate': (clicked / opened * 100) if opened > 0 else 0,
            'reply_rate': (replied / delivered * 100) if delivered > 0 else 0
        }
    
    def get_all_emails(self) -> List[Dict]:
        """Get all email logs"""
        return self.email_logs
    
    def get_emails_by_status(self, status: str) -> List[Dict]:
        """Get emails by status"""
        return [log for log in self.email_logs if log['status'] == status]
    
    def delete_email_log(self, email_id: str) -> bool:
        """Delete an email log"""
        for i, log in enumerate(self.email_logs):
            if log['id'] == email_id:
                del self.email_logs[i]
                self.save_email_logs()
                return True
        return False

# Global email sender instance
email_sender = EmailSender()
