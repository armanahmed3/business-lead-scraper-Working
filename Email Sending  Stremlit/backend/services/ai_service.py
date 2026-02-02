"""
AI service for lead scoring, email generation, and analytics
"""

import openai
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models import Lead, Campaign, Email
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered features"""
    
    def __init__(self):
        # Initialize OpenAI
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize ML models
        self.lead_scoring_model = None
        self.email_classification_model = None
        self.is_models_trained = False
        
        # Feature encoders
        self.industry_encoder = LabelEncoder()
        self.job_title_encoder = LabelEncoder()
    
    async def score_leads(self, leads: List[Lead]) -> List[Tuple[Lead, float]]:
        """Score leads using AI and ML models"""
        try:
            # If models are not trained, use rule-based scoring
            if not self.is_models_trained:
                return await self._rule_based_scoring(leads)
            
            # Use ML model for scoring
            return await self._ml_based_scoring(leads)
            
        except Exception as e:
            logger.error(f"Error scoring leads: {str(e)}")
            return await self._rule_based_scoring(leads)
    
    async def _rule_based_scoring(self, leads: List[Lead]) -> List[Tuple[Lead, float]]:
        """Rule-based lead scoring as fallback"""
        scored_leads = []
        
        for lead in leads:
            score = 0.0
            
            # Email domain scoring
            if lead.email:
                domain = lead.email.split('@')[1].lower()
                if domain in ['gmail.com', 'yahoo.com', 'hotmail.com']:
                    score += 0.1
                else:
                    score += 0.3
            
            # Company information
            if lead.company:
                score += 0.2
                # Company size estimation based on domain
                if any(keyword in lead.company.lower() for keyword in ['inc', 'corp', 'llc', 'ltd']):
                    score += 0.1
            
            # Job title scoring
            if lead.job_title:
                title_lower = lead.job_title.lower()
                if any(keyword in title_lower for keyword in ['ceo', 'cto', 'founder', 'director', 'vp']):
                    score += 0.3
                elif any(keyword in title_lower for keyword in ['manager', 'senior', 'lead', 'principal']):
                    score += 0.2
                else:
                    score += 0.1
            
            # Phone number
            if lead.phone:
                score += 0.1
            
            # Industry scoring
            if lead.industry:
                high_value_industries = ['technology', 'finance', 'healthcare', 'consulting']
                if lead.industry.lower() in high_value_industries:
                    score += 0.2
                else:
                    score += 0.1
            
            # Normalize score
            score = min(score, 1.0)
            scored_leads.append((lead, score))
        
        return scored_leads
    
    async def _ml_based_scoring(self, leads: List[Lead]) -> List[Tuple[Lead, float]]:
        """ML-based lead scoring"""
        try:
            # Prepare features
            features = []
            for lead in leads:
                feature_vector = self._extract_features(lead)
                features.append(feature_vector)
            
            # Predict scores
            features_array = np.array(features)
            scores = self.lead_scoring_model.predict_proba(features_array)[:, 1]  # Probability of high value
            
            return [(lead, float(score)) for lead, score in zip(leads, scores)]
            
        except Exception as e:
            logger.error(f"Error in ML-based scoring: {str(e)}")
            return await self._rule_based_scoring(leads)
    
    def _extract_features(self, lead: Lead) -> List[float]:
        """Extract features for ML model"""
        features = []
        
        # Email features
        if lead.email:
            domain = lead.email.split('@')[1].lower()
            features.extend([
                1 if domain in ['gmail.com', 'yahoo.com', 'hotmail.com'] else 0,  # Personal email
                1 if any(keyword in domain for keyword in ['corp', 'inc', 'llc', 'ltd']) else 0,  # Corporate domain
                len(domain)  # Domain length
            ])
        else:
            features.extend([0, 0, 0])
        
        # Company features
        features.extend([
            1 if lead.company else 0,  # Has company
            len(lead.company) if lead.company else 0,  # Company name length
        ])
        
        # Job title features
        if lead.job_title:
            title_lower = lead.job_title.lower()
            features.extend([
                1 if any(keyword in title_lower for keyword in ['ceo', 'cto', 'founder', 'director', 'vp']) else 0,  # Executive
                1 if any(keyword in title_lower for keyword in ['manager', 'senior', 'lead', 'principal']) else 0,  # Senior level
                len(lead.job_title)  # Title length
            ])
        else:
            features.extend([0, 0, 0])
        
        # Contact features
        features.extend([
            1 if lead.phone else 0,  # Has phone
            1 if lead.industry else 0,  # Has industry
        ])
        
        # Industry encoding
        if lead.industry:
            try:
                industry_encoded = self.industry_encoder.transform([lead.industry])[0]
                features.append(industry_encoded)
            except ValueError:
                features.append(0)  # Unknown industry
        else:
            features.append(0)
        
        return features
    
    async def generate_email_content(self, prompt: str, tone: str = "professional", length: str = "medium") -> str:
        """Generate email content using OpenAI"""
        try:
            if not openai.api_key:
                return await self._fallback_email_generation(prompt, tone, length)
            
            # Create system prompt
            system_prompt = f"""
            You are an expert email marketing copywriter. Generate professional email content based on the user's prompt.
            
            Tone: {tone}
            Length: {length}
            
            Guidelines:
            - Use engaging subject lines
            - Include a clear call-to-action
            - Personalize with placeholders like {{name}} and {{company}}
            - Keep it professional but friendly
            - Use proper email formatting
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating email content: {str(e)}")
            return await self._fallback_email_generation(prompt, tone, length)
    
    async def _fallback_email_generation(self, prompt: str, tone: str, length: str) -> str:
        """Fallback email generation without OpenAI"""
        templates = {
            "professional": {
                "short": f"""
                Subject: {prompt}
                
                Dear {{name}},
                
                I hope this email finds you well. I wanted to reach out regarding {prompt.lower()}.
                
                Please let me know if you have any questions.
                
                Best regards,
                The {{company}} Team
                """,
                "medium": f"""
                Subject: {prompt}
                
                Dear {{name}},
                
                I hope this email finds you well. I wanted to reach out regarding {prompt.lower()}.
                
                We believe this could be valuable for {{company}} and would love to discuss how we can help.
                
                Please let me know if you'd like to schedule a brief call to discuss further.
                
                Best regards,
                The {{company}} Team
                """,
                "long": f"""
                Subject: {prompt}
                
                Dear {{name}},
                
                I hope this email finds you well. I wanted to reach out regarding {prompt.lower()}.
                
                At {{company}}, we understand the challenges that businesses face, and we believe our solution can help address these issues effectively.
                
                We would love to schedule a brief call to discuss how we can help {{company}} achieve its goals.
                
                Please let me know if you'd be interested in learning more.
                
                Best regards,
                The {{company}} Team
                """
            }
        }
        
        return templates.get(tone, templates["professional"]).get(length, templates["professional"]["medium"])
    
    async def train_lead_scoring_model(self, db: Session) -> Dict[str, Any]:
        """Train ML model for lead scoring"""
        try:
            # Get historical data
            leads = db.query(Lead).filter(Lead.ai_score.isnot(None)).all()
            
            if len(leads) < 100:  # Need sufficient data
                return {"status": "insufficient_data", "message": "Need at least 100 leads with scores"}
            
            # Prepare training data
            X = []
            y = []
            
            for lead in leads:
                features = self._extract_features(lead)
                X.append(features)
                y.append(1 if lead.ai_score > 0.5 else 0)  # Binary classification
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            self.lead_scoring_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.lead_scoring_model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.lead_scoring_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.is_models_trained = True
            
            return {
                "status": "success",
                "accuracy": accuracy,
                "training_samples": len(X_train),
                "test_samples": len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training lead scoring model: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def predict_campaign_performance(self, campaign: Campaign, leads: List[Lead]) -> Dict[str, Any]:
        """Predict campaign performance using AI"""
        try:
            # Calculate predicted metrics
            total_leads = len(leads)
            
            # Get average AI scores
            avg_score = np.mean([lead.ai_score for lead in leads if lead.ai_score])
            
            # Predict open rate based on subject line and lead quality
            subject_score = self._analyze_subject_line(campaign.subject)
            predicted_open_rate = min(0.3 + (avg_score * 0.2) + (subject_score * 0.1), 0.8)
            
            # Predict click rate
            predicted_click_rate = predicted_open_rate * 0.3  # Typical click rate is 30% of open rate
            
            # Predict bounce rate
            predicted_bounce_rate = max(0.05 - (avg_score * 0.02), 0.01)
            
            return {
                "predicted_open_rate": round(predicted_open_rate * 100, 2),
                "predicted_click_rate": round(predicted_click_rate * 100, 2),
                "predicted_bounce_rate": round(predicted_bounce_rate * 100, 2),
                "estimated_opens": int(total_leads * predicted_open_rate),
                "estimated_clicks": int(total_leads * predicted_click_rate),
                "estimated_bounces": int(total_leads * predicted_bounce_rate),
                "confidence": "high" if avg_score > 0.5 else "medium"
            }
            
        except Exception as e:
            logger.error(f"Error predicting campaign performance: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_subject_line(self, subject: str) -> float:
        """Analyze subject line quality"""
        score = 0.0
        
        # Length analysis (optimal: 30-50 characters)
        length = len(subject)
        if 30 <= length <= 50:
            score += 0.3
        elif 20 <= length <= 60:
            score += 0.2
        else:
            score += 0.1
        
        # Word count (optimal: 6-10 words)
        word_count = len(subject.split())
        if 6 <= word_count <= 10:
            score += 0.3
        elif 4 <= word_count <= 12:
            score += 0.2
        else:
            score += 0.1
        
        # Emotional words
        emotional_words = ['urgent', 'exclusive', 'limited', 'free', 'new', 'special', 'important']
        if any(word in subject.lower() for word in emotional_words):
            score += 0.2
        
        # Personalization
        if any(placeholder in subject for placeholder in ['{name}', '{company}', '{first_name}']):
            score += 0.2
        
        return min(score, 1.0)
    
    async def generate_personalized_subject(self, base_subject: str, lead: Lead) -> str:
        """Generate personalized subject line"""
        personalized = base_subject
        
        # Replace placeholders
        placeholders = {
            '{name}': lead.first_name or 'there',
            '{first_name}': lead.first_name or '',
            '{company}': lead.company or 'your company',
            '{industry}': lead.industry or 'your industry'
        }
        
        for placeholder, value in placeholders.items():
            personalized = personalized.replace(placeholder, str(value))
        
        return personalized
    
    async def analyze_email_performance(self, campaign_id: int, db: Session) -> Dict[str, Any]:
        """Analyze email campaign performance using AI"""
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                return {"error": "Campaign not found"}
            
            # Get email data
            emails = db.query(Email).filter(Email.campaign_id == campaign_id).all()
            
            if not emails:
                return {"error": "No emails found for campaign"}
            
            # Calculate performance metrics
            total_sent = len(emails)
            opened = sum(1 for email in emails if email.is_opened)
            clicked = sum(1 for email in emails if email.is_clicked)
            bounced = sum(1 for email in emails if email.is_bounced)
            
            open_rate = (opened / total_sent) * 100 if total_sent > 0 else 0
            click_rate = (clicked / total_sent) * 100 if total_sent > 0 else 0
            bounce_rate = (bounced / total_sent) * 100 if total_sent > 0 else 0
            
            # AI insights
            insights = []
            
            if open_rate < 20:
                insights.append("Low open rate - consider improving subject line")
            elif open_rate > 40:
                insights.append("Excellent open rate - great subject line performance")
            
            if click_rate < 5:
                insights.append("Low click rate - consider improving email content and CTA")
            elif click_rate > 15:
                insights.append("High click rate - excellent content engagement")
            
            if bounce_rate > 5:
                insights.append("High bounce rate - check email list quality")
            
            return {
                "total_sent": total_sent,
                "opened": opened,
                "clicked": clicked,
                "bounced": bounced,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "bounce_rate": round(bounce_rate, 2),
                "insights": insights,
                "performance_score": self._calculate_performance_score(open_rate, click_rate, bounce_rate)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing email performance: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_performance_score(self, open_rate: float, click_rate: float, bounce_rate: float) -> float:
        """Calculate overall performance score"""
        # Weighted score
        score = (open_rate * 0.4) + (click_rate * 0.5) - (bounce_rate * 0.1)
        return max(0, min(100, score))  # Clamp between 0 and 100
