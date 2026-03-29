"""
schemas.py
----------
Pydantic v2 schemas used for request validation and response serialisation.

Naming convention
-----------------
  <Model>Base    – shared fields (used by Create and Read schemas)
  <Model>Create  – fields accepted on POST / PUT requests
  <Model>Update  – fields accepted on PATCH requests (all optional)
  <Model>Read    – fields returned in API responses (includes id, timestamps)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Product ───────────────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    name:        str     = Field(..., min_length=1, max_length=200,  description="Product name")
    description: Optional[str] = Field(None, max_length=2000,       description="Long-form description")
    price:       Decimal = Field(..., gt=0,        description="Unit price (must be > 0)")
    stock:       int     = Field(0,  ge=0,                           description="Units in stock")
    category:    Optional[str] = Field(None, max_length=100,         description="Category label")
    emoji:       Optional[str] = Field(None, max_length=8,           description="Display emoji")
    is_active:   bool    = Field(True,                               description="Soft-delete flag")


class ProductCreate(ProductBase):
    """Payload for POST /products"""
    pass


class ProductUpdate(BaseModel):
    """Payload for PATCH /products/{id} — all fields optional."""
    name:        Optional[str]     = Field(None, min_length=1, max_length=200)
    description: Optional[str]     = Field(None, max_length=2000)
    price:       Optional[Decimal] = Field(None, gt=0,)
    stock:       Optional[int]     = Field(None, ge=0)
    category:    Optional[str]     = Field(None, max_length=100)
    emoji:       Optional[str]     = Field(None, max_length=8)
    is_active:   Optional[bool]    = None


class ProductRead(ProductBase):
    """Shape of a product object returned by the API."""
    id:         int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── CartItem ──────────────────────────────────────────────────────────────────

class CartItemBase(BaseModel):
    product_id: int = Field(..., gt=0, description="ID of the product to add")
    quantity:   int = Field(1,  ge=1,  description="Number of units (min 1)")


class CartItemCreate(CartItemBase):
    """Payload for POST /cart — adds or increments a cart item."""
    pass


class CartItemUpdate(BaseModel):
    """Payload for PATCH /cart/{id} — update quantity only."""
    quantity: int = Field(..., ge=1, description="New quantity (min 1)")


class CartItemRead(CartItemBase):
    """Shape of a cart item returned by the API (includes joined product info)."""
    id:         int
    session_id: str
    added_at:   datetime
    updated_at: datetime

    # Nested product snapshot (avoids a second API call from the frontend)
    product:    Optional[ProductRead] = None

    model_config = ConfigDict(from_attributes=True)


# ── Aggregates ────────────────────────────────────────────────────────────────

class CartSummary(BaseModel):
    """Top-level cart response — items + computed totals."""
    items:       list[CartItemRead]
    item_count:  int     = Field(description="Total number of units across all lines")
    total_price: Decimal = Field(description="Sum of (price × quantity) for all items")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("total_price", mode="before")
    @classmethod
    def round_total(cls, v):
        return round(Decimal(str(v)), 2)


# ── Generic responses ─────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    """Generic success / info message."""
    message: str

class HealthResponse(BaseModel):
    """Response shape for GET /health."""
    status:   str
    database: str
    version:  str