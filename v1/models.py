from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

# --- Enums ---
class MovementType(str, Enum):
    STOCK_IN = "stock_in"
    SALE = "sale"
    MANUAL_REMOVAL = "manual_removal"

# --- Models ---
class Store(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    location: Optional[str] = Field(max_length=200, default=None)
    
    # Relationships
    stock_movements: list["StockMovement"] = Relationship(back_populates="store")

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    sku: str = Field(max_length=50, unique=True)
    category: Optional[str] = Field(max_length=50, default=None)
    unit: str = Field(max_length=20)  # "kg", "pieces", etc.
    
    # Relationships
    movements: list["StockMovement"] = Relationship(back_populates="product")
    current_stock: Optional["CurrentStock"] = Relationship(back_populates="product")

class StockMovement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    store_id: int = Field(foreign_key="store.id")
    quantity: int
    type: MovementType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    product: Product = Relationship(back_populates="movements")
    store: Store = Relationship(back_populates="stock_movements")

class CurrentStock(SQLModel, table=True):
    product_id: int = Field(foreign_key="product.id", primary_key=True)
    quantity: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    product: Product = Relationship(back_populates="current_stock")