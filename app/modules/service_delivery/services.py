import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, schemas

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
def create_website_instance(db: Session, data: schemas.WebsiteInstanceCreate):
    # 1. Cek apakah subdomain sudah dipakai
    existing = db.query(models.WebsiteInstance).filter(models.WebsiteInstance.subdomain == data.subdomain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")

    # 2. Buat Instance Baru
    new_instance = models.WebsiteInstance(
        order_id=data.order_id,
        user_id=data.user_id,
        subdomain=data.subdomain,
        stage=models.ProjectStage.PENDING
    )
    db.add(new_instance)
    db.commit()
    db.refresh(new_instance)

    # 3. Generate Default Milestones (Otomatis)
    default_tasks = ["Order Verified", "Server Provisioning", "Template Installation", "Content Upload", "Domain Setup", "Live"]
    for task in default_tasks:
        milestone = models.ProjectMilestone(website_instance_id=new_instance.id, task_name=task)
        db.add(milestone)
    
    db.commit()
    return new_instance

def get_client_dashboard(db: Session, user_id: int):
    return db.query(models.WebsiteInstance).filter(models.WebsiteInstance.user_id == user_id).all()