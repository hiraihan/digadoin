from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .models import ProjectStage, TicketStatus

# --- Schemas untuk Website Project ---
class MilestoneBase(BaseModel):
    task_name: str
    is_completed: bool

class MilestoneResponse(MilestoneBase):
    id: int
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class WebsiteInstanceCreate(BaseModel):
    order_id: Optional[int] = None  # Optional for direct creation
    user_id: int
    subdomain: str

class WebsiteInstanceResponse(BaseModel):
    id: int
    order_id: Optional[int] = None  # Optional for direct creation
    user_id: int
    name: Optional[str] = None
    subdomain: str
    custom_domain: Optional[str] = None
    tier: Optional[str] = None
    description: Optional[str] = None
    stage: str
    display_status: Optional[str] = "Draft" # active, draft, expired, suspended
    total_value: Optional[float] = 0.0

    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Schemas untuk Ticket ---
class TicketCreate(BaseModel):
    subject: str
    message: str # Pesan pertama saat buat tiket
    priority: str = "medium"
    request_type: str = "other"
    project_id: Optional[int] = None

class TicketMessageResponse(BaseModel):
    sender_id: int
    message: str
    created_at: datetime

class TicketResponse(BaseModel):
    id: int
    user_id: int
    subject: str
    status: str
    priority: str
    request_type: Optional[str] = None
    project_id: Optional[int] = None
    created_at: datetime
    messages: List[TicketMessageResponse] = []

    class Config:
        from_attributes = True

# --- Schema untuk Update Domain (Integrasi Cloudflare) ---
class DomainUpdate(BaseModel):
    custom_domain: str

# --- Schema untuk Reply Ticket ---
class TicketReply(BaseModel):
    message: str

# --- Schema for Direct Project Creation ---
class ProjectCreate(BaseModel):
    subdomain: str
    name: Optional[str] = None
    tier: Optional[str] = None
    description: Optional[str] = None

# --- Schema for Admin to Update Project Stage ---
class ProjectStageUpdate(BaseModel):
    stage: str  # pending, development, review, live