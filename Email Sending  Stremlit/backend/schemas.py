"""
Pydantic schemas for request/response models
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CLIENT = "client"

class SubscriptionPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.CLIENT
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Lead schemas
class LeadBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    source: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[LeadStatus] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class LeadResponse(LeadBase):
    id: int
    user_id: int
    ai_score: float
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Campaign schemas
class CampaignBase(BaseModel):
    name: str
    subject: str
    content: str
    template_type: str = "newsletter"
    scheduled_at: Optional[datetime] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignResponse(CampaignBase):
    id: int
    user_id: int
    status: CampaignStatus
    sent_at: Optional[datetime]
    total_recipients: int
    opened_count: int
    clicked_count: int
    bounce_count: int
    unsubscribe_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Email schemas
class EmailBase(BaseModel):
    recipient_email: EmailStr
    subject: str
    content: str
    personalized_content: Optional[str] = None

class EmailCreate(EmailBase):
    campaign_id: int
    lead_id: int

class EmailResponse(EmailBase):
    id: int
    campaign_id: int
    lead_id: int
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    is_opened: bool
    is_clicked: bool
    clicked_link: Optional[str]
    is_bounced: bool
    is_unsubscribed: bool
    bounce_reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Analytics schemas
class AnalyticsResponse(BaseModel):
    total_leads: int
    total_campaigns: int
    total_emails_sent: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    unsubscribe_rate: float
    revenue: float
    top_performing_campaigns: List[Dict[str, Any]]
    lead_quality_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

# AI schemas
class AIScoreRequest(BaseModel):
    lead_ids: List[int]

class AIScoreResponse(BaseModel):
    lead_id: int
    score: float
    factors: Dict[str, Any]

class EmailGenerationRequest(BaseModel):
    prompt: str
    tone: Optional[str] = "professional"
    length: Optional[str] = "medium"
    include_cta: bool = True

class EmailGenerationResponse(BaseModel):
    subject: str
    content: str
    suggestions: List[str]

# File upload schemas
class CSVUploadResponse(BaseModel):
    total_rows: int
    processed_rows: int
    errors: List[str]
    leads: List[LeadResponse]

# Notification schemas
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    action_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard schemas
class DashboardMetrics(BaseModel):
    total_leads: int
    active_campaigns: int
    emails_sent_today: int
    open_rate: float
    click_rate: float
    conversion_rate: float
    revenue: float

class CampaignMetrics(BaseModel):
    campaign_id: int
    campaign_name: str
    total_recipients: int
    opened_count: int
    clicked_count: int
    bounce_count: int
    unsubscribe_count: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    unsubscribe_rate: float

# Search and filter schemas
class LeadSearchRequest(BaseModel):
    query: Optional[str] = None
    status: Optional[LeadStatus] = None
    industry: Optional[str] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    limit: int = 50

class LeadSearchResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    limit: int
    total_pages: int
