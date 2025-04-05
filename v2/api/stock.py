from fastapi import APIRouter, Body, Depends, HTTPException, Request, Query
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from models import StoreStock, StockMovement, MovementType
from models import Store
from models import Product, User
from database import get_session
from core.security import get_api_key
from core import limiter

router = APIRouter()

# Store Stock endpoints
@router.get("/{store_id}/stock", response_model=List[Dict[str, Any]])
def get_store_stock(
    store_id: int,
    product_id: Optional[int] = None,
    below_min_stock: bool = False,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    # Check if store exists
    store = session.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Build query
    query = select(
        StoreStock, 
        Product
    ).join(
        Product, 
        StoreStock.product_id == Product.id
    ).where(
        StoreStock.store_id == store_id
    )
    
    if product_id:
        query = query.where(StoreStock.product_id == product_id)
    
    if below_min_stock:
        query = query.where(StoreStock.current_quantity < Product.min_stock_level)
    
    # Execute query
    results = session.exec(query).all()
    
    # Format response
    response = []
    for store_stock, product in results:
        response.append({
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "current_quantity": store_stock.current_quantity,
            "min_stock_level": product.min_stock_level,
            "last_updated": store_stock.last_updated
        })
    
    return response

# Stock Movement endpoints
@router.post("/{store_id}/stock", response_model=Dict[str, Any])
@limiter.limit("10/minute")
def record_store_stock(
    request: Request,
    store_id: int,
    movement_data: dict = Body(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    # Check if store exists
    store = session.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Check if product exists
    product_id = movement_data.get("product_id")
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Extract movement details
    quantity = movement_data.get("quantity", 0)
    movement_type = movement_data.get("type")
    notes = movement_data.get("notes")
    reference_number = movement_data.get("reference_number")
    
    if not isinstance(movement_type, MovementType):
        try:
            movement_type = MovementType(movement_type)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid movement type")
    
    # Get or create StoreStock
    store_stock = session.exec(
        select(StoreStock).where(
            StoreStock.store_id == store_id,
            StoreStock.product_id == product_id
        )
    ).first()
    
    if not store_stock:
        store_stock = StoreStock(
            store_id=store_id,
            product_id=product_id,
            current_quantity=0
        )
        session.add(store_stock)
    
    # Update stock level based on movement type
    if movement_type in [MovementType.STOCK_IN, MovementType.RETURN]:
        new_quantity = store_stock.current_quantity + quantity
    elif movement_type == MovementType.ADJUSTMENT:
        # Adjustment sets to a specific value
        new_quantity = quantity
    else:  # SALE, DAMAGE, TRANSFER
        new_quantity = store_stock.current_quantity - abs(quantity)
        if new_quantity < 0:
            raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Update the store stock
    store_stock.current_quantity = new_quantity
    store_stock.last_updated = datetime.utcnow()
    
    # Create a new StockMovement record
    stock_movement = StockMovement(
        product_id=product_id,
        store_id=store_id,
        quantity=quantity,
        type=movement_type,
        notes=notes,
        user_id=current_user.id if current_user else None,
        timestamp=datetime.utcnow(),
        reference_number=reference_number
    )
    
    # Add movement to DB
    session.add(stock_movement)
    
    # Commit both changes in a single transaction
    try:
        session.commit()
        session.refresh(stock_movement)
        return {
            "movement": {
                "id": stock_movement.id,
                "product_id": stock_movement.product_id,
                "product_name": product.name,
                "quantity": stock_movement.quantity,
                "type": stock_movement.type,
                "timestamp": stock_movement.timestamp,
                "user_id": stock_movement.user_id,
                "reference_number": stock_movement.reference_number
            },
            "current_stock": store_stock.current_quantity
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{store_id}/movements", response_model=List[Dict[str, Any]])
def get_store_movements(
    store_id: int,
    product_id: Optional[int] = None,
    movement_type: Optional[MovementType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    # Check if store exists
    store = session.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Build query
    query = select(
        StockMovement,
        Product
    ).join(
        Product,
        StockMovement.product_id == Product.id
    ).where(
        StockMovement.store_id == store_id
    ).order_by(
        StockMovement.timestamp.desc()
    )
    
    if product_id:
        query = query.where(StockMovement.product_id == product_id)
    
    if movement_type:
        query = query.where(StockMovement.type == movement_type)
    
    if start_date:
        query = query.where(StockMovement.timestamp >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.where(StockMovement.timestamp <= datetime.combine(end_date, datetime.max.time()))
    
    # Execute query with pagination
    results = session.exec(query.offset(skip).limit(limit)).all()
    
    # Format response
    response = []
    for movement, product in results:
        response.append({
            "id": movement.id,
            "product_id": movement.product_id,
            "product_name": product.name,
            "quantity": movement.quantity,
            "type": movement.type,
            "timestamp": movement.timestamp,
            "notes": movement.notes,
            "user_id": movement.user_id,
            "reference_number": movement.reference_number
        })
    
    return response