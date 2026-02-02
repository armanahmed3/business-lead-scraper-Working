"""
Campaign management service
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import Campaign, Lead, Email
from ..schemas import CampaignCreate, CampaignResponse
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CampaignService:
    """Service for campaign management operations"""
    
    def __init__(self):
        pass
    
    async def create_campaign(self, campaign_data: CampaignCreate, user_id: int, db: Session) -> Campaign:
        """Create a new email campaign"""
        try:
            campaign = Campaign(
                user_id=user_id,
                name=campaign_data.name,
                subject=campaign_data.subject,
                content=campaign_data.content,
                template_type=campaign_data.template_type,
                scheduled_at=campaign_data.scheduled_at
            )
            
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
            
            logger.info(f"Campaign created: {campaign.id} for user {user_id}")
            return campaign
            
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            raise e
    
    async def get_campaigns(self, user_id: int, db: Session) -> List[Campaign]:
        """Get all campaigns for a user"""
        try:
            campaigns = db.query(Campaign).filter(Campaign.user_id == user_id).order_by(Campaign.created_at.desc()).all()
            return campaigns
            
        except Exception as e:
            logger.error(f"Error getting campaigns: {str(e)}")
            raise e
    
    async def get_campaign(self, campaign_id: int, user_id: int, db: Session) -> Optional[Campaign]:
        """Get a specific campaign"""
        try:
            campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            return campaign
            
        except Exception as e:
            logger.error(f"Error getting campaign {campaign_id}: {str(e)}")
            raise e
    
    async def update_campaign(self, campaign_id: int, campaign_data: Dict[str, Any], user_id: int, db: Session) -> Optional[Campaign]:
        """Update a campaign"""
        try:
            campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                return None
            
            # Update fields
            for field, value in campaign_data.items():
                if hasattr(campaign, field):
                    setattr(campaign, field, value)
            
            campaign.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(campaign)
            
            logger.info(f"Campaign updated: {campaign_id}")
            return campaign
            
        except Exception as e:
            logger.error(f"Error updating campaign {campaign_id}: {str(e)}")
            raise e
    
    async def delete_campaign(self, campaign_id: int, user_id: int, db: Session) -> bool:
        """Delete a campaign"""
        try:
            campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                return False
            
            # Delete associated emails
            db.query(Email).filter(Email.campaign_id == campaign_id).delete()
            
            # Delete campaign
            db.delete(campaign)
            db.commit()
            
            logger.info(f"Campaign deleted: {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting campaign {campaign_id}: {str(e)}")
            raise e
    
    async def duplicate_campaign(self, campaign_id: int, user_id: int, db: Session) -> Optional[Campaign]:
        """Duplicate a campaign"""
        try:
            original_campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not original_campaign:
                return None
            
            # Create new campaign
            new_campaign = Campaign(
                user_id=user_id,
                name=f"{original_campaign.name} (Copy)",
                subject=original_campaign.subject,
                content=original_campaign.content,
                template_type=original_campaign.template_type,
                status="draft"
            )
            
            db.add(new_campaign)
            db.commit()
            db.refresh(new_campaign)
            
            logger.info(f"Campaign duplicated: {campaign_id} -> {new_campaign.id}")
            return new_campaign
            
        except Exception as e:
            logger.error(f"Error duplicating campaign {campaign_id}: {str(e)}")
            raise e
    
    async def schedule_campaign(self, campaign_id: int, scheduled_at: datetime, user_id: int, db: Session) -> bool:
        """Schedule a campaign for sending"""
        try:
            campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                return False
            
            campaign.scheduled_at = scheduled_at
            campaign.status = "scheduled"
            campaign.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Campaign scheduled: {campaign_id} for {scheduled_at}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling campaign {campaign_id}: {str(e)}")
            raise e
    
    async def pause_campaign(self, campaign_id: int, user_id: int, db: Session) -> bool:
        """Pause a campaign"""
        try:
            campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                return False
            
            if campaign.status in ["sending", "scheduled"]:
                campaign.status = "paused"
                campaign.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Campaign paused: {campaign_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error pausing campaign {campaign_id}: {str(e)}")
            raise e
    
    async def resume_campaign(self, campaign_id: int, user_id: int, db: Session) -> bool:
        """Resume a paused campaign"""
        try:
            campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                return False
            
            if campaign.status == "paused":
                if campaign.scheduled_at and campaign.scheduled_at > datetime.utcnow():
                    campaign.status = "scheduled"
                else:
                    campaign.status = "sending"
                
                campaign.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Campaign resumed: {campaign_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resuming campaign {campaign_id}: {str(e)}")
            raise e
    
    async def get_campaign_stats(self, campaign_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """Get campaign statistics"""
        try:
            campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                return {}
            
            # Get email statistics
            emails = db.query(Email).filter(Email.campaign_id == campaign_id).all()
            
            total_emails = len(emails)
            sent_emails = sum(1 for email in emails if email.sent_at)
            opened_emails = sum(1 for email in emails if email.is_opened)
            clicked_emails = sum(1 for email in emails if email.is_clicked)
            bounced_emails = sum(1 for email in emails if email.is_bounced)
            unsubscribed_emails = sum(1 for email in emails if email.is_unsubscribed)
            
            # Calculate rates
            open_rate = (opened_emails / sent_emails * 100) if sent_emails > 0 else 0
            click_rate = (clicked_emails / sent_emails * 100) if sent_emails > 0 else 0
            bounce_rate = (bounced_emails / sent_emails * 100) if sent_emails > 0 else 0
            unsubscribe_rate = (unsubscribed_emails / sent_emails * 100) if sent_emails > 0 else 0
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "status": campaign.status,
                "total_recipients": campaign.total_recipients,
                "total_emails": total_emails,
                "sent_emails": sent_emails,
                "opened_emails": opened_emails,
                "clicked_emails": clicked_emails,
                "bounced_emails": bounced_emails,
                "unsubscribed_emails": unsubscribed_emails,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "bounce_rate": round(bounce_rate, 2),
                "unsubscribe_rate": round(unsubscribe_rate, 2),
                "created_at": campaign.created_at,
                "scheduled_at": campaign.scheduled_at,
                "sent_at": campaign.sent_at
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign stats for {campaign_id}: {str(e)}")
            raise e
    
    async def get_campaign_recipients(self, campaign_id: int, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get campaign recipients with their status"""
        try:
            campaign = db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                return []
            
            # Get emails with lead information
            emails = db.query(Email, Lead).join(Lead, Email.lead_id == Lead.id).filter(
                Email.campaign_id == campaign_id
            ).all()
            
            recipients = []
            for email, lead in emails:
                recipients.append({
                    "email_id": email.id,
                    "lead_id": lead.id,
                    "email": email.recipient_email,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "company": lead.company,
                    "status": "sent" if email.sent_at else "pending",
                    "opened": email.is_opened,
                    "clicked": email.is_clicked,
                    "bounced": email.is_bounced,
                    "unsubscribed": email.is_unsubscribed,
                    "sent_at": email.sent_at,
                    "opened_at": email.opened_at,
                    "clicked_at": email.clicked_at
                })
            
            return recipients
            
        except Exception as e:
            logger.error(f"Error getting campaign recipients for {campaign_id}: {str(e)}")
            raise e
    
    async def get_campaign_templates(self) -> List[Dict[str, Any]]:
        """Get available campaign templates"""
        templates = [
            {
                "id": "newsletter",
                "name": "Newsletter",
                "description": "General newsletter template for regular updates",
                "subject": "Weekly Update from {company}",
                "content": """
                <h2>Hello {name}!</h2>
                <p>Thank you for your interest in {company}.</p>
                <p>Here's what's new this week:</p>
                <ul>
                    <li>Feature updates</li>
                    <li>Industry insights</li>
                    <li>Upcoming events</li>
                </ul>
                <p>Best regards,<br>The {company} Team</p>
                """,
                "category": "newsletter"
            },
            {
                "id": "promotional",
                "name": "Promotional",
                "description": "Promotional email template for special offers",
                "subject": "Special Offer for {name} - Limited Time!",
                "content": """
                <h2>Hi {name}!</h2>
                <p>We have an exclusive offer for you at {company}!</p>
                <div style="background-color: #f0f0f0; padding: 20px; margin: 20px 0; text-align: center;">
                    <h3>🎉 Special Discount</h3>
                    <p>Get 20% off your first order!</p>
                    <a href="#" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Claim Offer</a>
                </div>
                <p>Don't miss out on this limited-time deal.</p>
                <p>Best regards,<br>The {company} Team</p>
                """,
                "category": "promotional"
            },
            {
                "id": "follow_up",
                "name": "Follow-up",
                "description": "Follow-up email template for nurturing leads",
                "subject": "Following up on our conversation",
                "content": """
                <h2>Hi {name}!</h2>
                <p>I wanted to follow up on our recent conversation about {company}.</p>
                <p>Do you have any questions I can help with?</p>
                <p>I'd love to schedule a brief call to discuss how we can help your business grow.</p>
                <p>Best regards,<br>The {company} Team</p>
                """,
                "category": "follow_up"
            },
            {
                "id": "welcome",
                "name": "Welcome",
                "description": "Welcome email template for new subscribers",
                "subject": "Welcome to {company}!",
                "content": """
                <h2>Welcome {name}!</h2>
                <p>Thank you for joining {company}!</p>
                <p>We're excited to have you on board. Here's what you can expect:</p>
                <ul>
                    <li>Regular updates and insights</li>
                    <li>Exclusive offers and promotions</li>
                    <li>Industry best practices</li>
                </ul>
                <p>If you have any questions, feel free to reach out!</p>
                <p>Best regards,<br>The {company} Team</p>
                """,
                "category": "welcome"
            }
        ]
        
        return templates
