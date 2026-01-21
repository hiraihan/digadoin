from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user
from . import models, schemas, services

router = APIRouter()

# ==========================================
# CLIENT AREA (Diakses oleh Customer)
# ==========================================

@router.get("/my-projects", response_model=List[schemas.WebsiteInstanceResponse])
def get_my_projects(
    db: Session = Depends(get_db),
    current_user_token: str = Depends(get_current_user) # Nanti ini return user object
):
    # TODO: Ambil user_id asli dari token (sementara hardcode 1 untuk dev)
    user_id = 1 
    projects = services.get_client_dashboard(db, user_id)
    return projects

@router.post("/tickets", response_model=schemas.TicketResponse)
def create_support_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user_token: str = Depends(get_current_user)
):
    user_id = 1 # TODO: Ambil dari token
    
    # 1. Buat Header Tiket
    new_ticket = models.Ticket(
        user_id=user_id,
        subject=ticket.subject,
        priority=ticket.priority
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # 2. Masukkan Pesan Pertama
    first_message = models.TicketMessage(
        ticket_id=new_ticket.id,
        sender_id=user_id,
        message=ticket.message
    )
    db.add(first_message)
    db.commit()
    
    return new_ticket

# ==========================================
# DEVELOPER / SYSTEM AREA (Internal Trigger)
# ==========================================

@router.post("/internal/init-project", status_code=status.HTTP_201_CREATED)
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
    
    # Trigger Cloudflare Logic
    await services.register_domain_on_cloudflare(project.subdomain, "192.168.1.100")
    
    project.custom_domain = domain_data.custom_domain
    db.commit()
    
    return {"status": "Domain updated and propagating"}