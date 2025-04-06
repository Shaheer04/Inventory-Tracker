from datetime import datetime
from typing import Optional, List
from enum import Enum, auto
from sqlmodel import Field, SQLModel, Relationship
from .base import TimestampMixin
from sqlalchemy import UniqueConstraint

class MovementType(str, Enum):
    STOCK_IN = "stock_in"        # Initial stocking or replenishment
    SALE = "sale"                # Regular sale
    RETURN = "return"            # Customer return (increases stock)
    ADJUSTMENT = "adjustment"    # Manual inventory adjustment
    DAMAGE = "damage"            # Damaged items removal
    TRANSFER = "transfer"        # Transfer between stores

class StoreStock(SQLModel, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    store_id: int = Field(foreign_key="store.id")
    current_quantity: float = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Define a unique constraint for product_id and store_id
    __table_args__ = (UniqueConstraint("product_id", "store_id", name="store_product_constraint"),)   

    # Relationships
    product: "Product" = Relationship(back_populates="store_stock")
    store: "Store" = Relationship(back_populates="stock_items")

class StockMovement(SQLModel, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    store_id: int = Field(foreign_key="store.id")
    quantity: float
    type: MovementType
    notes: Optional[str] = None
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    reference_number: Optional[str] = Field(default=None, index=True)  # For invoices/POs
    
    # Relationships
    product: "Product" = Relationship(back_populates="movements")
    store: "Store" = Relationship(back_populates="movements") 
    user: Optional["User"] = Relationship(back_populates="movements")