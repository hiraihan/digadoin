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
    order_id: int
    user_id: int
    subdomain: str

class WebsiteInstanceResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    subdomain: str       # <--- PASTIKAN BARIS INI ADA
    custom_domain: Optional[str] = None
    stage: str
    created_at: datetime
    # milestones: List[MilestoneResponse] = [] # Uncomment jika relasi sudah diload di service
    
    class Config:
        from_attributes = True

# --- Schemas untuk Ticket ---
class TicketCreate(BaseModel):
    subject: str
    message: str # Pesan pertama saat buat tiket
    priority: str = "medium"

class TicketMessageResponse(BaseModel):
    sender_id: int
    message: str
    created_at: datetime

class TicketResponse(BaseModel):
    id: int
    subject: str
    status: str
    messages: List[TicketMessageResponse] = []

    class Config:
        from_attributes = True

# --- Schema untuk Update Domain (Integrasi Cloudflare) ---
class DomainUpdate(BaseModel):
    custom_domain: str