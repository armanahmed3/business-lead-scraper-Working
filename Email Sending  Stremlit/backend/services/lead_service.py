"""
Lead management service
"""

import pandas as pd
import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models import Lead, User
from ..schemas import LeadCreate, LeadResponse
import logging

logger = logging.getLogger(__name__)

class LeadService:
    """Service for lead management operations"""
    
    def __init__(self):
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
    
    async def process_csv_leads(self, file_data: Dict[str, Any], user_id: int, db: Session) -> List[Lead]:
        """Process uploaded CSV file and create leads"""
        try:
            # Parse CSV data
            df = pd.read_csv(file_data['file_path'])
            
            leads = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Extract and validate lead data
                    lead_data = self._extract_lead_data(row)
                    
                    if not lead_data['email']:
                        errors.append(f"Row {index + 1}: Missing email address")
                        continue
                    
                    # Check for duplicate email
                    existing_lead = db.query(Lead).filter(
                        Lead.email == lead_data['email'],
                        Lead.user_id == user_id
                    ).first()
                    
                    if existing_lead:
                        errors.append(f"Row {index + 1}: Email already exists")
                        continue
                    
                    # Create lead
                    lead = Lead(
                        user_id=user_id,
                        **lead_data
                    )
                    
                    # AI-powered data enhancement
                    lead = await self._enhance_lead_data(lead)
                    
                    db.add(lead)
                    leads.append(lead)
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    logger.error(f"Error processing row {index + 1}: {str(e)}")
            
            db.commit()
            
            # Log processing results
            logger.info(f"Processed {len(leads)} leads with {len(errors)} errors")
            
            return leads
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            raise Exception(f"Failed to process CSV file: {str(e)}")
    
    def _extract_lead_data(self, row: pd.Series) -> Dict[str, Any]:
        """Extract and clean lead data from CSV row"""
        # Common column name mappings
        column_mappings = {
            'email': ['email', 'e-mail', 'email_address', 'mail'],
            'first_name': ['first_name', 'firstname', 'fname', 'first'],
            'last_name': ['last_name', 'lastname', 'lname', 'last'],
            'company': ['company', 'organization', 'org', 'business'],
            'phone': ['phone', 'telephone', 'mobile', 'cell', 'phone_number'],
            'job_title': ['title', 'position', 'job_title', 'role'],
            'industry': ['industry', 'sector', 'field']
        }
        
        lead_data = {}
        
        # Map columns to lead fields
        for field, possible_columns in column_mappings.items():
            value = None
            for col in possible_columns:
                if col.lower() in [c.lower() for c in row.index]:
                    value = str(row[col]).strip() if pd.notna(row[col]) else None
                    break
            
            lead_data[field] = value if value and value != 'nan' else None
        
        # Validate email
        if lead_data['email']:
            lead_data['email'] = lead_data['email'].lower().strip()
            if not self.email_pattern.match(lead_data['email']):
                lead_data['email'] = None
        
        # Validate phone
        if lead_data['phone']:
            # Clean phone number
            phone = re.sub(r'[^\d\+]', '', lead_data['phone'])
            if not self.phone_pattern.match(phone):
                lead_data['phone'] = None
            else:
                lead_data['phone'] = phone
        
        return lead_data
    
    async def _enhance_lead_data(self, lead: Lead) -> Lead:
        """Enhance lead data using AI and external services"""
        try:
            # AI-powered data completion
            if not lead.first_name and not lead.last_name and lead.email:
                # Try to extract name from email
                email_local = lead.email.split('@')[0]
                if '.' in email_local:
                    parts = email_local.split('.')
                    lead.first_name = parts[0].title()
                    lead.last_name = parts[1].title()
                else:
                    lead.first_name = email_local.title()
            
            # AI-powered industry detection
            if not lead.industry and lead.company:
                lead.industry = await self._detect_industry(lead.company)
            
            # AI-powered lead scoring
            lead.ai_score = await self._calculate_lead_score(lead)
            
            # Data validation and cleaning
            lead = self._clean_lead_data(lead)
            
            return lead
            
        except Exception as e:
            logger.error(f"Error enhancing lead data: {str(e)}")
            return lead
    
    async def _detect_industry(self, company_name: str) -> str:
        """Detect industry based on company name using AI"""
        # Simple keyword-based industry detection
        # In production, this would use a more sophisticated AI model
        industry_keywords = {
            'technology': ['tech', 'software', 'ai', 'data', 'cloud', 'digital'],
            'finance': ['bank', 'financial', 'investment', 'capital', 'credit'],
            'healthcare': ['health', 'medical', 'pharma', 'hospital', 'clinic'],
            'retail': ['retail', 'store', 'shop', 'commerce', 'ecommerce'],
            'manufacturing': ['manufacturing', 'factory', 'production', 'industrial'],
            'education': ['school', 'university', 'education', 'learning', 'academy']
        }
        
        company_lower = company_name.lower()
        for industry, keywords in industry_keywords.items():
            if any(keyword in company_lower for keyword in keywords):
                return industry.title()
        
        return 'Other'
    
    async def _calculate_lead_score(self, lead: Lead) -> float:
        """Calculate AI-powered lead score"""
        score = 0.0
        
        # Email domain scoring
        if lead.email:
            domain = lead.email.split('@')[1].lower()
            if domain in ['gmail.com', 'yahoo.com', 'hotmail.com']:
                score += 0.1  # Lower score for personal emails
            else:
                score += 0.3  # Higher score for business emails
        
        # Company information
        if lead.company:
            score += 0.2
        
        # Job title scoring
        if lead.job_title:
            title_lower = lead.job_title.lower()
            if any(keyword in title_lower for keyword in ['ceo', 'cto', 'founder', 'director', 'manager']):
                score += 0.3
            elif any(keyword in title_lower for keyword in ['senior', 'lead', 'principal']):
                score += 0.2
            else:
                score += 0.1
        
        # Phone number
        if lead.phone:
            score += 0.1
        
        # Industry scoring
        if lead.industry:
            high_value_industries = ['technology', 'finance', 'healthcare']
            if lead.industry.lower() in high_value_industries:
                score += 0.2
            else:
                score += 0.1
        
        # Normalize score to 0-1 range
        return min(score, 1.0)
    
    def _clean_lead_data(self, lead: Lead) -> Lead:
        """Clean and standardize lead data"""
        # Clean names
        if lead.first_name:
            lead.first_name = lead.first_name.strip().title()
        if lead.last_name:
            lead.last_name = lead.last_name.strip().title()
        
        # Clean company name
        if lead.company:
            lead.company = lead.company.strip().title()
        
        # Clean job title
        if lead.job_title:
            lead.job_title = lead.job_title.strip().title()
        
        # Clean industry
        if lead.industry:
            lead.industry = lead.industry.strip().title()
        
        return lead
    
    async def search_leads(self, query: str, user_id: int, db: Session) -> List[Lead]:
        """Search leads based on query"""
        leads = db.query(Lead).filter(Lead.user_id == user_id)
        
        if query:
            search_filter = (
                Lead.first_name.ilike(f"%{query}%") |
                Lead.last_name.ilike(f"%{query}%") |
                Lead.email.ilike(f"%{query}%") |
                Lead.company.ilike(f"%{query}%") |
                Lead.job_title.ilike(f"%{query}%")
            )
            leads = leads.filter(search_filter)
        
        return leads.all()
    
    async def get_lead_analytics(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get lead analytics for user"""
        total_leads = db.query(Lead).filter(Lead.user_id == user_id).count()
        
        # Lead status distribution
        status_counts = db.query(Lead.status, db.func.count(Lead.id)).filter(
            Lead.user_id == user_id
        ).group_by(Lead.status).all()
        
        # Industry distribution
        industry_counts = db.query(Lead.industry, db.func.count(Lead.id)).filter(
            Lead.user_id == user_id,
            Lead.industry.isnot(None)
        ).group_by(Lead.industry).all()
        
        # AI score distribution
        avg_score = db.query(db.func.avg(Lead.ai_score)).filter(
            Lead.user_id == user_id
        ).scalar() or 0
        
        return {
            'total_leads': total_leads,
            'status_distribution': dict(status_counts),
            'industry_distribution': dict(industry_counts),
            'average_ai_score': round(avg_score, 2)
        }
