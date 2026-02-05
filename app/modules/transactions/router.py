"""
API Router for Transaction Module
Dev 2: Transaction, Billing & Order Engine
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.dependencies import get_db, get_current_user
from app.modules.auth_user.models import User
from pydantic import BaseModel
from app.modules.transactions.services import (
    ProductService,
    OrderService,
    PaymentService,
    InvoiceService,
    ReportingService
)
from app.modules.transactions.schemas import (
    PricingPlanCreate,
    PricingPlanUpdate,
    TemplateCreate,
    TemplateUpdate,
    OrderCreate,
    OrderCancel
)
from app.modules.transactions.models import OrderStatus, PaymentStatus
from app.modules.transactions import services, models, schemas

from app.core.config import settings


# Create router
router = APIRouter()


# ==================== PRODUCT MANAGEMENT ENDPOINTS ====================

@router.post("/products/pricing-plans", status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_pricing_plan(
    plan: PricingPlanCreate,
    db: Session = Depends(get_db)
):
    """Create a new pricing plan"""
    db_plan = ProductService.create_pricing_plan(db, plan)
    return {
        "id": db_plan.id,
        "name": db_plan.name,
        "category": db_plan.category,
        "description": db_plan.description,
        "price": float(db_plan.price),
        "duration_months": db_plan.duration_months,
        "features": db_plan.features,
        "is_active": db_plan.is_active,
        "created_at": db_plan.created_at
    }


@router.get("/products/pricing-plans", tags=["Products"])
def get_pricing_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get all pricing plans with pagination"""
    plans = ProductService.get_pricing_plans(db, skip, limit, active_only)
    return {
        "total": len(plans),
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "price": float(p.price),
                "duration_months": p.duration_months,
                "features": p.features,
                "is_active": p.is_active,
                "created_at": p.created_at
            }
            for p in plans
        ]
    }


@router.get("/products/pricing-plans/{plan_id}", tags=["Products"])
def get_pricing_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific pricing plan"""
    plan = ProductService.get_pricing_plan(db, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing plan not found"
        )
    return {
        "id": plan.id,
        "name": plan.name,
        "category": plan.category,
        "description": plan.description,
        "price": float(plan.price),
        "duration_months": plan.duration_months,
        "features": plan.features,
        "is_active": plan.is_active,
        "created_at": plan.created_at
    }


@router.put("/products/pricing-plans/{plan_id}", tags=["Products"])
def update_pricing_plan(
    plan_id: int,
    plan: PricingPlanUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing pricing plan"""
    db_plan = ProductService.update_pricing_plan(db, plan_id, plan)
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing plan not found"
        )
    return {
        "id": db_plan.id,
        "name": db_plan.name,
        "category": db_plan.category,
        "description": db_plan.description,
        "price": float(db_plan.price),
        "duration_months": db_plan.duration_months,
        "features": db_plan.features,
        "is_active": db_plan.is_active,
        "updated_at": db_plan.updated_at
    }


@router.delete("/products/pricing-plans/{plan_id}", tags=["Products"])
def delete_pricing_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """Delete a pricing plan (soft delete)"""
    success = ProductService.delete_pricing_plan(db, plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing plan not found"
        )
    return {"message": "Pricing plan deleted successfully"}


@router.post("/products/templates", status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new template"""
    db_template = ProductService.create_template(db, template)
    return {
        "id": db_template.id,
        "name": db_template.name,
        "category": db_template.category,
        "description": db_template.description,
        "preview_image": db_template.preview_image,
        "price_adjustment": float(db_template.price_adjustment),
        "is_active": db_template.is_active,
        "created_at": db_template.created_at
    }


@router.get("/products/templates", tags=["Products"])
def get_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get all templates with pagination"""
    templates = ProductService.get_templates(db, skip, limit, active_only)
    return {
        "total": len(templates),
        "items": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category,
                "description": t.description,
                "preview_image": t.preview_image,
                "price_adjustment": float(t.price_adjustment),
                "is_active": t.is_active,
                "created_at": t.created_at
            }
            for t in templates
        ]
    }


@router.get("/products/templates/{template_id}", tags=["Products"])
def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific template"""
    template = ProductService.get_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return {
        "id": template.id,
        "name": template.name,
        "category": template.category,
        "description": template.description,
        "preview_image": template.preview_image,
        "price_adjustment": float(template.price_adjustment),
        "is_active": template.is_active,
        "created_at": template.created_at
    }


@router.put("/products/templates/{template_id}", tags=["Products"])
def update_template(
    template_id: int,
    template: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing template"""
    db_template = ProductService.update_template(db, template_id, template)
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return {
        "id": db_template.id,
        "name": db_template.name,
        "category": db_template.category,
        "description": db_template.description,
        "preview_image": db_template.preview_image,
        "price_adjustment": float(db_template.price_adjustment),
        "is_active": db_template.is_active,
        "updated_at": db_template.updated_at
    }


@router.delete("/products/templates/{template_id}", tags=["Products"])
def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Delete a template (soft delete)"""
    success = ProductService.delete_template(db, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return {"message": "Template deleted successfully"}


@router.get("/products/subscription-plans", tags=["Products"])
def get_subscription_plans(
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get all subscription plan combinations"""
    plans = ProductService.get_subscription_plans(db, active_only)
    return {
        "total": len(plans),
        "items": plans
    }


# ==================== ORDER ENDPOINTS ====================

# Client-facing order creation with authentication
class OrderCreateClient(BaseModel):
    pricing_plan_id: int
    template_id: Optional[int] = None
    # Project Details
    project_name: Optional[str] = None
    subdomain: Optional[str] = None
    description: Optional[str] = None
    tier: Optional[str] = None

@router.post("/orders/create", status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order_authenticated(
    order_data: OrderCreateClient,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new order for the authenticated user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Create order using OrderCreate schema
    order = schemas.OrderCreate(
        user_id=current_user.id,
        pricing_plan_id=order_data.pricing_plan_id,
        template_id=order_data.template_id,
        project_name=order_data.project_name,
        subdomain=order_data.subdomain,
        description=order_data.description,
        tier=order_data.tier
    )
    
    db_order = OrderService.create_order(db, order)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pricing plan or template"
        )
    
    # Create payment via Midtrans
    try:
        payment = PaymentService.create_payment(db, db_order.id)
        return {
            "order_id": db_order.id,
            "status": db_order.status.value,
            "total_price": float(db_order.total_price),
            "payment_url": payment.get("payment_url") if payment else None
        }
    except Exception as e:
        return {
            "order_id": db_order.id,
            "status": db_order.status.value,
            "total_price": float(db_order.total_price),
            "payment_url": None,
            "error": str(e)
        }

@router.get("/orders/my-orders", tags=["Orders"])
def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all orders for the authenticated user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    orders = OrderService.get_user_orders(db, current_user.id, skip, limit)
    
    return [
        {
            "id": order.id,
            "subscription_plan_id": order.subscription_plan_id,
            "status": order.status.value,
            "total_price": float(order.total_price),
            "created_at": order.created_at,
            "paid_at": order.paid_at
        }
        for order in orders
    ]

@router.post("/orders", status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new order"""
    db_order = OrderService.create_order(db, order)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pricing plan or template"
        )

    from app.modules.transactions.models import OrderItem
    order_items = db.query(OrderItem).filter(OrderItem.order_id == db_order.id).all()


    return {
        "id": db_order.id,
        "user_id": db_order.user_id,
        "subscription_plan_id": db_order.subscription_plan_id,
        "status": db_order.status.value,
        "total_price": float(db_order.total_price),
        "created_at": db_order.created_at,
        "items": [
            {
                "id": item.id,
                "item_type": item.item_type.value,
                "item_name": item.item_name,
                "price": float(item.price)
            }
            for item in order_items
        ]
    }


# ==================== ADMIN ORDER MANAGEMENT ====================

@router.get("/orders/admin/all", tags=["Orders"])
def get_all_orders_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all orders for admin dashboard with filtering"""
    # Only admin can access
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from app.modules.transactions.models import Order, OrderItem, SubscriptionPlan, PricingPlan
    from app.modules.auth_user.models import User as UserModel
    
    query = db.query(Order).order_by(Order.created_at.desc())
    
    # Filter by status if provided
    if status:
        try:
            status_enum = OrderStatus(status)
            query = query.filter(Order.status == status_enum)
        except ValueError:
            pass
    
    orders = query.offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        # Get user info
        user = db.query(UserModel).filter(UserModel.id == order.user_id).first()
        
        # Get plan info
        subscription_plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == order.subscription_plan_id
        ).first()
        
        pricing_plan = None
        if subscription_plan:
            pricing_plan = db.query(PricingPlan).filter(
                PricingPlan.id == subscription_plan.pricing_plan_id
            ).first()
        
        # Get project info
        from app.modules.service_delivery.models import WebsiteInstance
        project = db.query(WebsiteInstance).filter(WebsiteInstance.order_id == order.id).first()
        
        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "user_name": user.name if user else "Unknown",
            "user_email": user.email if user else "Unknown",
            "status": order.status.value,
            "total_price": float(order.total_price),
            "plan_name": pricing_plan.name if pricing_plan else "Unknown",
            "plan_category": pricing_plan.category if pricing_plan else None,
            "created_at": order.created_at,
            "paid_at": order.paid_at,
            "project_id": project.id if project else None,
            "project_stage": project.stage if project else None
        })
    
    # Get total count
    total_query = db.query(Order)
    if status:
        try:
            status_enum = OrderStatus(status)
            total_query = total_query.filter(Order.status == status_enum)
        except ValueError:
            pass
    total_count = total_query.count()
    
    # Get status counts
    pending_count = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    paid_count = db.query(Order).filter(Order.status == OrderStatus.PAID).count()
    cancelled_count = db.query(Order).filter(Order.status == OrderStatus.CANCELLED).count()
    
    return {
        "total": total_count,
        "pending_count": pending_count,
        "paid_count": paid_count,
        "cancelled_count": cancelled_count,
        "items": result
    }


@router.get("/orders", tags=["Orders"])
def get_user_orders(
    user_id: int = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all orders for a user"""
    orders = OrderService.get_user_orders(db, user_id, skip, limit)

    from app.modules.transactions.models import OrderItem, SubscriptionPlan, PricingPlan, Template
    result = []
    for order in orders:
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        
        # specific plan info
        sub_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == order.subscription_plan_id).first()
        pricing_plan_data = None
        template_data = None
        
        if sub_plan:
            p_plan = db.query(PricingPlan).filter(PricingPlan.id == sub_plan.pricing_plan_id).first()
            if p_plan:
                pricing_plan_data = {"name": p_plan.name}
            
            if sub_plan.template_id:
                t_plate = db.query(Template).filter(Template.id == sub_plan.template_id).first()
                if t_plate:
                    template_data = {"name": t_plate.name}

        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "subscription_plan_id": order.subscription_plan_id,
            "status": order.status.value,
            "total_price": float(order.total_price),
            "created_at": order.created_at,
            "paid_at": order.paid_at,
            "pricing_plan": pricing_plan_data,
            "template": template_data,
            "items": [
                {
                    "id": item.id,
                    "item_type": item.item_type.value,
                    "item_name": item.item_name,
                    "price": float(item.price)
                }
                for item in order_items
            ]
        })

    return {
        "total": len(result),
        "items": result
    }


@router.get("/orders/{order_id}", tags=["Orders"])
def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific order"""
    order = OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    from app.modules.transactions.models import OrderItem
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    return {
        "id": order.id,
        "user_id": order.user_id,
        "subscription_plan_id": order.subscription_plan_id,
        "status": order.status.value,
        "total_price": float(order.total_price),
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "paid_at": order.paid_at,
        "items": [
            {
                "id": item.id,
                "item_type": item.item_type.value,
                "item_name": item.item_name,
                "price": float(item.price)
            }
            for item in order_items
        ]
    }


@router.put("/orders/{order_id}/cancel", tags=["Orders"])
def cancel_order(
    order_id: int,
    cancel_data: OrderCancel = None,
    db: Session = Depends(get_db)
):
    """Cancel a pending order"""
    try:
        order = OrderService.cancel_order(db, order_id, cancel_data.reason if cancel_data else None)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        return {
            "id": order.id,
            "status": order.status.value,
            "message": "Order cancelled successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== PAYMENT ENDPOINTS ====================

@router.post("/payments/create", tags=["Payments"])
async def create_payment(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Create a payment link for an order"""
    payment_url = f"{settings.API_V1_STR}/payments" if hasattr(settings, 'API_V1_STR') else "http://localhost:8000"

    try:
        result = await PaymentService.create_payment_link(db, order_id, payment_url)
        return {
            "order_id": order_id,
            "payment_url": result["payment_url"],
            "transaction_id": result["transaction_id"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.post("/payments/webhooks/midtrans", tags=["Payments"])
def midtrans_webhook(
    webhook_data: dict,
    db: Session = Depends(get_db)
):
    """Handle Midtrans webhook notifications"""
    success = PaymentService.handle_webhook(db, webhook_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook data"
        )
    return {"status": "success"}


@router.get("/payments/by-order/{order_id}", tags=["Payments"])
def get_payment_status(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get payment status for an order"""
    payment = PaymentService.get_payment_status(db, order_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


# ==================== SIMULATION PAYMENT ENDPOINTS ====================

class SimulatePaymentRequest(BaseModel):
    action: str  # "pay" or "cancel"
    payment_method: str = "bank_transfer"  # bank_transfer, ewallet, qris

@router.get("/payments/order-details/{order_id}", tags=["Payments"])
def get_order_for_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order details for payment page"""
    order = OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify order belongs to current user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    # Get pricing plan details
    subscription_plan = db.query(models.SubscriptionPlan).filter(
        models.SubscriptionPlan.id == order.subscription_plan_id
    ).first()
    
    pricing_plan = None
    if subscription_plan:
        pricing_plan = db.query(models.PricingPlan).filter(
            models.PricingPlan.id == subscription_plan.pricing_plan_id
        ).first()
    
    return {
        "id": order.id,
        "status": order.status.value,
        "total_price": float(order.total_price),
        "created_at": order.created_at,
        "plan_name": pricing_plan.name if pricing_plan else "Unknown Plan",
        "plan_category": pricing_plan.category if pricing_plan else None,
        "plan_description": pricing_plan.description if pricing_plan else None,
        "duration_months": pricing_plan.duration_months if pricing_plan else 0
    }


@router.post("/payments/simulate/{order_id}", tags=["Payments"])
def simulate_payment(
    order_id: int,
    request: SimulatePaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simulate payment for demo/development - no real payment gateway"""
    order = OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify order belongs to current user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to process this order"
        )
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order already {order.status.value}"
        )
    
    if request.action == "pay":
        # Create payment record
        from datetime import datetime
        import uuid
        
        transaction_id = f"SIM-{uuid.uuid4().hex[:12].upper()}"
        
        # Check if payment record exists
        existing_payment = db.query(models.Payment).filter(
            models.Payment.order_id == order_id
        ).first()
        
        if existing_payment:
            existing_payment.status = PaymentStatus.SUCCESS
            existing_payment.paid_at = datetime.utcnow()
            existing_payment.payment_method = request.payment_method
            existing_payment.transaction_id = transaction_id
        else:
            new_payment = models.Payment(
                order_id=order_id,
                payment_gateway=models.PaymentGateway.MIDTRANS,
                transaction_id=transaction_id,
                amount=order.total_price,
                status=PaymentStatus.SUCCESS,
                payment_method=request.payment_method,
                paid_at=datetime.utcnow()
            )
            db.add(new_payment)
        
        # Mark order as paid
        order.status = OrderStatus.PAID
        order.paid_at = datetime.utcnow()
        db.commit()
        
        # Create project automatically (Dev 3 integration)
        try:
            from app.modules.service_delivery import services as delivery_services
            from app.modules.service_delivery import schemas as delivery_schemas
            
            existing_project = delivery_services.get_instance_by_order(db, order.id)
            if existing_project:
                pass
            else:
                default_subdomain = f"project-{order.id}-{int(datetime.utcnow().timestamp())}"
                project_data = delivery_schemas.WebsiteInstanceCreate(
                    order_id=order.id,
                    user_id=order.user_id,
                    subdomain=default_subdomain
                )
                delivery_services.create_website_instance(
                    db, 
                    project_data,
                    order_id=order.id
                )
        except Exception as e:
            pass
        
        return {
            "success": True,
            "message": "Payment successful",
            "order_id": order_id,
            "status": "paid",
            "transaction_id": transaction_id
        }
    
    elif request.action == "cancel":
        order.status = OrderStatus.CANCELLED
        db.commit()
        
        return {
            "success": True,
            "message": "Order cancelled",
            "order_id": order_id,
            "status": "cancelled"
        }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use 'pay' or 'cancel'"
        )


# ==================== INVOICE ENDPOINTS ====================

@router.get("/invoices/{order_id}", tags=["Invoices"])
def get_invoice(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get/download invoice PDF for an order"""
    try:
        InvoiceService.generate_invoice(db, order_id)
    except Exception:
        pass
    
    invoice = InvoiceService.get_invoice(db, order_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if invoice.pdf_url:
        return FileResponse(
            path=invoice.pdf_url,
            filename=f"{invoice.invoice_number}.pdf",
            media_type="application/pdf"
        )

    return {
        "id": invoice.id,
        "order_id": invoice.order_id,
        "invoice_number": invoice.invoice_number,
        "sent_via_email": invoice.sent_via_email,
        "sent_at": invoice.sent_at,
        "created_at": invoice.created_at
    }


@router.post("/invoices/{order_id}/resend", tags=["Invoices"])
def resend_invoice(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resend invoice to customer email"""
    success = InvoiceService.resend_invoice_email(db, order_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return {"message": "Invoice resent successfully"}


@router.post("/invoices/generate/{order_id}", tags=["Invoices"])
def generate_invoice(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Manually trigger invoice generation for a paid order"""
    try:
        invoice = InvoiceService.generate_invoice(db, order_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or invalid status"
            )
        return {
            "id": invoice.id,
            "order_id": invoice.order_id,
            "invoice_number": invoice.invoice_number,
            "pdf_url": invoice.pdf_url
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoice: {str(e)}"
        )


# ==================== REPORTING ENDPOINTS ====================

@router.get("/reports/mrr", tags=["Reports"])
def get_mrr(db: Session = Depends(get_db)):
    """Get Monthly Recurring Revenue metrics"""
    mrr_data = ReportingService.calculate_mrr(db)
    return mrr_data


@router.get("/reports/conversion-rate", tags=["Reports"])
def get_conversion_rate(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get order to payment conversion rate"""
    return ReportingService.get_conversion_rate(db, start_date, end_date)


@router.get("/reports/revenue", tags=["Reports"])
def get_revenue_by_period(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """Get revenue grouped by day, week, or month"""
    return ReportingService.get_revenue_by_period(db, start_date, end_date, group_by)


@router.get("/reports/top-plans", tags=["Reports"])
def get_top_selling_plans(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top selling pricing plans"""
    return ReportingService.get_top_selling_plans(db, limit)


@router.get("/reports/dashboard", tags=["Reports"])
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Get comprehensive dashboard metrics"""
    return ReportingService.get_dashboard_metrics(db)


@router.get("/reports/activities", tags=["Reports"])
def get_recent_activities(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get recent activities for dashboard feed (orders, projects, tickets)"""
    return ReportingService.get_recent_activities(db, limit)
