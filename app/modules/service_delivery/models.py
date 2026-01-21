from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

# Enum untuk status agar konsisten
class ProjectStage(str, enum.Enum):
    PENDING = "pending"
    DEVELOPMENT = "development"
    REVIEW = "review"
    LIVE = "live"

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"

class WebsiteInstance(Base):
    __tablename__ = "website_instances"

    id = Column(Integer, primary_key=True, index=True)
    # Relasi ke modul Dev 2 (Order) & Dev 1 (User)
    order_id = Column(Integer, index=True, nullable=False) 
    user_id = Column(Integer, index=True, nullable=False) 
    
    subdomain = Column(String, unique=True, index=True) # misal: toko-budi.waas.com
    custom_domain = Column(String, nullable=True)       # misal: www.tokobudi.com
    server_ip = Column(String, nullable=True)           # IP tempat deploy
    
    stage = Column(String, default=ProjectStage.PENDING) 
    repo_url = Column(String, nullable=True)            # Link Git repo user
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relasi ke Milestone
    milestones = relationship("ProjectMilestone", back_populates="instance")

class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    website_instance_id = Column(Integer, ForeignKey("website_instances.id"))
    
    task_name = Column(String, nullable=False)   # Misal: "Setup Server", "Install Theme"
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    instance = relationship("WebsiteInstance", back_populates="milestones")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # Client yang buat tiket
    
    subject = Column(String, nullable=False)
    priority = Column(String, default="medium") # low, medium, high
    status = Column(String, default=TicketStatus.OPEN)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    messages = relationship("TicketMessage", back_populates="ticket")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    sender_id = Column(Integer) # ID User pengirim (bisa admin atau client)
    
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ticket = relationship("Ticket", back_populates="messages")