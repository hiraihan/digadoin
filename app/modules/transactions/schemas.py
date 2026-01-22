from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

# --- ENUMS ---
class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

# --- PRICING PLANS ---
class PricingPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    duration_months: int = 1
    features: List[str] = []
    is_active: bool = True

class PricingPlanCreate(PricingPlanBase):
    pass

class PricingPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_months: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

class PricingPlanResponse(PricingPlanBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- TEMPLATES ---
class TemplateBase(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    preview_image: Optional[str] = None
    price_adjustment: float = 0
    is_active: bool = True

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    preview_image: Optional[str] = None
    price_adjustment: Optional[float] = None
    is_active: Optional[bool] = None

class TemplateResponse(TemplateBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- ORDERS ---
class OrderCreate(BaseModel):
    user_id: int
    pricing_plan_id: int
    template_id: Optional[int] = None
    custom_price: Optional[float] = None

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_price: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- PAYMENTS ---
class PaymentLinkResponse(BaseModel):
    payment_url: str
    transaction_id: str