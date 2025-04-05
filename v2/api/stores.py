from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from models import Store
from database import get_session
from core.security import get_api_key
from models import User


router = APIRouter()

@router.post("/", response_model=Store)
def create_store(
    store: Store,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    session.add(store)
    session.commit()
    session.refresh(store)
    return store

@router.get("/", response_model=List[Store])
def get_stores(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    query = select(Store)
    if is_active is not None:
        query = query.where(Store.is_active == is_active)
    
    stores = session.exec(query.offset(skip).limit(limit)).all()
    return stores

@router.get("/{store_id}", response_model=Store)
def get_store(
    store_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    store = session.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

@router.put("/{store_id}", response_model=Store)
def update_store(
    store_id: int,
    store_data: Store,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_api_key)
):
    db_store = session.get(Store, store_id)
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Update store attributes
    store_data_dict = store_data.dict(exclude_unset=True)
    for key, value in store_data_dict.items():
        setattr(db_store, key, value)
    
    session.add(db_store)
    session.commit()
    session.refresh(db_store)
    return db_store