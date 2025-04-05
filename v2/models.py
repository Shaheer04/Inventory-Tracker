from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# --- Enums ---
class MovementType(str, Enum):
    STOCK_IN = "stock_in"
    SALE = "sale"
    

class UserRole(str, Enum):
    ADMIN = "admin"
    STORE_MANAGER = "store_manager"

# --- Models ---
class Store(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    location: str = Field(max_length=200)
    is_active: bool = Field(default=True)
    timezone: str = Field(default="UTC") 

    #   Relationships
    stock_items: List["StoreStock"] = Relationship(back_populates="store")
    movements : List["StockMovement"] = Relationship(back_populates="store")
    staff : List["User"] = Relationship(back_populates="assigned_store")

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    sku: str = Field(max_length=50, unique=True)
    description: Optional[str]
    category: Optional[str] = Field(max_length=50, default=None)
    unit: str = Field(max_length=20)  # "kg", "pieces", etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # Relationships
    store_stock : List["StoreStock"] = Relationship(back_populates="product")
    movements: List["StockMovement"] = Relationship(back_populates="product")

class StoreStock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    store_id: int = Field(foreign_key="store.id")
    current_quantity: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    product: List["Product"] = Relationship(back_populates="store_stock")
    store: Store = Relationship(back_populates="stock_items")

class StockMovement(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    store_id: int = Field(foreign_key="store.id")
    quantity: float  
    type: MovementType  
    notes: Optional[str]
    user_id: Optional[int] = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    product: Product = Relationship(back_populates="movements")
    store : Store = Relationship(back_populates="movements")   
    user : Optional["User"] = Relationship(back_populates="movements") 

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=100, unique=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.STORE_MANAGER)  # Enum: admin/store_manager
    store_id: Optional[int] = Field(foreign_key="store.id")

    # Relationships
    movements : List[StockMovement] = Relationship(back_populates="user")
    assigned_store : Optional[Store] = Relationship(back_populates="staff")
