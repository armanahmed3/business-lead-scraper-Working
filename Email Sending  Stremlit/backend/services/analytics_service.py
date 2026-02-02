"""
Analytics service for data analysis and reporting
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..models import User, Lead, Campaign, Email, Analytics
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for analytics and reporting"""
    
    def __init__(self):
        pass
    
    async def get_dashboard_analytics(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get comprehensive dashboard analytics"""
        try:
            # Basic counts
            total_leads = db.query(Lead).filter(Lead.user_id == user_id).count()
            total_campaigns = db.query(Campaign).filter(Campaign.user_id == user_id).count()
            
            # Email statistics
            total_emails_sent = db.query(Email).join(Campaign).filter(
                Campaign.user_id == user_id,
                Email.sent_at.isnot(None)
            ).count()
            
            opened_emails = db.query(Email).join(Campaign).filter(
                Campaign.user_id == user_id,
                Email.is_opened == True
            ).count()
            
            clicked_emails = db.query(Email).join(Campaign).filter(
                Campaign.user_id == user_id,
                Email.is_clicked == True
            ).count()
            
            bounced_emails = db.query(Email).join(Campaign).filter(
                Campaign.user_id == user_id,
                Email.is_bounced == True
            ).count()
            
            unsubscribed_emails = db.query(Email).join(Campaign).filter(
                Campaign.user_id == user_id,
                Email.is_unsubscribed == True
            ).count()
            
            # Calculate rates
            open_rate = (opened_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0
            click_rate = (clicked_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0
            bounce_rate = (bounced_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0
            unsubscribe_rate = (unsubscribed_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0
            
            # Revenue calculation (placeholder - would need actual revenue data)
            revenue = total_leads * 10  # $10 per lead placeholder
            
            # Top performing campaigns
            top_campaigns = await self._get_top_campaigns(user_id, db)
            
            # Lead quality distribution
            lead_quality_dist = await self._get_lead_quality_distribution(user_id, db)
            
            # Recent activity
            recent_activity = await self._get_recent_activity(user_id, db)
            
            return {
                "total_leads": total_leads,
                "total_campaigns": total_campaigns,
                "total_emails_sent": total_emails_sent,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "bounce_rate": round(bounce_rate, 2),
                "unsubscribe_rate": round(unsubscribe_rate, 2),
                "revenue": revenue,
                "top_performing_campaigns": top_campaigns,
                "lead_quality_distribution": lead_quality_dist,
                "recent_activity": recent_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard analytics: {str(e)}")
            raise e
    
    async def _get_top_campaigns(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get top performing campaigns"""
        try:
            campaigns = db.query(Campaign).filter(Campaign.user_id == user_id).all()
            
            campaign_performance = []
            for campaign in campaigns:
                if campaign.total_recipients > 0:
                    open_rate = (campaign.opened_count / campaign.total_recipients * 100)
                    click_rate = (campaign.clicked_count / campaign.total_recipients * 100)
                    
                    campaign_performance.append({
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name,
                        "total_recipients": campaign.total_recipients,
                        "open_rate": round(open_rate, 2),
                        "click_rate": round(click_rate, 2),
                        "performance_score": round((open_rate + click_rate) / 2, 2)
                    })
            
            # Sort by performance score
            campaign_performance.sort(key=lambda x: x["performance_score"], reverse=True)
            
            return campaign_performance[:5]  # Top 5
            
        except Exception as e:
            logger.error(f"Error getting top campaigns: {str(e)}")
            return []
    
    async def _get_lead_quality_distribution(self, user_id: int, db: Session) -> Dict[str, int]:
        """Get lead quality distribution"""
        try:
            # Get leads with AI scores
            leads = db.query(Lead).filter(
                Lead.user_id == user_id,
                Lead.ai_score.isnot(None)
            ).all()
            
            distribution = {
                "high_quality": 0,  # > 0.7
                "medium_quality": 0,  # 0.4 - 0.7
                "low_quality": 0   # < 0.4
            }
            
            for lead in leads:
                if lead.ai_score > 0.7:
                    distribution["high_quality"] += 1
                elif lead.ai_score >= 0.4:
                    distribution["medium_quality"] += 1
                else:
                    distribution["low_quality"] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting lead quality distribution: {str(e)}")
            return {"high_quality": 0, "medium_quality": 0, "low_quality": 0}
    
    async def _get_recent_activity(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get recent activity"""
        try:
            activities = []
            
            # Recent campaigns
            recent_campaigns = db.query(Campaign).filter(
                Campaign.user_id == user_id
            ).order_by(desc(Campaign.created_at)).limit(3).all()
            
            for campaign in recent_campaigns:
                activities.append({
                    "type": "campaign_created",
                    "message": f"Campaign '{campaign.name}' created",
                    "timestamp": campaign.created_at,
                    "status": campaign.status
                })
            
            # Recent leads
            recent_leads = db.query(Lead).filter(
                Lead.user_id == user_id
            ).order_by(desc(Lead.created_at)).limit(3).all()
            
            for lead in recent_leads:
                activities.append({
                    "type": "lead_added",
                    "message": f"New lead added: {lead.email}",
                    "timestamp": lead.created_at,
                    "status": lead.status
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return activities[:10]  # Last 10 activities
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []
    
    async def get_campaign_analytics(self, campaign_id: int, db: Session) -> Dict[str, Any]:
        """Get detailed campaign analytics"""
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                return {}
            
            # Get email data
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
            
            # Time-based analytics
            time_analytics = await self._get_time_analytics(emails)
            
            # Device/location analytics (placeholder)
            device_analytics = {
                "desktop": 60,
                "mobile": 35,
                "tablet": 5
            }
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
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
                "time_analytics": time_analytics,
                "device_analytics": device_analytics,
                "created_at": campaign.created_at,
                "sent_at": campaign.sent_at
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {str(e)}")
            raise e
    
    async def _get_time_analytics(self, emails: List[Email]) -> Dict[str, Any]:
        """Get time-based analytics for emails"""
        try:
            # Open times
            open_times = [email.opened_at for email in emails if email.opened_at]
            
            # Click times
            click_times = [email.clicked_at for email in emails if email.clicked_at]
            
            # Calculate hourly distribution
            hourly_opens = {}
            hourly_clicks = {}
            
            for open_time in open_times:
                hour = open_time.hour
                hourly_opens[hour] = hourly_opens.get(hour, 0) + 1
            
            for click_time in click_times:
                hour = click_time.hour
                hourly_clicks[hour] = hourly_clicks.get(hour, 0) + 1
            
            return {
                "hourly_opens": hourly_opens,
                "hourly_clicks": hourly_clicks,
                "peak_open_hour": max(hourly_opens.items(), key=lambda x: x[1])[0] if hourly_opens else None,
                "peak_click_hour": max(hourly_clicks.items(), key=lambda x: x[1])[0] if hourly_clicks else None
            }
            
        except Exception as e:
            logger.error(f"Error getting time analytics: {str(e)}")
            return {}
    
    async def get_lead_analytics(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get lead-specific analytics"""
        try:
            leads = db.query(Lead).filter(Lead.user_id == user_id).all()
            
            if not leads:
                return {}
            
            # Lead status distribution
            status_counts = {}
            for lead in leads:
                status = lead.status or "unknown"
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Industry distribution
            industry_counts = {}
            for lead in leads:
                if lead.industry:
                    industry_counts[lead.industry] = industry_counts.get(lead.industry, 0) + 1
            
            # AI score statistics
            ai_scores = [lead.ai_score for lead in leads if lead.ai_score is not None]
            avg_ai_score = sum(ai_scores) / len(ai_scores) if ai_scores else 0
            
            # Source distribution
            source_counts = {}
            for lead in leads:
                if lead.source:
                    source_counts[lead.source] = source_counts.get(lead.source, 0) + 1
            
            return {
                "total_leads": len(leads),
                "status_distribution": status_counts,
                "industry_distribution": industry_counts,
                "source_distribution": source_counts,
                "average_ai_score": round(avg_ai_score, 2),
                "high_quality_leads": len([s for s in ai_scores if s > 0.7]),
                "medium_quality_leads": len([s for s in ai_scores if 0.4 <= s <= 0.7]),
                "low_quality_leads": len([s for s in ai_scores if s < 0.4])
            }
            
        except Exception as e:
            logger.error(f"Error getting lead analytics: {str(e)}")
            raise e
    
    async def get_performance_trends(self, user_id: int, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Daily email performance
            daily_stats = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                # Get emails sent on this date
                emails_sent = db.query(Email).join(Campaign).filter(
                    Campaign.user_id == user_id,
                    Email.sent_at >= current_date,
                    Email.sent_at < next_date
                ).count()
                
                # Get opens on this date
                emails_opened = db.query(Email).join(Campaign).filter(
                    Campaign.user_id == user_id,
                    Email.opened_at >= current_date,
                    Email.opened_at < next_date
                ).count()
                
                # Get clicks on this date
                emails_clicked = db.query(Email).join(Campaign).filter(
                    Campaign.user_id == user_id,
                    Email.clicked_at >= current_date,
                    Email.clicked_at < next_date
                ).count()
                
                daily_stats.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "emails_sent": emails_sent,
                    "emails_opened": emails_opened,
                    "emails_clicked": emails_clicked,
                    "open_rate": (emails_opened / emails_sent * 100) if emails_sent > 0 else 0,
                    "click_rate": (emails_clicked / emails_sent * 100) if emails_sent > 0 else 0
                })
                
                current_date = next_date
            
            return {
                "daily_stats": daily_stats,
                "period_days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {str(e)}")
            raise e
    
    async def save_analytics(self, user_id: int, metric_name: str, metric_value: float, 
                           metric_data: Dict[str, Any], campaign_id: int = None, db: Session = None):
        """Save analytics data"""
        try:
            analytics = Analytics(
                user_id=user_id,
                campaign_id=campaign_id,
                metric_name=metric_name,
                metric_value=metric_value,
                metric_data=metric_data
            )
            
            db.add(analytics)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving analytics: {str(e)}")
            raise e
