"""
Database Models for Transaction Module
Dev 2: Transaction, Billing & Order Engine
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
import enum
from app.core.database import Base



# ==================== ENUMS ====================

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentGateway(str, enum.Enum):
    MIDTRANS = "midtrans"
    XENDIT = "xendit"


class OrderItemType(str, enum.Enum):
    PRICING_PLAN = "pricing_plan"
    TEMPLATE = "template"


# ==================== PRODUCT MANAGEMENT ====================

class PricingPlan(Base):
    __tablename__ = "pricing_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    duration_months = Column(Integer, nullable=False, default=1)
    features = Column(JSON, nullable=True)  # List of features included
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscription_plans = relationship("SubscriptionPlan", back_populates="pricing_plan")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    preview_image = Column(String(500), nullable=True)  # URL to preview image
    price_adjustment = Column(Numeric(12, 2), nullable=False, default=0)  # Additional cost
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscription_plans = relationship("SubscriptionPlan", back_populates="template")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    pricing_plan_id = Column(Integer, ForeignKey("pricing_plans.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    custom_price = Column(Numeric(12, 2), nullable=True)  # Override total price if needed
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    pricing_plan = relationship("PricingPlan", back_populates="subscription_plans")
    template = relationship("Template", back_populates="subscription_plans")
    orders = relationship("Order", back_populates="subscription_plan")


# ==================== ORDER SYSTEM ====================

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)
    total_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    subscription_plan = relationship("SubscriptionPlan", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    item_type = Column(SQLEnum(OrderItemType), nullable=False)
    item_id = Column(Integer, nullable=False)  # ID of pricing_plan or template
    item_name = Column(String(200), nullable=False)  # Denormalized for display
    price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="order_items")


# ==================== PAYMENT GATEWAY ====================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    payment_gateway = Column(SQLEnum(PaymentGateway), nullable=False, default=PaymentGateway.MIDTRANS)
    transaction_id = Column(String(100), nullable=True, unique=True)  # External transaction ID
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    payment_url = Column(String(500), nullable=True)  # Redirect URL for payment
    payment_method = Column(String(50), nullable=True)  # e.g., gopay, bank_transfer, qris
    raw_response = Column(JSON, nullable=True)  # Store full gateway response
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="payments")


# ==================== INVOICE ====================

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    pdf_url = Column(String(500), nullable=True)  # Path to generated PDF
    sent_via_email = Column(Boolean, nullable=False, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="invoice")
