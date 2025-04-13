from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from .base import TimestampMixin

class Store(SQLModel, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    location: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool = Field(default=True)
    
    # Relationships
    stock_items: List["StoreStock"] = Relationship(back_populates="store")
    movements: List["StockMovement"] = Relationship(back_populates="store")
    suppliers: List["Supplier"] = Relationship(back_populates="stores", link_model="StoreSupplierLink")
    supply_records: List["SupplyRecord"] = Relationship(back_populates="store")