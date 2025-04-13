from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from .base import TimestampMixin

class Product(SQLModel, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    description: Optional[str] = None
    category : str = Field(default=None)
    unit_price: float = Field(default=0.0)
    is_active: bool = Field(default=True)
    manufacturer: Optional[str] = None
    barcode: Optional[str] = Field(default=None, index=True)
    weight: Optional[float] = None
    
    # Relationships
    store_stock: List["StoreStock"] = Relationship(back_populates="product")
    movements: List["StockMovement"] = Relationship(back_populates="product")
    supply_records: List["SupplyRecord"] = Relationship(back_populates="product")
