from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base

# --- Import Router Modul (Uncomment saat modul sudah dibuat developer) ---
from app.modules.auth_user import router as auth_router
from app.modules.cms.router import router as cms_router

# from app.modules.transactions import router as transaction_router
# from app.modules.service_delivery import router as delivery_router

# 1. Create Tables (Otomatis buat tabel jika belum ada saat restart)
# Idealnya pakai Alembic untuk production, tapi ini membantu untuk MVP/Dev
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend API untuk WaaS Platform (Order, Invoice, Project Tracking)",
    version="1.0.0",
)

# 2. Setup CORS (PENTING untuk Frontend Next.js)
# Izinkan akses dari localhost frontend (misal port 3000)
origins = [
    "http://localhost",
    "http://localhost:3000", # Next.js local
    "https://waas-frontend.vercel.app", # Contoh domain production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Izinkan semua method (GET, POST, PUT, DELETE)
    allow_headers=["*"],
)

# 3. Health Check Endpoint (Untuk memastikan server jalan)
@app.get("/")
def root():
    return {
        "message": "Welcome to WaaS API Platform",
        "status": "running",
        "docs_url": "/docs"
    }

# 4. Include Routers (Tempat menggabungkan kerjaan 3 Developer)
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(cms_router, prefix="/api/v1/cms", tags=["CMS"])


# app.include_router(transaction_router.router, prefix="/api/v1/orders", tags=["Orders"])
# app.include_router(delivery_router.router, prefix="/api/v1/projects", tags=["Project Delivery"])