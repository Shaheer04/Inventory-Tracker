from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from database import get_session
from models import User, StockMovement, Store, StoreStock, Product
from core.security import get_api_key

# Create router
router = APIRouter()

# Endpoints
@router.get("/stock-levels", response_model=Dict[str, Any])
def get_stock_levels(
    store_id: Optional[int] = None,
    product_id: Optional[int] = None,
    min_stock: Optional[int] = None,
    max_stock: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user : User = Depends(get_api_key)
):
    """
    Get current stock levels with optional filtering parameters.
    """
    # Build query
    query = select(
        StoreStock, 
        Product
    ).join(
        Product, 
        StoreStock.product_id == Product.id
    )
    
    # Apply filters
    if store_id:
        # Check if store exists
        store = session.get(Store, store_id)
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        query = query.where(StoreStock.store_id == store_id)
    
    if product_id:
        query = query.where(StoreStock.product_id == product_id)
    
    if min_stock is not None:
        query = query.where(StoreStock.current_quantity >= min_stock)
        
    if max_stock is not None:
        query = query.where(StoreStock.current_quantity <= max_stock)
        
    # Create a query for counting that includes all filters
    base_query = query
    
    # Count total matching records
    count_query = select(func.count()).select_from(base_query.subquery())
    total_count = session.exec(count_query).one()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    results = session.exec(query).all()
    
    # Format response
    stock_levels = []
    for store_stock, product in results:
        stock_levels.append({
            "store_id": store_stock.store_id,
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "current_quantity": store_stock.current_quantity,
            "last_updated": store_stock.last_updated
        })
    
    return {
        "data": stock_levels,
        "total_count": total_count
    }

@router.get("/sales", response_model=Dict[str, Any])
def get_sales_report(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    store_id: Optional[int] = None,
    product_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    """
    Get sales report for a specific date range with optional filtering.
    """
    # Convert dates to datetime for comparison
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Build base query - only get "out" movements (sales)
    query = select(
        StockMovement.product_id,
        StockMovement.store_id,
        func.sum(StockMovement.quantity).label("quantity_sold"),
        func.sum(StockMovement.quantity * StockMovement.unit_price).label("total_value")
    ).where(
        (StockMovement.movement_type == "out") &
        (StockMovement.created_at >= start_datetime) &
        (StockMovement.created_at <= end_datetime)
    ).group_by(
        StockMovement.product_id,
        StockMovement.store_id
    )
    
    # Apply filters
    if product_id:
        query = query.where(StockMovement.product_id == product_id)
        
    if store_id:
        # Check if store exists
        store = session.get(Store, store_id)
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        query = query.where(StockMovement.store_id == store_id)
    
    # Get total sales value
    total_sales_query = select(
        func.sum(StockMovement.quantity * StockMovement.unit_price)
    ).where(
        (StockMovement.movement_type == "out") &
        (StockMovement.created_at >= start_datetime) &
        (StockMovement.created_at <= end_datetime)
    )
    
    if product_id:
        total_sales_query = total_sales_query.where(StockMovement.product_id == product_id)
        
    if store_id:
        total_sales_query = total_sales_query.where(StockMovement.store_id == store_id)
    
    total_sales = session.exec(total_sales_query).one() or 0
    
    # Count total matching records
    count_query = select(func.count()).select_from(
        select(StockMovement.product_id)
        .where(
            (StockMovement.movement_type == "out") &
            (StockMovement.created_at >= start_datetime) &
            (StockMovement.created_at <= end_datetime)
        )
        .group_by(StockMovement.product_id)
    )
    
    if store_id:
        count_query = count_query.where(StockMovement.store_id == store_id)
        
    total_count = session.exec(count_query).one()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    sales_data = session.exec(query).all()
    
    # Get product details
    product_ids = [item[0] for item in sales_data]  # First element is product_id
    products = {}
    if product_ids:
        products_query = select(Product).where(Product.id.in_(product_ids))
        product_results = session.exec(products_query).all()
        products = {p.id: {"name": p.name, "sku": p.sku} for p in product_results}
    
    # Get store details
    store_ids = [item[1] for item in sales_data]  # Second element is store_id
    stores = {}
    if store_ids:
        stores_query = select(Store).where(Store.id.in_(store_ids))
        store_results = session.exec(stores_query).all()
        stores = {s.id: s.name for s in store_results}
    
    # Format response
    sales_report = []
    for product_id, store_id, quantity_sold, total_value in sales_data:
        product_info = products.get(product_id, {"name": f"Product {product_id}", "sku": "Unknown"})
        store_name = stores.get(store_id, f"Store {store_id}")
        
        sales_report.append({
            "product_id": product_id,
            "product_name": product_info["name"],
            "sku": product_info["sku"],
            "store_id": store_id,
            "store_name": store_name,
            "quantity_sold": quantity_sold,
            "total_value": float(total_value)
        })
    
    return {
        "data": sales_report,
        "total_count": total_count,
        "total_sales": float(total_sales),
        "date_range": f"{start_date} to {end_date}"
    }

@router.get("/inventory-movements", response_model=Dict[str, Any])
def get_inventory_movements(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    store_id: Optional[int] = None,
    product_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    """
    Get detailed inventory movements for a specific date range.
    """
    # Convert dates to datetime for comparison
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Build query
    query = select(
        StockMovement,
        Product,
        Store
    ).join(
        Product,
        StockMovement.product_id == Product.id
    ).join(
        Store,
        StockMovement.store_id == Store.id
    ).where(
        (StockMovement.created_at >= start_datetime) &
        (StockMovement.created_at <= end_datetime)
    ).order_by(
        StockMovement.created_at.desc()
    )
    
    # Apply filters
    if product_id:
        query = query.where(StockMovement.product_id == product_id)
        
    if store_id:
        # Check if store exists
        store = session.get(Store, store_id)
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        query = query.where(StockMovement.store_id == store_id)
        
    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type)
    
    # Count total matching records
    count_query = select(func.count()).select_from(query)
    total_count = session.exec(count_query).one()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    results = session.exec(query).all()
    
    # Format response
    movements = []
    for movement, product, store in results:
        movements.append({
            "id": movement.id,
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "store_id": store.id,
            "store_name": store.name,
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "unit_price": float(movement.unit_price),
            "total_value": float(movement.quantity * movement.unit_price),
            "reference": movement.reference,
            "created_at": movement.created_at,
            "created_by": movement.created_by_user_id
        })
    
    return {
        "data": movements,
        "total_count": total_count,
        "date_range": f"{start_date} to {end_date}"
    }