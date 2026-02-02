"""
Background Email Scheduler - Send emails when user is offline
"""

import threading
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid
from email_sender import email_sender

class EmailScheduler:
    def __init__(self):
        self.scheduled_emails_file = "scheduled_emails.json"
        self.scheduled_emails = self.load_scheduled_emails()
        self.is_running = False
        self.scheduler_thread = None
    
    def load_scheduled_emails(self) -> List[Dict]:
        """Load scheduled emails from file"""
        if os.path.exists(self.scheduled_emails_file):
            try:
                with open(self.scheduled_emails_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_scheduled_emails(self):
        """Save scheduled emails to file"""
        with open(self.scheduled_emails_file, 'w', encoding='utf-8') as f:
            json.dump(self.scheduled_emails, f, indent=2, ensure_ascii=False)
    
    def schedule_campaign(self, campaign_name: str, recipients: List[Dict], 
                         subject: str, body: str, send_time: datetime, 
                         delay_seconds: int = 20) -> str:
        """Schedule a campaign for future sending"""
        
        campaign_id = f"{campaign_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        scheduled_campaign = {
            'id': campaign_id,
            'campaign_name': campaign_name,
            'recipients': recipients,
            'subject': subject,
            'body': body,
            'send_time': send_time.isoformat(),
            'delay_seconds': delay_seconds,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
            'total_emails': len(recipients)
        }
        
        self.scheduled_emails.append(scheduled_campaign)
        self.save_scheduled_emails()
        
        return campaign_id
    
    def start_scheduler(self):
        """Start the background email scheduler"""
        if not self.is_running:
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            print("📧 Email scheduler started")
    
    def stop_scheduler(self):
        """Stop the background email scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        print("📧 Email scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop - runs in background"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check for emails ready to send
                emails_to_send = []
                for email in self.scheduled_emails:
                    if email['status'] == 'scheduled':
                        send_time = datetime.fromisoformat(email['send_time'])
                        if current_time >= send_time:
                            emails_to_send.append(email)
                
                # Send scheduled emails
                for email in emails_to_send:
                    self._send_scheduled_campaign(email)
                
                # Sleep for 30 seconds before checking again
                time.sleep(30)
                
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _send_scheduled_campaign(self, campaign_data: Dict):
        """Send a scheduled campaign"""
        try:
            # Update status to sending
            campaign_data['status'] = 'sending'
            campaign_data['started_at'] = datetime.now().isoformat()
            self.save_scheduled_emails()
            
            # Send emails
            results = email_sender.send_bulk_emails(
                recipients=campaign_data['recipients'],
                subject=campaign_data['subject'],
                body=campaign_data['body'],
                campaign_id=campaign_data['id'],
                delay_seconds=campaign_data['delay_seconds']
            )
            
            # Update status to completed
            successful = len([r for r in results if r['status'] == 'sent'])
            failed = len([r for r in results if r['status'] == 'failed'])
            
            campaign_data['status'] = 'completed'
            campaign_data['completed_at'] = datetime.now().isoformat()
            campaign_data['successful_emails'] = successful
            campaign_data['failed_emails'] = failed
            self.save_scheduled_emails()
            
            print(f"✅ Campaign '{campaign_data['campaign_name']}' completed: {successful} sent, {failed} failed")
            
        except Exception as e:
            # Update status to failed
            campaign_data['status'] = 'failed'
            campaign_data['error'] = str(e)
            campaign_data['failed_at'] = datetime.now().isoformat()
            self.save_scheduled_emails()
            
            print(f"❌ Campaign '{campaign_data['campaign_name']}' failed: {e}")
    
    def get_scheduled_campaigns(self) -> List[Dict]:
        """Get all scheduled campaigns"""
        return self.scheduled_emails
    
    def get_campaign_status(self, campaign_id: str) -> Dict:
        """Get status of a specific campaign"""
        for campaign in self.scheduled_emails:
            if campaign['id'] == campaign_id:
                return campaign
        return {}
    
    def cancel_campaign(self, campaign_id: str) -> bool:
        """Cancel a scheduled campaign"""
        for i, campaign in enumerate(self.scheduled_emails):
            if campaign['id'] == campaign_id and campaign['status'] == 'scheduled':
                self.scheduled_emails[i]['status'] = 'cancelled'
                self.scheduled_emails[i]['cancelled_at'] = datetime.now().isoformat()
                self.save_scheduled_emails()
                return True
        return False
    
    def get_next_send_time(self) -> str:
        """Get the next scheduled send time"""
        scheduled_emails = [e for e in self.scheduled_emails if e['status'] == 'scheduled']
        if scheduled_emails:
            next_time = min([datetime.fromisoformat(e['send_time']) for e in scheduled_emails])
            return next_time.strftime('%Y-%m-%d %H:%M:%S')
        return "No emails scheduled"

# Global scheduler instance
email_scheduler = EmailScheduler()

# Start scheduler when module is imported
email_scheduler.start_scheduler()
