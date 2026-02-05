from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

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
    order_id = Column(Integer, index=True, nullable=True)
    user_id = Column(Integer, index=True, nullable=False) 
    
    name = Column(String, nullable=True)
    subdomain = Column(String, unique=True, index=True)
    custom_domain = Column(String, nullable=True)
    tier = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    server_ip = Column(String, nullable=True)
    
    stage = Column(String, default=ProjectStage.PENDING) 
    repo_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    milestones = relationship("ProjectMilestone", back_populates="instance")

class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    website_instance_id = Column(Integer, ForeignKey("website_instances.id"))
    
    task_name = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    instance = relationship("WebsiteInstance", back_populates="milestones")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    
    subject = Column(String, nullable=False)
    priority = Column(String, default="medium")
    status = Column(String, default=TicketStatus.OPEN)
    
    request_type = Column(String, default="other")
    project_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    messages = relationship("TicketMessage", back_populates="ticket")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    sender_id = Column(Integer)
    
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ticket = relationship("Ticket", back_populates="messages")