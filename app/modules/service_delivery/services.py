import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, schemas
from app.modules.transactions.models import Order

# --- Logic 1: Cloudflare Integration (Simulasi) ---
async def register_domain_on_cloudflare(subdomain: str, ip_address: str):
    """
    Simulasi hit ke Cloudflare API untuk add DNS Record.
    """
    return True

# --- Logic 2: Notifikasi (Simulasi) ---
def send_notification(user_id: int, message: str, channel: str = "email"):
    """
    Simulasi kirim WA atau Email.
    """
    pass

# --- Logic 3: Project Management ---
def create_website_instance(
    db: Session, 
    data: schemas.WebsiteInstanceCreate,
    name: str = None,
    tier: str = None,
    description: str = None,
    order_id: int = None
):
    existing = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.subdomain == data.subdomain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")

    # Use explicit order_id if provided, otherwise fallback to data.order_id
    final_order_id = order_id if order_id is not None else data.order_id

    new_instance = models.WebsiteInstance(
        order_id=final_order_id,
        user_id=data.user_id,
        subdomain=data.subdomain,
        name=name or data.subdomain,  # Default name to subdomain if not provided
        tier=tier,
        description=description,
        stage=models.ProjectStage.PENDING
    )
    db.add(new_instance)
    db.commit()
    db.refresh(new_instance)

    default_tasks = ["Order Verified", "Server Provisioning", "Template Installation", "Content Upload", "Domain Setup", "Live"]
    for task in default_tasks:
        milestone = models.ProjectMilestone(website_instance_id=new_instance.id, task_name=task)
        db.add(milestone)
    
    db.commit()
    return new_instance

def get_client_dashboard(db: Session, user_id: int):
    projects = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.user_id == user_id).all()
    
    for p in projects:
        p.total_value = 0.0
        p.display_status = "Draft"
        
        if p.order_id:
            order = db.query(Order).filter(Order.id == p.order_id).first()
            if order:
                p.total_value = float(order.total_price or 0)
                
                if p.stage == "live":
                    p.display_status = "Active"
                elif order.status == "paid":
                    # If paid but not live, check stage
                    if p.stage == "pending": p.display_status = "Queue"
                    elif p.stage == "development": p.display_status = "In Dev"
                    else: p.display_status = "In Progress"
                elif order.status == "pending":
                    p.display_status = "Unpaid"
                elif order.status == "cancelled":
                    p.display_status = "Cancelled"
                    p.stage = "cancelled"
                
    return projects

def get_instance_by_order(db: Session, order_id: int):
    instance = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.order_id == order_id).first()
    return instance