"""
Email service for campaign management and sending
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import Campaign, Lead, Email, EmailQueue
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    """Service for email campaign management and sending"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@leadai.com")
        self.from_name = os.getenv("FROM_NAME", "LeadAI Pro")
        
        # Email sending configuration
        self.send_delay = 20  # seconds between emails
        self.max_retries = 3
        self.batch_size = 10
    
    async def create_campaign(self, campaign_data: Dict[str, Any], user_id: int, db: Session) -> Campaign:
        """Create a new email campaign"""
        campaign = Campaign(
            user_id=user_id,
            name=campaign_data['name'],
            subject=campaign_data['subject'],
            content=campaign_data['content'],
            template_type=campaign_data.get('template_type', 'newsletter'),
            scheduled_at=campaign_data.get('scheduled_at')
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        return campaign
    
    async def queue_campaign(self, campaign: Campaign, db: Session) -> None:
        """Queue a campaign for sending"""
        # Get all leads for the user
        leads = db.query(Lead).filter(Lead.user_id == campaign.user_id).all()
        
        if not leads:
            logger.warning(f"No leads found for campaign {campaign.id}")
            return
        
        # Create email records and queue them
        for lead in leads:
            # Personalize content
            personalized_content = self._personalize_content(
                campaign.content, 
                lead
            )
            
            # Create email record
            email = Email(
                campaign_id=campaign.id,
                lead_id=lead.id,
                recipient_email=lead.email,
                subject=campaign.subject,
                content=campaign.content,
                personalized_content=personalized_content
            )
            
            db.add(email)
            db.flush()  # Get the email ID
            
            # Queue email for sending
            queue_item = EmailQueue(
                email_id=email.id,
                scheduled_at=datetime.utcnow() + timedelta(minutes=5),  # 5-minute delay
                priority=1
            )
            
            db.add(queue_item)
        
        # Update campaign status
        campaign.status = "scheduled"
        campaign.total_recipients = len(leads)
        
        db.commit()
        
        # Start background email sending task
        asyncio.create_task(self._process_email_queue(db))
    
    def _personalize_content(self, content: str, lead: Lead) -> str:
        """Personalize email content with lead data"""
        personalized = content
        
        # Replace placeholders
        placeholders = {
            '{name}': lead.first_name or 'there',
            '{first_name}': lead.first_name or '',
            '{last_name}': lead.last_name or '',
            '{company}': lead.company or 'your company',
            '{email}': lead.email,
            '{phone}': lead.phone or '',
            '{job_title}': lead.job_title or '',
            '{industry}': lead.industry or ''
        }
        
        for placeholder, value in placeholders.items():
            personalized = personalized.replace(placeholder, str(value))
        
        return personalized
    
    async def _process_email_queue(self, db: Session) -> None:
        """Process queued emails with throttling"""
        while True:
            try:
                # Get pending emails
                pending_emails = db.query(EmailQueue).filter(
                    EmailQueue.status == "pending",
                    EmailQueue.scheduled_at <= datetime.utcnow()
                ).order_by(EmailQueue.priority.desc(), EmailQueue.created_at.asc()).limit(self.batch_size).all()
                
                if not pending_emails:
                    await asyncio.sleep(30)  # Wait 30 seconds if no emails
                    continue
                
                # Process batch
                for queue_item in pending_emails:
                    try:
                        await self._send_email(queue_item, db)
                        await asyncio.sleep(self.send_delay)  # Throttle sending
                    except Exception as e:
                        logger.error(f"Error sending email {queue_item.email_id}: {str(e)}")
                        await self._handle_send_error(queue_item, str(e), db)
                
                # Wait before next batch
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in email queue processing: {str(e)}")
                await asyncio.sleep(60)
    
    async def _send_email(self, queue_item: EmailQueue, db: Session) -> None:
        """Send a single email"""
        email = db.query(Email).filter(Email.id == queue_item.email_id).first()
        if not email:
            logger.error(f"Email {queue_item.email_id} not found")
            return
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = email.recipient_email
            msg['Subject'] = email.subject
            
            # Add tracking pixel
            tracking_pixel = f'<img src="http://localhost:8000/emails/{email.id}/track" width="1" height="1" style="display:none;">'
            
            # Create HTML content with tracking
            html_content = f"""
            <html>
            <body>
                {email.personalized_content}
                {tracking_pixel}
            </body>
            </html>
            """
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            # Update email status
            email.sent_at = datetime.utcnow()
            queue_item.status = "sent"
            
            db.commit()
            
            logger.info(f"Email sent successfully to {email.recipient_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email {email.id}: {str(e)}")
            raise e
    
    async def _handle_send_error(self, queue_item: EmailQueue, error: str, db: Session) -> None:
        """Handle email sending errors"""
        queue_item.retry_count += 1
        queue_item.error_message = error
        
        if queue_item.retry_count >= queue_item.max_retries:
            queue_item.status = "failed"
            logger.error(f"Email {queue_item.email_id} failed after {queue_item.max_retries} retries")
        else:
            # Reschedule for retry
            queue_item.scheduled_at = datetime.utcnow() + timedelta(minutes=5)
            logger.warning(f"Email {queue_item.email_id} scheduled for retry {queue_item.retry_count}")
        
        db.commit()
    
    async def track_email_open(self, email_id: int, db: Session) -> None:
        """Track email open"""
        email = db.query(Email).filter(Email.id == email_id).first()
        if email and not email.is_opened:
            email.is_opened = True
            email.opened_at = datetime.utcnow()
            db.commit()
            
            # Update campaign stats
            campaign = db.query(Campaign).filter(Campaign.id == email.campaign_id).first()
            if campaign:
                campaign.opened_count += 1
                db.commit()
    
    async def track_email_click(self, email_id: int, link: str, db: Session) -> None:
        """Track email click"""
        email = db.query(Email).filter(Email.id == email_id).first()
        if email and not email.is_clicked:
            email.is_clicked = True
            email.clicked_at = datetime.utcnow()
            email.clicked_link = link
            db.commit()
            
            # Update campaign stats
            campaign = db.query(Campaign).filter(Campaign.id == email.campaign_id).first()
            if campaign:
                campaign.clicked_count += 1
                db.commit()
    
    async def get_campaign_analytics(self, campaign_id: int, db: Session) -> Dict[str, Any]:
        """Get campaign analytics"""
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {}
        
        # Calculate rates
        total_sent = campaign.total_recipients
        open_rate = (campaign.opened_count / total_sent * 100) if total_sent > 0 else 0
        click_rate = (campaign.clicked_count / total_sent * 100) if total_sent > 0 else 0
        bounce_rate = (campaign.bounce_count / total_sent * 100) if total_sent > 0 else 0
        unsubscribe_rate = (campaign.unsubscribe_count / total_sent * 100) if total_sent > 0 else 0
        
        return {
            'campaign_id': campaign_id,
            'campaign_name': campaign.name,
            'total_recipients': total_sent,
            'opened_count': campaign.opened_count,
            'clicked_count': campaign.clicked_count,
            'bounce_count': campaign.bounce_count,
            'unsubscribe_count': campaign.unsubscribe_count,
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2),
            'bounce_rate': round(bounce_rate, 2),
            'unsubscribe_rate': round(unsubscribe_rate, 2),
            'sent_at': campaign.sent_at,
            'created_at': campaign.created_at
        }
    
    async def get_email_templates(self) -> List[Dict[str, Any]]:
        """Get available email templates"""
        templates = [
            {
                'id': 'newsletter',
                'name': 'Newsletter',
                'description': 'General newsletter template',
                'subject': 'Weekly Update from {company}',
                'content': '''
                <h2>Hello {name}!</h2>
                <p>Thank you for your interest in {company}.</p>
                <p>Here's what's new this week...</p>
                <p>Best regards,<br>The {company} Team</p>
                '''
            },
            {
                'id': 'promotional',
                'name': 'Promotional',
                'description': 'Promotional email template',
                'subject': 'Special Offer for {name}',
                'content': '''
                <h2>Hi {name}!</h2>
                <p>We have an exclusive offer for you at {company}!</p>
                <p>Don't miss out on this limited-time deal.</p>
                <p>Click here to learn more!</p>
                <p>Best regards,<br>The {company} Team</p>
                '''
            },
            {
                'id': 'follow_up',
                'name': 'Follow-up',
                'description': 'Follow-up email template',
                'subject': 'Following up on our conversation',
                'content': '''
                <h2>Hi {name}!</h2>
                <p>I wanted to follow up on our recent conversation about {company}.</p>
                <p>Do you have any questions I can help with?</p>
                <p>Best regards,<br>The {company} Team</p>
                '''
            }
        ]
        
        return templates
