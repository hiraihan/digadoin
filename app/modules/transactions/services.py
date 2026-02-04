"""
Business Logic Services for Transaction Module
Dev 2: Transaction, Billing & Order Engine
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, and_, or_
from decimal import Decimal
import httpx
import os
import base64
from pathlib import Path

from app.modules.transactions.models import (
    PricingPlan, Template, SubscriptionPlan, Order, OrderItem,
    Payment, Invoice, OrderStatus, PaymentStatus, PaymentGateway, OrderItemType
)

# [REVISION] Import Dev 3 Modules for Project Automation
# Moved to local scope to prevent circular imports
# from app.modules.service_delivery import services as delivery_services
# from app.modules.service_delivery import schemas as delivery_schemas

# ==================== PYDANTIC SCHEMAS ====================

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime


class PricingPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    duration_months: int = 1
    features: Optional[List[str]] = None
    is_active: bool = True


class PricingPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_months: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TemplateCreate(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    preview_image: Optional[str] = None
    price_adjustment: float = 0
    is_active: bool = True


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    preview_image: Optional[str] = None
    price_adjustment: Optional[float] = None
    is_active: Optional[bool] = None


class OrderCreate(BaseModel):
    user_id: int
    pricing_plan_id: int
    template_id: Optional[int] = None
    custom_price: Optional[float] = None


class OrderCancel(BaseModel):
    reason: Optional[str] = None


# ==================== PRODUCT SERVICE ====================

class ProductService:
    """Service for managing Pricing Plans, Templates, and Subscription Plans"""

    @staticmethod
    def create_pricing_plan(db: Session, plan_data: PricingPlanCreate) -> PricingPlan:
        """Create a new pricing plan"""
        db_plan = PricingPlan(
            name=plan_data.name,
            description=plan_data.description,
            price=plan_data.price,
            duration_months=plan_data.duration_months,
            features=plan_data.features or [],
            is_active=plan_data.is_active
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return db_plan

    @staticmethod
    def get_pricing_plans(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[PricingPlan]:
        """Get all pricing plans with optional filtering"""
        query = db.query(PricingPlan)
        if active_only:
            query = query.filter(PricingPlan.is_active == True)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_pricing_plan(db: Session, plan_id: int) -> Optional[PricingPlan]:
        """Get a specific pricing plan by ID"""
        return db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()

    @staticmethod
    def update_pricing_plan(db: Session, plan_id: int, plan_data: PricingPlanUpdate) -> Optional[PricingPlan]:
        """Update an existing pricing plan"""
        db_plan = db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()
        if not db_plan:
            return None

        update_data = plan_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_plan, field, value)

        db.commit()
        db.refresh(db_plan)
        return db_plan

    @staticmethod
    def delete_pricing_plan(db: Session, plan_id: int) -> bool:
        """Delete a pricing plan (hard delete)"""
        db_plan = db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()
        if not db_plan:
            return False
        db.delete(db_plan)
        db.commit()
        return True

    @staticmethod
    def create_template(db: Session, template_data: TemplateCreate) -> Template:
        """Create a new template"""
        db_template = Template(
            name=template_data.name,
            category=template_data.category,
            description=template_data.description,
            preview_image=template_data.preview_image,
            repo_url=template_data.repo_url,
            price_adjustment=template_data.price_adjustment,
            is_active=template_data.is_active
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def get_templates(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Template]:
        """Get all templates with optional filtering"""
        query = db.query(Template)
        if active_only:
            query = query.filter(Template.is_active == True)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[Template]:
        """Get a specific template by ID"""
        return db.query(Template).filter(Template.id == template_id).first()

    @staticmethod
    def update_template(db: Session, template_id: int, template_data: TemplateUpdate) -> Optional[Template]:
        """Update an existing template"""
        db_template = db.query(Template).filter(Template.id == template_id).first()
        if not db_template:
            return None

        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)

        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        """Delete a template (hard delete)"""
        db_template = db.query(Template).filter(Template.id == template_id).first()
        if not db_template:
            return False
        db.delete(db_template)
        db.commit()
        return True

    @staticmethod
    def get_subscription_plans(db: Session, active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all subscription plan combinations"""
        query = db.query(SubscriptionPlan, PricingPlan, Template).join(
            PricingPlan, SubscriptionPlan.pricing_plan_id == PricingPlan.id
        ).outerjoin(
            Template, SubscriptionPlan.template_id == Template.id
        )

        if active_only:
            query = query.filter(SubscriptionPlan.is_active == True)

        results = []
        for sub_plan, pricing_plan, template in query.all():
            results.append({
                "id": sub_plan.id,
                "pricing_plan": {
                    "id": pricing_plan.id,
                    "name": pricing_plan.name,
                    "price": float(pricing_plan.price),
                    "duration_months": pricing_plan.duration_months,
                    "features": pricing_plan.features
                },
                "template": {
                    "id": template.id,
                    "name": template.name,
                    "category": template.category,
                    "price_adjustment": float(template.price_adjustment)
                } if template else None,
                "custom_price": float(sub_plan.custom_price) if sub_plan.custom_price else None,
                "is_active": sub_plan.is_active
            })
        return results


# ==================== ORDER SERVICE ====================

class OrderService:
    """Service for managing orders"""

    @staticmethod
    def create_order(db: Session, order_data: OrderCreate) -> Optional[Order]:
        """Create a new order with validation and price calculation"""
        # Validate pricing plan exists and is active
        pricing_plan = db.query(PricingPlan).filter(
            PricingPlan.id == order_data.pricing_plan_id,
            PricingPlan.is_active == True
        ).first()
        if not pricing_plan:
            return None
            
        # Local import to prevent circular dependency
        from app.modules.service_delivery import services as delivery_services

        # Validate template if provided
        template = None
        if order_data.template_id:
            template = db.query(Template).filter(
                Template.id == order_data.template_id,
                Template.is_active == True
            ).first()
            if not template:
                return None
        
        # [REVISION] Check for existing PENDING orders for this user and CANCEL them
        # This prevents "hanging" orders when users navigate back and forth
        existing_pending_orders = db.query(Order).filter(
            Order.user_id == order_data.user_id,
            Order.status == OrderStatus.PENDING
        ).all()
        
        for pending_order in existing_pending_orders:
            pending_order.status = OrderStatus.CANCELLED
            print(f"[ORDER-CLEANUP] Auto-cancelling orphaned pending order #{pending_order.id}")
            
            # [FIX] Also CANCEL the associated Project (WebsiteInstance)
            # This prevents "Waiting" projects from piling up in the client dashboard
            orphan_project = delivery_services.get_instance_by_order(db, pending_order.id)
            if orphan_project:
                orphan_project.stage = "cancelled"
                print(f"[ORDER-CLEANUP] Auto-cancelling orphaned project #{orphan_project.id}")
        
        if existing_pending_orders:
            db.commit() # Commit the cancellations first

        # Calculate total price
        total_price = Decimal(str(pricing_plan.price))
        if template:
            total_price += Decimal(str(template.price_adjustment))
        if order_data.custom_price:
            total_price = Decimal(str(order_data.custom_price))

        # Create or find subscription plan
        subscription_plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.pricing_plan_id == order_data.pricing_plan_id,
            SubscriptionPlan.template_id == order_data.template_id
        ).first()

        if not subscription_plan:
            subscription_plan = SubscriptionPlan(
                pricing_plan_id=order_data.pricing_plan_id,
                template_id=order_data.template_id,
                custom_price=order_data.custom_price
            )
            db.add(subscription_plan)
            db.flush()

        # Create order
        db_order = Order(
            user_id=order_data.user_id,
            subscription_plan_id=subscription_plan.id,
            status=OrderStatus.PENDING,
            total_price=total_price
        )
        db.add(db_order)
        db.flush()

        # Automatically Create Project (WebsiteInstance) if details provided
        if order_data.project_name or order_data.subdomain:
            from app.modules.service_delivery import services as delivery_services
            from app.modules.service_delivery import schemas as delivery_schemas
            
            # Use provided subdomain or fallback to project name slug or order id
            subdomain = order_data.subdomain
            if not subdomain and order_data.project_name:
                subdomain = order_data.project_name.lower().replace(" ", "-")
            if not subdomain:
                subdomain = f"project-{db_order.id}"

            try:
                project_data = delivery_schemas.WebsiteInstanceCreate(
                    order_id=db_order.id,
                    user_id=order_data.user_id,
                    subdomain=subdomain
                )
                delivery_services.create_website_instance(
                    db, 
                    project_data, 
                    name=order_data.project_name, 
                    tier=order_data.tier, 
                    description=order_data.description,
                    order_id=db_order.id
                )
            except Exception as e:
                print(f"Failed to auto-create project: {e}")
                # Don't fail the order creation, just log it. Project can be created later.

        # Create order items
        db.add(OrderItem(
            order_id=db_order.id,
            item_type=OrderItemType.PRICING_PLAN,
            item_id=pricing_plan.id,
            item_name=pricing_plan.name,
            price=pricing_plan.price
        ))

        if template:
            db.add(OrderItem(
                order_id=db_order.id,
                item_type=OrderItemType.TEMPLATE,
                item_id=template.id,
                item_name=f"Template: {template.name}",
                price=template.price_adjustment
            ))

        db.commit()
        db.refresh(db_order)

        # [NOTIFIKASI] Notify Admins
        try:
            from app.modules.auth_user import models as auth_models
            from app.modules.auth_user import services as auth_services
            
            admins = db.query(auth_models.User).filter(auth_models.User.role == 'admin').all()
            for admin in admins:
                auth_services.create_notification(
                    db, 
                    admin.id, 
                    "shopping-bag", 
                    "New Order Received", 
                    f"Order #{db_order.id} for {pricing_plan.name}",
                    f"/dashboard/orders" # Direct to orders list for now
                )
        except Exception as e:
            print(f"[NOTIF ERROR] Failed to notify admins: {e}")

        return db_order

    @staticmethod
    def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        """Get all orders for a specific user"""
        return db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_order(db: Session, order_id: int) -> Optional[Order]:
        """Get a specific order by ID"""
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def cancel_order(db: Session, order_id: int, reason: Optional[str] = None) -> Optional[Order]:
        """Cancel a pending order"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None

        if db_order.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can be cancelled")

        db_order.status = OrderStatus.CANCELLED
        
        # [FIX] Also CANCEL the associated Project
        from app.modules.service_delivery import services as delivery_services
        associated_project = delivery_services.get_instance_by_order(db, db_order.id)
        if associated_project:
            associated_project.stage = "cancelled"
            print(f"[ORDER-CANCEL] Auto-cancelling associated project #{associated_project.id}")

        db.commit()
        db.refresh(db_order)
        return db_order

    @staticmethod
    def mark_order_paid(db: Session, order_id: int) -> Optional[Order]:
        """Mark an order as paid"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None

        db_order.status = OrderStatus.PAID
        db_order.paid_at = datetime.utcnow()
        db.commit()
        db.refresh(db_order)
        return db_order


# ==================== PAYMENT SERVICE ====================

class PaymentService:
    """Service for managing payments with Midtrans integration"""

    @staticmethod
    def _encode_auth(server_key: str) -> str:
        """Encode server key for Basic Auth"""
        auth_string = f"{server_key}:"
        return base64.b64encode(auth_string.encode()).decode()

    @staticmethod
    async def create_payment_link(db: Session, order_id: int, payment_url: str) -> Optional[Dict[str, Any]]:
        """Create a payment link via Midtrans Snap API"""
        from app.core.config import settings

        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None

        if db_order.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can have payment links created")

        # Check if payment already exists
        existing_payment = db.query(Payment).filter(
            Payment.order_id == order_id,
            Payment.status == PaymentStatus.PENDING
        ).first()

        if existing_payment:
            return {
                "payment_url": existing_payment.payment_url,
                "transaction_id": existing_payment.transaction_id
            }

        # Prepare Midtrans payload
        transaction_details = {
            "order_id": f"ORDER-{order_id}-{int(datetime.utcnow().timestamp())}",
            "gross_amount": int(db_order.total_price)
        }

        customer_details = {
            "user_id": db_order.user_id,
            # Add more details when user system is integrated
        }

        payload = {
            "transaction_details": transaction_details,
            "customer_details": customer_details,
            "enabled_payments": ["gopay", "bank_transfer", "qris", "credit_card"],
            "callbacks": {
                "finish": f"{payment_url}/payment/finish"
            }
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {PaymentService._encode_auth(settings.MIDTRANS_SERVER_KEY)}"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.MIDTRANS_PAYMENT_URL,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()

            # Save payment record
            db_payment = Payment(
                order_id=order_id,
                payment_gateway=PaymentGateway.MIDTRANS,
                transaction_id=result.get("token", ""),
                amount=db_order.total_price,
                status=PaymentStatus.PENDING,
                payment_url=result.get("redirect_url", ""),
                raw_response=result
            )
            db.add(db_payment)
            db.commit()
            db.refresh(db_payment)

            return {
                "payment_url": db_payment.payment_url,
                "transaction_id": db_payment.transaction_id
            }

        except httpx.HTTPError as e:
            raise Exception(f"Payment gateway error: {str(e)}")

    @staticmethod
    def handle_webhook(db: Session, webhook_data: Dict[str, Any]) -> bool:
        """Process Midtrans webhook notification"""
        transaction_id = webhook_data.get("transaction_id")
        transaction_status = webhook_data.get("transaction_status")
        fraud_status = webhook_data.get("fraud_status")
        gross_amount = webhook_data.get("gross_amount")

        if not transaction_id:
            return False

        # Find payment by transaction_id
        db_payment = db.query(Payment).filter(
            Payment.transaction_id == transaction_id
        ).first()

        if not db_payment:
            return False

        should_activate_project = False

        # Update payment status based on transaction status
        if transaction_status == "capture":
            if fraud_status == "accept":
                db_payment.status = PaymentStatus.SUCCESS
                db_payment.paid_at = datetime.utcnow()
                should_activate_project = True

        elif transaction_status == "settlement":
            db_payment.status = PaymentStatus.SUCCESS
            db_payment.paid_at = datetime.utcnow()
            should_activate_project = True

        elif transaction_status == "cancel" or transaction_status == "deny":
            db_payment.status = PaymentStatus.CANCELLED

        elif transaction_status == "expire":
            db_payment.status = PaymentStatus.CANCELLED
            # Mark order as expired
            db_order = db.query(Order).filter(Order.id == db_payment.order_id).first()
            if db_order:
                db_order.status = OrderStatus.EXPIRED

        db_payment.raw_response = webhook_data
        db.commit()

        # [REVISION] If Payment Success -> Mark Order Paid & Create Project (Dev 3 Integration)
        if should_activate_project:
            # 1. Update Order Status
            OrderService.mark_order_paid(db, db_payment.order_id)
            
            # 2. Generate Invoice
            InvoiceService.generate_invoice(db, db_payment.order_id)
            
            # 3. [NEW] Automatically Create Website Project (Bridge to Dev 3)
            # 3. [NEW] Automatically Create Website Project (Bridge to Dev 3)
            # Use with_for_update() to lock the order row, preventing race conditions if multiple webhooks fire closely
            db_order = db.query(Order).filter(Order.id == db_payment.order_id).with_for_update().first()
            
            # Local import
            from app.modules.service_delivery import services as delivery_services
            from app.modules.service_delivery import schemas as delivery_schemas
            
            if db_order:
                # [REVISION] Check if project already exists to prevent duplicate (Dev 3 Integration Fix)
                # Now safe from race conditions due to lock above
                existing_project = delivery_services.get_instance_by_order(db, db_order.id)
                if existing_project:
                    print(f"[AUTO-PROJECT] Project already exists for Order #{db_order.id}. Skipping creation.")
                else:
                    # Generate unique subdomain suggestion
                    default_subdomain = f"project-{db_order.id}-{int(datetime.utcnow().timestamp())}"
                    
                    project_data = delivery_schemas.WebsiteInstanceCreate(
                        order_id=db_order.id,
                        user_id=db_order.user_id,
                        subdomain=default_subdomain
                    )
                    try:
                        delivery_services.create_website_instance(
                            db, 
                            project_data,
                            order_id=db_order.id
                        )
                        print(f"[AUTO-PROJECT] Project created for Order #{db_order.id}")
                    except Exception as e:
                        # Log error but don't fail the webhook response
                        print(f"[AUTO-PROJECT ERROR] Failed to create project: {str(e)}")

        return True

    @staticmethod
    def get_payment_status(db: Session, order_id: int) -> Optional[Dict[str, Any]]:
        """Get payment status for an order"""
        db_payment = db.query(Payment).filter(
            Payment.order_id == order_id
        ).order_by(Payment.created_at.desc()).first()

        if not db_payment:
            return None

        return {
            "id": db_payment.id,
            "transaction_id": db_payment.transaction_id,
            "amount": float(db_payment.amount),
            "status": db_payment.status.value,
            "payment_method": db_payment.payment_method,
            "payment_url": db_payment.payment_url,
            "created_at": db_payment.created_at,
            "paid_at": db_payment.paid_at
        }


# ==================== INVOICE SERVICE ====================

class InvoiceService:
    """Service for generating and managing invoices"""

    @staticmethod
    def _ensure_invoice_directory():
        """Ensure invoice directory exists"""
        invoice_dir = Path("/invoices")
        invoice_dir.mkdir(exist_ok=True)
        return invoice_dir

    @staticmethod
    def _generate_invoice_number(db: Session, date: datetime) -> str:
        """Generate invoice number with format: INV/YYYYMMDD/XXXXX"""
        date_str = date.strftime("%Y%m%d")

        # Get sequence number for today
        count = db.query(Invoice).filter(
            Invoice.invoice_number.like(f"INV/{date_str}/%")
        ).count()

        sequence = str(count + 1).zfill(5)
        return f"INV/{date_str}/{sequence}"

    @staticmethod
    def _generate_pdf_html(order: Order, items: list, invoice_number: str) -> str:
        """Generate HTML for PDF invoice (Compact Single Page)"""

        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; color: #334155;">{item.item_name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right; color: #0f172a; font-weight: bold;">Rp {float(item.price):,.2f}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4;
                    margin: 1.5cm;
                }}
                body {{
                    font-family: Helvetica, Arial, sans-serif;
                    font-size: 13px;
                    line-height: 1.4;
                    color: #334155;
                    margin: 0;
                    padding: 0;
                }}
                
                /* Utilities */
                .w-full {{ width: 100%; }}
                .mb-2 {{ margin-bottom: 10px; }}
                .mb-4 {{ margin-bottom: 20px; }}
                .mb-6 {{ margin-bottom: 30px; }}
                .text-right {{ text-align: right; }}
                .text-blue {{ color: #2563eb; }}
                .font-bold {{ font-weight: bold; }}
                .text-sm {{ font-size: 11px; color: #64748b; }}
                
                /* Header */
                .header-title {{
                    font-size: 24px; 
                    font-weight: bold; 
                    color: #1e293b;
                    margin: 0;
                }}
                
                .invoice-tag {{
                    font-size: 32px;
                    color: #cbd5e1;
                    font-weight: bold;
                    line-height: 1;
                }}

                /* Client Box */
                .client-box {{
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 15px;
                }}
                
                h3 {{
                    font-size: 11px;
                    text-transform: uppercase;
                    color: #94a3b8;
                    letter-spacing: 0.5px;
                    margin: 0 0 5px 0;
                }}

                /* Tables */
                table {{ width: 100%; border-collapse: collapse; }}
                
                th {{
                    background-color: #f1f5f9;
                    color: #475569;
                    font-size: 11px;
                    font-weight: bold;
                    text-transform: uppercase;
                    padding: 10px;
                    text-align: left;
                    border-top: 1px solid #cbd5e1;
                    border-bottom: 1px solid #cbd5e1;
                }}
                
                /* Footer */
                .footer {{
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    text-align: center;
                    font-size: 11px;
                    color: #94a3b8;
                    padding-top: 10px;
                    border-top: 1px solid #e2e8f0;
                }}
            </style>
        </head>
        <body>
            <!-- Header -->
            <table class="w-full mb-6">
                <tr>
                    <td valign="top">
                        <div class="header-title text-blue">DIGADOIN</div>
                        <div class="text-sm" style="margin-top: 5px; line-height: 1.4;">
                            PT Digadoin Teknologi<br>
                            Jalan Teknologi No. 1<br>
                            Bandung, 40132
                        </div>
                    </td>
                    <td valign="top" class="text-right">
                        <div class="invoice-tag">INVOICE</div>
                        <div class="text-sm" style="margin-top: 8px;">
                            <strong>#{invoice_number}</strong><br>
                            Date: {order.created_at.strftime('%d %B %Y')}
                        </div>
                    </td>
                </tr>
            </table>

            <div style="width: 100%; height: 2px; background-color: #2563eb; margin-bottom: 30px;"></div>

            <!-- Addresses -->
            <table class="w-full mb-6">
                <tr>
                    <td width="48%" valign="top">
                        <div class="client-box" style="height: 100px;">
                            <h3>Bill To</h3>
                            <div style="font-size: 16px; font-weight: bold; color: #0f172a; margin-bottom: 5px;">
                                User ID: #{order.user_id}
                            </div>
                            <div class="text-sm">
                                Valued Customer<br>
                                Digital Services Package
                            </div>
                        </div>
                    </td>
                    <td width="4%"></td>
                    <td width="48%" valign="top">
                        <div class="client-box" style="height: 100px;">
                            <h3>Order Details</h3>
                            <table class="w-full">
                                <tr>
                                    <td class="text-sm" style="padding: 2px 0;">Order Ref:</td>
                                    <td class="text-right font-bold text-sm" style="padding: 2px 0;">#{order.id}</td>
                                </tr>
                                <tr>
                                    <td class="text-sm" style="padding: 2px 0;">Status:</td>
                                    <td class="text-right font-bold text-blue text-sm" style="padding: 2px 0;">PAID</td>
                                </tr>
                                <tr>
                                    <td class="text-sm" style="padding: 2px 0;">Payment:</td>
                                    <td class="text-right text-sm" style="padding: 2px 0;">Bank Transfer</td>
                                </tr>
                            </table>
                        </div>
                    </td>
                </tr>
            </table>

            <!-- Line Items -->
            <table class="w-full mb-4">
                <thead>
                    <tr>
                        <th width="70%">Description</th>
                        <th width="30%" class="text-right">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <!-- Totals -->
            <table class="w-full">
                <tr>
                    <td width="55%"></td>
                    <td width="45%">
                        <table class="w-full">
                            <tr>
                                <td style="padding: 8px 0; color: #64748b;" class="text-right">Subtotal</td>
                                <td class="text-right font-bold" style="padding: 8px 0; width: 120px;">Rp {float(order.total_price):,.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b;" class="text-right">Tax</td>
                                <td class="text-right font-bold" style="padding: 8px 0;">Rp 0.00</td>
                            </tr>
                            <tr>
                                <td style="padding: 15px 0; font-size: 16px; font-weight: bold; color: #1e293b; border-top: 2px solid #e2e8f0;" class="text-right">TOTAL</td>
                                <td class="text-right" style="padding: 15px 0; font-size: 16px; font-weight: bold; color: #2563eb; border-top: 2px solid #e2e8f0;">Rp {float(order.total_price):,.2f}</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>

            <div class="footer">
                <p>Thank you for your business. | www.digadoin.com</p>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def generate_invoice(db: Session, order_id: int) -> Optional[Invoice]:
        """Generate invoice PDF for a paid order (Force Regenerate if exists)"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None

        if db_order.status != OrderStatus.PAID:
            raise ValueError("Invoice can only be generated for paid orders")

        # Check if invoice already exists
        existing_invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
        
        invoice_dir = InvoiceService._ensure_invoice_directory()
        
        if existing_invoice:
            # Reuse existing number
            invoice_number = existing_invoice.invoice_number
        else:
            # Generate new number
            invoice_number = InvoiceService._generate_invoice_number(db, db_order.created_at)

        try:
            # Monkey patch for reportlab compatibility (ShowBoundaryValue removed in newer versions)
            import reportlab.platypus.frames
            if not hasattr(reportlab.platypus.frames, 'ShowBoundaryValue'):
                class MockShowBoundaryValue:
                    def __init__(self, *args, **kwargs):
                        pass
                reportlab.platypus.frames.ShowBoundaryValue = MockShowBoundaryValue

            from xhtml2pdf import pisa

            # Get order items for the invoice
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

            html_content = InvoiceService._generate_pdf_html(db_order, order_items, invoice_number)
            pdf_path = invoice_dir / f"{invoice_number.replace('/', '_')}.pdf"

            # Generate PDF (Overwrite if exists)
            with open(pdf_path, "wb") as pdf_file:
                pisa.CreatePDF(html_content, dest=pdf_file)

            if existing_invoice:
                existing_invoice.pdf_url = str(pdf_path)
                db.commit()
                db.refresh(existing_invoice)
                return existing_invoice
            
            # Create invoice record
            db_invoice = Invoice(
                order_id=order_id,
                invoice_number=invoice_number,
                pdf_url=str(pdf_path)
            )
            db.add(db_invoice)
            db.commit()
            db.refresh(db_invoice)

            # Send invoice email
            InvoiceService.send_invoice_email(db, db_invoice.id)

            return db_invoice

        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")

    @staticmethod
    def get_invoice(db: Session, order_id: int) -> Optional[Invoice]:
        """Get invoice for an order"""
        return db.query(Invoice).filter(Invoice.order_id == order_id).first()

    @staticmethod
    def send_invoice_email(db: Session, invoice_id: int) -> bool:
        """Send invoice via email (placeholder for email service integration)"""
        from app.core.config import settings

        db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not db_invoice:
            return False

        # TODO: Integrate with fastapi-mail for actual email sending
        # For now, just mark as sent
        db_invoice.sent_via_email = True
        db_invoice.sent_at = datetime.utcnow()
        db.commit()

        return True

    @staticmethod
    def resend_invoice_email(db: Session, order_id: int) -> bool:
        """Resend invoice to customer"""
        db_invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
        if not db_invoice:
            return False

        return InvoiceService.send_invoice_email(db, db_invoice.id)


# ==================== REPORTING SERVICE ====================

class ReportingService:
    """Service for generating revenue and business metrics"""

    @staticmethod
    def calculate_mrr(db: Session) -> Dict[str, Any]:
        """Calculate Monthly Recurring Revenue"""
        result = db.query(
            func.sum(Order.total_price).label("total_mrr"),
            func.count(Order.id).label("active_subscriptions")
        ).filter(
            Order.status == OrderStatus.PAID
        ).first()

        return {
            "mrr": float(result.total_mrr) if result.total_mrr else 0.0,
            "active_subscriptions": result.active_subscriptions or 0
        }

    @staticmethod
    def get_conversion_rate(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get order to payment conversion rate"""
        query = db.query(
            func.count(Order.id).label("total_orders"),
            func.sum(case((Order.status == OrderStatus.PAID, 1), else_=0)).label("paid_orders")
        )

        if start_date:
            query = query.filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at <= end_date)

        result = query.first()

        total_orders = result.total_orders or 0
        paid_orders = result.paid_orders or 0
        conversion_rate = (paid_orders / total_orders * 100) if total_orders > 0 else 0

        return {
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "conversion_rate": round(conversion_rate, 2)
        }

    @staticmethod
    def get_revenue_by_period(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """Get revenue grouped by day, week, or month"""
        if group_by == "day":
            date_trunc = func.date_trunc("day", Order.created_at)
            date_format = func.to_char(date_trunc, "YYYY-MM-DD")
        elif group_by == "week":
            date_trunc = func.date_trunc("week", Order.created_at)
            date_format = func.to_char(date_trunc, "YYYY-MM-DD")
        else:  # month
            date_trunc = func.date_trunc("month", Order.created_at)
            date_format = func.to_char(date_trunc, "YYYY-MM")

        query = db.query(
            date_format.label("period"),
            func.sum(Order.total_price).label("revenue"),
            func.count(Order.id).label("orders")
        ).filter(
            Order.status == OrderStatus.PAID
        )

        if start_date:
            query = query.filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at <= end_date)

        results = query.group_by(date_trunc).order_by(date_trunc).all()

        return [
            {
                "period": row.period,
                "revenue": float(row.revenue) if row.revenue else 0.0,
                "orders": row.orders
            }
            for row in results
        ]

    @staticmethod
    def get_top_selling_plans(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular pricing plans"""
        results = db.query(
            PricingPlan.name,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_price).label("total_revenue")
        ).join(
            SubscriptionPlan, PricingPlan.id == SubscriptionPlan.pricing_plan_id
        ).join(
            Order, SubscriptionPlan.id == Order.subscription_plan_id
        ).filter(
            Order.status == OrderStatus.PAID
        ).group_by(
            PricingPlan.id, PricingPlan.name
        ).order_by(
            func.count(Order.id).desc()
        ).limit(limit).all()

        return [
            {
                "plan_name": row.name,
                "order_count": row.order_count,
                "total_revenue": float(row.total_revenue) if row.total_revenue else 0.0
            }
            for row in results
        ]

    @staticmethod
    def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        from datetime import timedelta

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Today's revenue
        today_revenue = db.query(
            func.sum(Order.total_price)
        ).filter(
            Order.status == OrderStatus.PAID,
            Order.created_at >= today_start
        ).scalar() or 0

        # This month's revenue
        month_revenue = db.query(
            func.sum(Order.total_price)
        ).filter(
            Order.status == OrderStatus.PAID,
            Order.created_at >= month_start
        ).scalar() or 0

        # Total revenue
        total_revenue = db.query(
            func.sum(Order.total_price)
        ).filter(
            Order.status == OrderStatus.PAID
        ).scalar() or 0

        # Pending orders
        pending_orders = db.query(func.count(Order.id)).filter(
            Order.status == OrderStatus.PENDING
        ).scalar() or 0

        # Get MRR
        mrr_data = ReportingService.calculate_mrr(db)

        # Get conversion rate
        conversion_data = ReportingService.get_conversion_rate(db)

        # Get top plans
        top_plans = ReportingService.get_top_selling_plans(db, limit=5)

        return {
            "revenue": {
                "today": float(today_revenue),
                "this_month": float(month_revenue),
                "all_time": float(total_revenue)
            },
            "mrr": mrr_data,
            "pending_orders": pending_orders,
            "conversion_rate": conversion_data["conversion_rate"],
            "top_plans": top_plans
        }

    @staticmethod
    def get_recent_activities(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activities for dashboard feed"""
        from app.modules.auth_user.models import User
        from app.modules.service_delivery.models import WebsiteInstance, Ticket
        
        activities = []
        
        # Get recent orders
        recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(limit).all()
        for order in recent_orders:
            user = db.query(User).filter(User.id == order.user_id).first()
            user_name = user.email if user else f"User #{order.user_id}"
            activities.append({
                "id": f"order-{order.id}",
                "type": "payment" if order.status == OrderStatus.PAID else "new_order",
                "title": f"Order #{order.id} - {order.status.value}",
                "description": f"Order by {user_name}",
                "time": order.created_at.isoformat(),
                "created_at": order.created_at.isoformat()
            })
        
        # Get recent projects
        try:
            recent_projects = db.query(WebsiteInstance).order_by(WebsiteInstance.created_at.desc()).limit(limit).all()
            for project in recent_projects:
                user = db.query(User).filter(User.id == project.user_id).first()
                user_name = user.email if user else f"User #{project.user_id}"
                activities.append({
                    "id": f"project-{project.id}",
                    "type": "new_project",
                    "title": f"Project: {project.subdomain}",
                    "description": f"Created by {user_name}",
                    "time": project.created_at.isoformat(),
                    "created_at": project.created_at.isoformat()
                })
        except Exception:
            pass  # WebsiteInstance table might not exist
        
        # Get recent tickets
        try:
            recent_tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).limit(limit).all()
            for ticket in recent_tickets:
                user = db.query(User).filter(User.id == ticket.user_id).first()
                user_name = user.email if user else f"User #{ticket.user_id}"
                activities.append({
                    "id": f"ticket-{ticket.id}",
                    "type": "ticket",
                    "title": f"Ticket: {ticket.subject}",
                    "description": f"From {user_name}",
                    "time": ticket.created_at.isoformat(),
                    "created_at": ticket.created_at.isoformat()
                })
        except Exception:
            pass  # Ticket table might not exist
        
        # Sort all activities by time and return top N
        activities.sort(key=lambda x: x["created_at"], reverse=True)
        return activities[:limit]