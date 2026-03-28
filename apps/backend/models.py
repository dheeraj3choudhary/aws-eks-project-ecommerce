"""
models.py
---------
SQLAlchemy ORM models for the e-commerce app.

Tables
------
  products  – Product catalogue (id, name, description, price, stock, …)
  cart_items – Shopping cart rows (one row per product per session)

All timestamps are stored as UTC.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


# ── Helpers ───────────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Product ───────────────────────────────────────────────────────────────────

class Product(Base):
    """
    Represents an item available for purchase in the store.

    Columns
    -------
    id          – Auto-incrementing primary key.
    name        – Human-readable product name (unique, max 200 chars).
    description – Optional long-form description.
    price       – Decimal price (max 10 digits, 2 decimal places). Must be > 0.
    stock       – Integer quantity in stock. 0 = out of stock. Must be >= 0.
    category    – Optional category label (e.g. "Audio", "Accessories").
    emoji       – Optional single emoji for UI display (e.g. "🎧").
    is_active   – Soft-delete flag. Inactive products are hidden from listings.
    created_at  – UTC timestamp of row creation.
    updated_at  – UTC timestamp, auto-refreshed on every update.
    """

    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("price > 0",  name="ck_products_price_positive"),
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
    )

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    price       = Column(Numeric(10, 2), nullable=False)
    stock       = Column(Integer, nullable=False, default=0)
    category    = Column(String(100), nullable=True, index=True)
    emoji       = Column(String(8), nullable=True)
    is_active   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at  = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    # Relationship: a product can appear in many cart rows
    cart_items = relationship(
        "CartItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} price={self.price}>"


# ── CartItem ──────────────────────────────────────────────────────────────────

class CartItem(Base):
    """
    Represents one line in a user's shopping cart.

    In this implementation the cart is identified by a session_id string
    (stored in the browser / passed as a header).  A more complete system
    would link this to an authenticated User row instead.

    Columns
    -------
    id          – Auto-incrementing primary key.
    session_id  – Client-supplied cart / session identifier (max 128 chars).
    product_id  – FK → products.id.
    quantity    – How many units of the product are in the cart. Must be >= 1.
    added_at    – UTC timestamp of when the item was first added.
    updated_at  – UTC timestamp, refreshed whenever quantity changes.
    """

    __tablename__ = "cart_items"

    __table_args__ = (
        # Each session can only have one row per product; duplicates → qty update
        UniqueConstraint("session_id", "product_id", name="uq_cart_session_product"),
        CheckConstraint("quantity >= 1", name="ck_cart_quantity_positive"),
    )

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity   = Column(Integer, nullable=False, default=1)
    added_at   = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    # Relationship: each cart item belongs to one product
    product = relationship("Product", back_populates="cart_items")

    def __repr__(self) -> str:
        return (
            f"<CartItem id={self.id} session={self.session_id!r} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )