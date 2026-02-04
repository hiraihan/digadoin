import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, schemas
from app.modules.transactions.models import Order

# --- Logic 1: Cloudflare Integration (Simulasi) ---
async def register_domain_on_cloudflare(subdomain: str, ip_address: str):
    """
    Simulasi hit ke Cloudflare API untuk add DNS Record.
    Nanti diganti dengan Real API Call menggunakan CLOUDFLARE_API_TOKEN dari config.
    """
    print(f"[CLOUDFLARE] Adding A Record: {subdomain} -> {ip_address}")
    # async with httpx.AsyncClient() as client:
    #     response = await client.post("https://api.cloudflare.com/...", ...)
    return True

# --- Logic 2: Notifikasi (Simulasi) ---
def send_notification(user_id: int, message: str, channel: str = "email"):
    """
    Simulasi kirim WA atau Email.
    """
    print(f"[NOTIF-{channel.upper()}] To User {user_id}: {message}")

# --- Logic 3: Project Management ---
def create_website_instance(
    db: Session, 
    data: schemas.WebsiteInstanceCreate,
    name: str = None,
    tier: str = None,
    description: str = None,
    order_id: int = None
):
    # 1. Cek apakah subdomain sudah dipakai
    existing = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.subdomain == data.subdomain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")

    # Use explicit order_id if provided, otherwise fallback to data.order_id
    final_order_id = order_id if order_id is not None else data.order_id
    print(f"[DEBUG] Creating WebsiteInstance. Order ID: {final_order_id}, Subdomain: {data.subdomain}")

    # 2. Buat Instance Baru dengan semua field
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
    print(f"[DEBUG] Created WebsiteInstance ID: {new_instance.id} with Order ID: {new_instance.order_id}")

    # 3. Generate Default Milestones (Otomatis)
    default_tasks = ["Order Verified", "Server Provisioning", "Template Installation", "Content Upload", "Domain Setup", "Live"]
    for task in default_tasks:
        milestone = models.ProjectMilestone(website_instance_id=new_instance.id, task_name=task)
        db.add(milestone)
    
    db.commit()
    return new_instance

def get_client_dashboard(db: Session, user_id: int):
    projects = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.user_id == user_id).all()
    
    # Enrich with Order Data manually (since no ORM relationship defined across modules)
    for p in projects:
        p.total_value = 0.0
        p.display_status = "Draft"
        
        if p.order_id:
            order = db.query(Order).filter(Order.id == p.order_id).first()
            if order:
                p.total_value = float(order.total_price or 0)
                
                # Logic Status Display
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
                    # Fix Inconsistency: If order is cancelled, force stage to appear cancelled too
                    p.stage = "cancelled"
                
    return projects

def get_instance_by_order(db: Session, order_id: int):
    print(f"[DEBUG] checking instance for order_id: {order_id}")
    instance = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.order_id == order_id).first()
    print(f"[DEBUG] Found instance: {instance.id if instance else 'None'}")
    return instance