"""
main.py
-------
FastAPI application entry-point for the ShopEKS e-commerce backend.

Endpoints
---------
  GET    /health                  – Liveness / readiness probe
  GET    /products                – List active products (with optional filters)
  POST   /products                – Create a new product
  GET    /products/{id}           – Get a single product
  PATCH  /products/{id}           – Partially update a product
  DELETE /products/{id}           – Soft-delete a product

  GET    /cart                    – Get current session's cart
  POST   /cart                    – Add / increment a product in the cart
  PATCH  /cart/{item_id}          – Update quantity of a cart item
  DELETE /cart/{item_id}          – Remove a single item from the cart
  DELETE /cart                    – Clear the entire cart

Session identity
----------------
  Cart operations use the X-Session-ID request header to identify the cart.
  The frontend generates a UUID and stores it in localStorage.
  A default value of "anonymous" is used when the header is absent.
"""

import logging
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, check_db_connection, engine, get_db
from models import CartItem, Product
from schemas import (
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartSummary,
    HealthResponse,
    MessageResponse,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup; yield; nothing special on shutdown."""
    logger.info("Starting ShopEKS backend v%s", APP_VERSION)
    Base.metadata.create_all(bind=engine)   # idempotent — safe to run every boot
    check_db_connection()
    _seed_demo_products()
    yield
    logger.info("ShopEKS backend shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ShopEKS API",
    description="FastAPI backend for the ShopEKS e-commerce demo running on AWS EKS.",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# In production, replace "*" with your ALB/CloudFront domain.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found.")
    return product


def _get_cart_item_or_404(item_id: int, session_id: str, db: Session) -> CartItem:
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.session_id == session_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Cart item {item_id} not found.")
    return item


def _cart_summary(session_id: str, db: Session) -> CartSummary:
    items = (
        db.query(CartItem)
        .filter(CartItem.session_id == session_id)
        .all()
    )
    total = sum(
        Decimal(str(i.product.price)) * i.quantity
        for i in items
        if i.product
    )
    item_count = sum(i.quantity for i in items)
    return CartSummary(items=items, item_count=item_count, total_price=total)


# ── Seed data ─────────────────────────────────────────────────────────────────

def _seed_demo_products():
    """Insert sample products if the table is empty (first boot only)."""
    db = next(get_db())
    try:
        if db.query(Product).count() > 0:
            return
        demo = [
            Product(name="Wireless Headphones", description="Premium over-ear headphones with 30hr battery and ANC.", price=Decimal("89.99"),  stock=10, category="Audio",        emoji="🎧"),
            Product(name="Mechanical Keyboard",  description="Tactile switches, RGB backlight, compact TKL layout.", price=Decimal("129.99"), stock=5,  category="Peripherals",   emoji="⌨️"),
            Product(name="USB-C Hub",            description="7-in-1 hub: HDMI 4K, 3× USB-A, SD, PD, Ethernet.",    price=Decimal("39.99"),  stock=20, category="Accessories",   emoji="🔌"),
            Product(name="Standing Desk Mat",    description="Anti-fatigue mat with beveled edges.",                  price=Decimal("59.99"),  stock=8,  category="Ergonomics",    emoji="🟫"),
            Product(name="Webcam 4K",            description="Auto-focus 4K camera with built-in ring light.",        price=Decimal("109.99"), stock=3,  category="Video",         emoji="📷"),
            Product(name="Laptop Stand",         description="Adjustable aluminium stand, fits 10–17\" laptops.",    price=Decimal("49.99"),  stock=15, category="Accessories",   emoji="💻"),
        ]
        db.add_all(demo)
        db.commit()
        logger.info("Seeded %d demo products.", len(demo))
    except Exception as exc:
        logger.warning("Seed skipped: %s", exc)
        db.rollback()
    finally:
        db.close()


# ═════════════════════════════════════════════════════════════════════════════
# ROUTES — Health
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Liveness / readiness probe",
)
def health_check():
    db_ok = check_db_connection()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database="connected" if db_ok else "unreachable",
        version=APP_VERSION,
    )


# ═════════════════════════════════════════════════════════════════════════════
# ROUTES — Products
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/products",
    response_model=list[ProductRead],
    tags=["Products"],
    summary="List all active products",
)
def list_products(
    search:   Optional[str] = Query(None,  description="Filter by name or description"),
    category: Optional[str] = Query(None,  description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    skip:  int = Query(0,   ge=0,  description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.is_active == True)

    if search:
        like = f"%{search}%"
        q = q.filter(
            Product.name.ilike(like) | Product.description.ilike(like)
        )
    if category:
        q = q.filter(Product.category.ilike(category))
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)

    return q.order_by(Product.id).offset(skip).limit(limit).all()


@app.get(
    "/products/{product_id}",
    response_model=ProductRead,
    tags=["Products"],
    summary="Get a single product by ID",
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return _get_product_or_404(product_id, db)


@app.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Products"],
    summary="Create a new product",
)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    # Check for duplicate name
    existing = db.query(Product).filter(Product.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A product named '{payload.name}' already exists.",
        )
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    logger.info("Created product id=%d name=%r", product.id, product.name)
    return product


@app.patch(
    "/products/{product_id}",
    response_model=ProductRead,
    tags=["Products"],
    summary="Partially update a product",
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = _get_product_or_404(product_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    logger.info("Updated product id=%d fields=%s", product_id, list(update_data.keys()))
    return product


@app.delete(
    "/products/{product_id}",
    response_model=MessageResponse,
    tags=["Products"],
    summary="Soft-delete a product (sets is_active=False)",
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_product_or_404(product_id, db)
    product.is_active = False
    db.commit()
    logger.info("Soft-deleted product id=%d", product_id)
    return MessageResponse(message=f"Product {product_id} deactivated.")


# ═════════════════════════════════════════════════════════════════════════════
# ROUTES — Cart
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/cart",
    response_model=CartSummary,
    tags=["Cart"],
    summary="Get the current session's cart",
)
def get_cart(
    x_session_id: str = Header(default="anonymous", alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    return _cart_summary(x_session_id, db)


@app.post(
    "/cart",
    response_model=CartSummary,
    status_code=status.HTTP_201_CREATED,
    tags=["Cart"],
    summary="Add a product to cart (or increment quantity if already present)",
)
def add_to_cart(
    payload: CartItemCreate,
    x_session_id: str = Header(default="anonymous", alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    # Validate product exists and is in stock
    product = _get_product_or_404(payload.product_id, db)
    if not product.is_active:
        raise HTTPException(status_code=400, detail="Product is not available.")
    if product.stock < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock} unit(s) in stock.",
        )

    # Upsert: increment qty if row exists, else insert
    existing = (
        db.query(CartItem)
        .filter(
            CartItem.session_id == x_session_id,
            CartItem.product_id == payload.product_id,
        )
        .first()
    )
    if existing:
        existing.quantity += payload.quantity
        logger.info("Cart: incremented item id=%d qty→%d", existing.id, existing.quantity)
    else:
        item = CartItem(
            session_id=x_session_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        db.add(item)
        logger.info("Cart: added product_id=%d for session=%r", payload.product_id, x_session_id)

    db.commit()
    return _cart_summary(x_session_id, db)


@app.patch(
    "/cart/{item_id}",
    response_model=CartSummary,
    tags=["Cart"],
    summary="Update the quantity of a cart item",
)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    x_session_id: str = Header(default="anonymous", alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    item = _get_cart_item_or_404(item_id, x_session_id, db)
    item.quantity = payload.quantity
    db.commit()
    logger.info("Cart: updated item id=%d qty→%d", item_id, payload.quantity)
    return _cart_summary(x_session_id, db)


@app.delete(
    "/cart/{item_id}",
    response_model=CartSummary,
    tags=["Cart"],
    summary="Remove a single item from the cart",
)
def remove_cart_item(
    item_id: int,
    x_session_id: str = Header(default="anonymous", alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    item = _get_cart_item_or_404(item_id, x_session_id, db)
    db.delete(item)
    db.commit()
    logger.info("Cart: removed item id=%d", item_id)
    return _cart_summary(x_session_id, db)


@app.delete(
    "/cart",
    response_model=MessageResponse,
    tags=["Cart"],
    summary="Clear all items from the current session's cart",
)
def clear_cart(
    x_session_id: str = Header(default="anonymous", alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    deleted = (
        db.query(CartItem)
        .filter(CartItem.session_id == x_session_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    logger.info("Cart: cleared %d item(s) for session=%r", deleted, x_session_id)
    return MessageResponse(message=f"Cart cleared ({deleted} item(s) removed).")