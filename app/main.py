from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base

from app.modules.auth_user import router as auth_router
from app.modules.cms.router import router as cms_router
from app.modules.transactions.router import router as transaction_router
from app.modules.service_delivery import router as delivery_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend API untuk WaaS Platform (Order, Invoice, Project Tracking)",
    version="1.0.0",
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://digadoin.vercel.app",
]

import os
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    # Auto-remove trailing slash if user accidentally added it
    frontend_url = frontend_url.rstrip("/")
    origins.append(frontend_url)

print(f"DEBUG: Allowed CORS Origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Welcome to WaaS API Platform",
        "status": "running",
        "docs_url": "/docs"
    }

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(cms_router, prefix="/api/v1/cms", tags=["CMS"])
app.include_router(transaction_router, prefix="/api/v1", tags=["Transactions"])
app.include_router(delivery_router.router, prefix="/api/v1/delivery", tags=["Service Delivery & Support"])
