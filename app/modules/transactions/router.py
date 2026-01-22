"""
API Router for Transaction Module
Dev 2: Transaction, Billing & Order Engine
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.dependencies import get_db
from app.modules.transactions.services import (
    ProductService,
    OrderService,
    PaymentService,
    InvoiceService,
    ReportingService,
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


@router.get("/orders", tags=["Orders"])
def get_user_orders(
    user_id: int = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all orders for a user"""
    orders = OrderService.get_user_orders(db, user_id, skip, limit)

    from app.modules.transactions.models import OrderItem
    result = []
    for order in orders:
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "subscription_plan_id": order.subscription_plan_id,
            "status": order.status.value,
            "total_price": float(order.total_price),
            "created_at": order.created_at,
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
    # TODO: Verify signature key from Midtrans
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


# ==================== INVOICE ENDPOINTS ====================

@router.get("/invoices/{order_id}", tags=["Invoices"])
def get_invoice(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get/download invoice PDF for an order"""
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
