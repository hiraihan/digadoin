from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.dependencies import get_db, get_current_user
from app.modules.auth_user.models import User
from . import models, schemas, services


router = APIRouter()

# ==========================================
# CLIENT AREA (Diakses oleh Customer)
# ==========================================

@router.get("/my-projects", response_model=List[schemas.WebsiteInstanceResponse])
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects owned by the current authenticated user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    projects = services.get_client_dashboard(db, current_user.id)
    return projects


@router.get("/projects/{project_id}", response_model=schemas.WebsiteInstanceResponse)
def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project detail (Admin or Owner)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    project = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permissions (Admin or Owner)
    if current_user.role != "admin" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return project


@router.post("/tickets", response_model=schemas.TicketResponse)
def create_support_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new support ticket for the current user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    new_ticket = models.Ticket(
        user_id=current_user.id,
        subject=ticket.subject,
        priority=ticket.priority,
        request_type=ticket.request_type,
        project_id=ticket.project_id
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    first_message = models.TicketMessage(
        ticket_id=new_ticket.id,
        sender_id=current_user.id,
        message=ticket.message
    )
    db.add(first_message)
    db.commit()
    
    return new_ticket


@router.get("/tickets", response_model=List[schemas.TicketResponse])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tickets for current user (or all tickets if admin)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Admin can see all tickets, regular users only see their own
    if current_user.role == "admin":
        tickets = db.query(models.Ticket).order_by(models.Ticket.created_at.desc()).all()
    else:
        tickets = db.query(models.Ticket).filter(models.Ticket.user_id == current_user.id).order_by(models.Ticket.created_at.desc()).all()
    return tickets


@router.get("/tickets/all", response_model=List[schemas.TicketResponse])
def get_all_tickets_admin(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tickets (Admin only)"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(models.Ticket)
    
    if status:
        query = query.filter(models.Ticket.status == status)
    
    tickets = query.options(joinedload(models.Ticket.messages)).order_by(models.Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return tickets


@router.get("/tickets/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket_detail(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ticket detail with all messages"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Only allow owner or admin to view ticket
    if ticket.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
    
    return ticket


@router.post("/tickets/{ticket_id}/reply", response_model=schemas.TicketMessageResponse)
def reply_to_ticket(
    ticket_id: int,
    reply: schemas.TicketReply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a reply to an existing ticket"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Only allow owner or admin to reply
    if ticket.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to reply to this ticket")
    
    new_message = models.TicketMessage(
        ticket_id=ticket_id,
        sender_id=current_user.id,
        message=reply.message
    )
    db.add(new_message)
    
    # Update ticket status based on who replied
    if current_user.role == "admin":
        ticket.status = "answered"
    else:
        ticket.status = "open"  # Customer replied, needs attention
    
    db.commit()
    db.refresh(new_message)
    
    return new_message

# ==========================================
# DEVELOPER / SYSTEM AREA (Internal Trigger)
# ==========================================

@router.post("/internal/init-project", status_code=status.HTTP_201_CREATED, response_model=schemas.WebsiteInstanceResponse)
def trigger_project_creation(
    payload: schemas.WebsiteInstanceCreate, 
    db: Session = Depends(get_db)
):
    """
    Endpoint ini ditembak oleh Module 'Transactions' (Dev 2) 
    secara otomatis setelah pembayaran sukses.
    """
    return services.create_website_instance(db, payload)

@router.put("/projects/{project_id}/domain")
async def update_custom_domain(
    project_id: int, 
    domain_data: schemas.DomainUpdate, 
    db: Session = Depends(get_db)
):
    """
    Client request custom domain -> System otomatis set ke Cloudflare
    """
    project = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await services.register_domain_on_cloudflare(project.subdomain, "192.168.1.100")
    
    project.custom_domain = domain_data.custom_domain
    db.commit()
    
    return {"status": "Domain updated and propagating"}

# ==========================================
# ADMIN AREA (Admin only)
# ==========================================

@router.get("/projects", response_model=List[schemas.WebsiteInstanceResponse])
def get_all_projects(
    skip: int = 0,
    limit: int = 100,
    stage: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects (Admin only)"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(models.WebsiteInstance)
    
    if stage:
        query = query.filter(models.WebsiteInstance.stage == stage)
    
    projects = query.order_by(models.WebsiteInstance.created_at.desc()).offset(skip).limit(limit).all()
    return projects


@router.put("/projects/{project_id}/stage")
def update_project_stage(
    project_id: int, 
    stage_data: schemas.ProjectStageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin updates project stage.
    Valid stages: pending, development, review, live
    """
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    project = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    valid_stages = ["pending", "development", "review", "live", "cancelled"]
    if stage_data.stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {valid_stages}")
    
    project.stage = stage_data.stage
    db.commit()
    db.refresh(project)
    
    db.commit()
    db.refresh(project)

    try:
        from app.modules.auth_user import services as auth_services
        if project.user_id:
            auth_services.create_notification(
                db,
                project.user_id,
                "project",
                f"Project Update: {project.subdomain}",
                f"Status changed to {stage_data.stage.upper()}",
                f"/dashboard/projects/{project.id}"
            )
    except Exception as e:
        print(f"[NOTIF ERROR] Failed to notify client: {e}")
    
    return {
        "status": "success",
        "message": f"Project stage updated to '{stage_data.stage}'",
        "project_id": project.id,
        "new_stage": project.stage
    }