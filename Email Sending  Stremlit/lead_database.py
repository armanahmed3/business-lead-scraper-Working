"""
Lead Database Management System
Stores and manages leads with advanced features
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

class LeadDatabase:
    def __init__(self, db_file: str = "leads_database.json"):
        self.db_file = db_file
        self.leads = self.load_leads()
    
    def load_leads(self) -> List[Dict]:
        """Load leads from database file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_leads(self):
        """Save leads to database file"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.leads, f, indent=2, ensure_ascii=False)
    
    def add_lead(self, lead_data: Dict) -> str:
        """Add a new lead to database"""
        lead_id = str(uuid.uuid4())
        lead = {
            'id': lead_id,
            'name': lead_data.get('name', ''),
            'email': lead_data.get('email', ''),
            'company': lead_data.get('company', ''),
            'phone': lead_data.get('phone', ''),
            'title': lead_data.get('title', ''),
            'industry': lead_data.get('industry', ''),
            'source': lead_data.get('source', ''),
            'category': lead_data.get('category', 'General'),
            'score': lead_data.get('score', 50),
            'status': lead_data.get('status', 'New'),
            'tags': lead_data.get('tags', []),
            'notes': lead_data.get('notes', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_contact': None,
            'email_sent': 0,
            'email_opened': 0,
            'email_clicked': 0,
            'converted': False
        }
        self.leads.append(lead)
        self.save_leads()
        return lead_id
    
    def add_leads_bulk(self, leads_data: List[Dict]) -> List[str]:
        """Add multiple leads from CSV upload"""
        lead_ids = []
        for lead_data in leads_data:
            lead_id = self.add_lead(lead_data)
            lead_ids.append(lead_id)
        return lead_ids
    
    def get_lead(self, lead_id: str) -> Optional[Dict]:
        """Get a specific lead by ID"""
        for lead in self.leads:
            if lead['id'] == lead_id:
                return lead
        return None
    
    def get_leads_by_status(self, status: str) -> List[Dict]:
        """Get leads by status"""
        return [lead for lead in self.leads if lead['status'] == status]
    
    def get_leads_by_score_range(self, min_score: int, max_score: int) -> List[Dict]:
        """Get leads by score range"""
        return [lead for lead in self.leads if min_score <= lead['score'] <= max_score]
    
    def get_hot_leads(self) -> List[Dict]:
        """Get hot leads (score 80-100)"""
        return self.get_leads_by_score_range(80, 100)
    
    def get_warm_leads(self) -> List[Dict]:
        """Get warm leads (score 60-79)"""
        return self.get_leads_by_score_range(60, 79)
    
    def get_cold_leads(self) -> List[Dict]:
        """Get cold leads (score 0-59)"""
        return self.get_leads_by_score_range(0, 59)
    
    def update_lead(self, lead_id: str, updates: Dict) -> bool:
        """Update a lead"""
        for i, lead in enumerate(self.leads):
            if lead['id'] == lead_id:
                self.leads[i].update(updates)
                self.leads[i]['updated_at'] = datetime.now().isoformat()
                self.save_leads()
                return True
        return False
    
    def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead"""
        for i, lead in enumerate(self.leads):
            if lead['id'] == lead_id:
                del self.leads[i]
                self.save_leads()
                return True
        return False
    
    def search_leads(self, query: str) -> List[Dict]:
        """Search leads by name, email, or company"""
        if not query:
            return self.leads
            
        results = []
        query = query.lower()
        
        for lead in self.leads:
            # Ensure all fields are strings before calling .lower()
            name = str(lead.get('name', '')) if lead.get('name') is not None else ''
            email = str(lead.get('email', '')) if lead.get('email') is not None else ''
            company = str(lead.get('company', '')) if lead.get('company') is not None else ''
            
            if (query in name.lower() or 
                query in email.lower() or 
                query in company.lower()):
                results.append(lead)
        return results
    
    def get_lead_statistics(self) -> Dict:
        """Get lead statistics"""
        total = len(self.leads)
        hot = len(self.get_hot_leads())
        warm = len(self.get_warm_leads())
        cold = len(self.get_cold_leads())
        
        return {
            'total_leads': total,
            'hot_leads': hot,
            'warm_leads': warm,
            'cold_leads': cold,
            'conversion_rate': len([l for l in self.leads if l['converted']]) / total * 100 if total > 0 else 0
        }
    
    def get_all_leads(self) -> List[Dict]:
        """Get all leads"""
        return self.leads
    
    def get_leads_by_category(self, category: str) -> List[Dict]:
        """Get leads by category"""
        return [lead for lead in self.leads if lead.get('category', 'General') == category]
    
    def get_all_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = set()
        for lead in self.leads:
            categories.add(lead.get('category', 'General'))
        return sorted(list(categories))
    
    def export_leads(self, format: str = 'csv') -> str:
        """Export leads to CSV"""
        if format == 'csv':
            df = pd.DataFrame(self.leads)
            filename = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            return filename
        return None

# Global lead database instance
lead_db = LeadDatabase()
