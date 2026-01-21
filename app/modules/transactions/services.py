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
        """Delete a pricing plan (soft delete by setting is_active=False)"""
        db_plan = db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()
        if not db_plan:
            return False
        db_plan.is_active = False
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
        """Delete a template (soft delete by setting is_active=False)"""
        db_template = db.query(Template).filter(Template.id == template_id).first()
        if not db_template:
            return False
        db_template.is_active = False
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

        # Validate template if provided
        template = None
        if order_data.template_id:
            template = db.query(Template).filter(
                Template.id == order_data.template_id,
                Template.is_active == True
            ).first()
            if not template:
                return None

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

        # Create order items
        OrderItem(
            order_id=db_order.id,
            item_type=OrderItemType.PRICING_PLAN,
            item_id=pricing_plan.id,
            item_name=pricing_plan.name,
            price=pricing_plan.price
        )
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

        # Update payment status based on transaction status
        if transaction_status == "capture":
            if fraud_status == "accept":
                db_payment.status = PaymentStatus.SUCCESS
                db_payment.paid_at = datetime.utcnow()
                # Update order status
                OrderService.mark_order_paid(db, db_payment.order_id)
                # Trigger invoice generation
                InvoiceService.generate_invoice(db, db_payment.order_id)

        elif transaction_status == "settlement":
            db_payment.status = PaymentStatus.SUCCESS
            db_payment.paid_at = datetime.utcnow()
            OrderService.mark_order_paid(db, db_payment.order_id)
            InvoiceService.generate_invoice(db, db_payment.order_id)

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
        """Generate HTML for PDF invoice"""

        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">{item.item_name}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">Rp {float(item.price):,.2f}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .invoice-title {{ font-size: 32px; color: #2563eb; font-weight: bold; }}
                .invoice-info {{ background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .info-row {{ display: flex; justify-content: space-between; margin: 8px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
                th {{ background: #2563eb; color: white; padding: 12px; text-align: left; }}
                .total {{ font-size: 20px; font-weight: bold; text-align: right; padding: 20px; }}
                .footer {{ text-align: center; margin-top: 50px; color: #64748b; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="invoice-title">DIGADOIN</div>
                <p>Invoice</p>
            </div>

            <div class="invoice-info">
                <div class="info-row">
                    <span><strong>Invoice Number:</strong></span>
                    <span>{invoice_number}</span>
                </div>
                <div class="info-row">
                    <span><strong>Order ID:</strong></span>
                    <span>#{order.id}</span>
                </div>
                <div class="info-row">
                    <span><strong>Date:</strong></span>
                    <span>{order.created_at.strftime('%d %B %Y')}</span>
                </div>
                <div class="info-row">
                    <span><strong>User ID:</strong></span>
                    <span>{order.user_id}</span>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th style="text-align: right;">Price</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <div class="total">
                Total: Rp {float(order.total_price):,.2f}
            </div>

            <div class="footer">
                <p>Thank you for your purchase!</p>
                <p>For questions, contact support@digadoin.com</p>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def generate_invoice(db: Session, order_id: int) -> Optional[Invoice]:
        """Generate invoice PDF for a paid order"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None

        if db_order.status != OrderStatus.PAID:
            raise ValueError("Invoice can only be generated for paid orders")

        # Check if invoice already exists
        existing_invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
        if existing_invoice:
            return existing_invoice

        invoice_dir = InvoiceService._ensure_invoice_directory()
        invoice_number = InvoiceService._generate_invoice_number(db, db_order.created_at)

        try:
            from xhtml2pdf import pisa

            # Get order items for the invoice
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

            html_content = InvoiceService._generate_pdf_html(db_order, order_items, invoice_number)
            pdf_path = invoice_dir / f"{invoice_number.replace('/', '_')}.pdf"

            # Generate PDF
            with open(pdf_path, "wb") as pdf_file:
                pisa.CreatePDF(html_content, dest=pdf_file)

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
