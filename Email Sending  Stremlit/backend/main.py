"""
FastAPI Backend for LeadAI Pro
AI-powered lead management and email marketing platform
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
from datetime import datetime, timedelta
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and models
from .database import get_db, engine, SessionLocal
from .models import Base, User, Lead, Campaign, Email, Analytics
from .schemas import (
    UserCreate, UserLogin, UserResponse,
    LeadCreate, LeadResponse, LeadUpdate,
    CampaignCreate, CampaignResponse,
    EmailCreate, EmailResponse,
    AnalyticsResponse
)
from .auth import create_access_token, verify_token, get_password_hash, verify_password
from .services.lead_service import LeadService
from .services.campaign_service import CampaignService
from .services.email_service import EmailService
from .services.ai_service import AIService
from .services.analytics_service import AnalyticsService

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="LeadAI Pro API",
    description="AI-powered lead management and email marketing platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

# Initialize services
lead_service = LeadService()
campaign_service = CampaignService()
email_service = EmailService()
ai_service = AIService()
analytics_service = AnalyticsService()

# WebSocket for live analytics
clients = set()

@app.websocket("/ws/metrics")
async def websocket_metrics(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            # Periodically push overall metrics
            db = SessionLocal()
            try:
                total_leads = db.query(Lead).count()
                total_campaigns = db.query(Campaign).count()
                total_sent = db.query(Email).filter(Email.sent_at != None).count()
                total_opened = db.query(Email).filter(Email.opened_at != None).count()
                total_clicked = db.query(Email).filter(Email.clicked_at != None).count()
                payload = {
                    "type": "metrics",
                    "lead_count": total_leads,
                    "campaign_count": total_campaigns,
                    "sent_emails": total_sent,
                    "opened_emails": total_opened,
                    "clicked_emails": total_clicked,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await ws.send_json(payload)
            finally:
                db.close()
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            clients.discard(ws)
        except Exception:
            pass

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LeadAI Pro API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat()
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        subscription_plan=user_data.subscription_plan
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)

@app.post("/auth/login")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

# Lead management endpoints
@app.post("/leads/upload", response_model=List[LeadResponse])
async def upload_leads(
    file_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process CSV leads"""
    try:
        leads = await lead_service.process_csv_leads(file_data, current_user.id, db)
        return [LeadResponse.from_orm(lead) for lead in leads]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing leads: {str(e)}"
        )

@app.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's leads"""
    leads = db.query(Lead).filter(Lead.user_id == current_user.id).offset(skip).limit(limit).all()
    return [LeadResponse.from_orm(lead) for lead in leads]

@app.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a lead"""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Update lead data
    for field, value in lead_data.dict(exclude_unset=True).items():
        setattr(lead, field, value)
    
    db.commit()
    db.refresh(lead)
    
    return LeadResponse.from_orm(lead)

@app.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a lead"""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    db.delete(lead)
    db.commit()
    
    return {"message": "Lead deleted successfully"}

# Campaign management endpoints
@app.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new email campaign"""
    campaign = await campaign_service.create_campaign(campaign_data, current_user.id, db)
    return CampaignResponse.from_orm(campaign)

@app.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's campaigns"""
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()
    return [CampaignResponse.from_orm(campaign) for campaign in campaigns]

@app.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Queue campaign for sending
    await email_service.queue_campaign(campaign, db)
    
    return {"message": "Campaign queued for sending"}

# AI endpoints
@app.post("/ai/score-leads")
async def score_leads(
    lead_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Score leads using AI"""
    leads = db.query(Lead).filter(
        Lead.id.in_(lead_ids),
        Lead.user_id == current_user.id
    ).all()
    
    if not leads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No leads found"
        )
    
    scored_leads = await ai_service.score_leads(leads)
    
    # Update lead scores in database
    for lead, score in scored_leads:
        lead.ai_score = score
        db.commit()
    
    return {"message": "Leads scored successfully", "scores": scored_leads}

@app.post("/ai/generate-email")
async def generate_email(
    prompt: str,
    current_user: User = Depends(get_current_user)
):
    """Generate email content using AI"""
    try:
        email_content = await ai_service.generate_email_content(prompt)
        return {"content": email_content}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating email: {str(e)}"
        )

# Analytics endpoints
@app.get("/analytics/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics"""
    analytics = await analytics_service.get_dashboard_analytics(current_user.id, db)
    return analytics

@app.get("/analytics/campaigns/{campaign_id}")
async def get_campaign_analytics(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign-specific analytics"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    analytics = await analytics_service.get_campaign_analytics(campaign_id, db)
    return analytics

# Email tracking endpoints
@app.get("/emails/{email_id}/track")
async def track_email_open(
    email_id: int,
    db: Session = Depends(get_db)
):
    """Track email open"""
    email = db.query(Email).filter(Email.id == email_id).first()
    if email:
        email.opened_at = datetime.utcnow()
        email.is_opened = True
        db.commit()
    
    return {"message": "Email opened tracked"}

# Generic webhook endpoint for external events
@app.post("/webhook")
async def webhook_handler(event_data: dict):
    """Generic webhook for external events"""
    try:
        # Log the event (you can extend this to update counters)
        print(f"Webhook received: {event_data}")
        
        # Example: increment counters based on event type
        event_type = event_data.get("type", "")
        if event_type == "email_sent":
            # This would trigger a WebSocket update
            pass
        elif event_type == "email_opened":
            # This would trigger a WebSocket update
            pass
        elif event_type == "email_clicked":
            # This would trigger a WebSocket update
            pass
            
        return {"status": "success", "message": "Event processed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/emails/{email_id}/click")
async def track_email_click(
    email_id: int,
    link: str,
    db: Session = Depends(get_db)
):
    """Track email click"""
    email = db.query(Email).filter(Email.id == email_id).first()
    if email:
        email.clicked_at = datetime.utcnow()
        email.is_clicked = True
        email.clicked_link = link
        db.commit()
    
    return {"message": "Email click tracked"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
