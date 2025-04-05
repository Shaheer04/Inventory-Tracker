from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional

from models import Product,User
from database import get_session
from core.security import get_api_key

router = APIRouter()

# Product endpoints
@router.post("/", response_model=Product)
def create_product(
    product: Product,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.get("/", response_model=List[Product])
def get_products(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    query = select(Product)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    
    products = session.exec(query.offset(skip).limit(limit)).all()
    return products

@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product_data: Product,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update product attributes
    product_data_dict = product_data.dict(exclude_unset=True)
    for key, value in product_data_dict.items():
        setattr(db_product, key, value)
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product