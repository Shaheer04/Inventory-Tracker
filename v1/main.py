
from sqlmodel import Session
from models import Product, StockMovement, CurrentStock, MovementType
from database import engine, create_db_and_tables
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/test")
def test():
    return {"message": "API is working!"}

@app.post("/products")
def create_product(product: Product):
    with Session(engine) as session:
        product.current_stock = CurrentStock()
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    
@app.post("/movements")
def record_movements(movement: StockMovement):
    with Session(engine) as session:
        product = session.get(Product, movement.product_id)
        if movement.type == MovementType.STOCK_IN:  
            product.current_stock.quantity += movement.quantity  
        else:
            product.current_stock.quantity -= abs(movement.quantity)  # Fixed attribute access
        session.add(movement)
        session.commit()
        return {"message": "Movement recorded successfully"}


@app.get("/products/{product_id}/stock")
def get_stock(product_id: int):  # Fixed type annotation
    with Session(engine) as session:
        stock = session.get(CurrentStock, product_id)
        return stock


@app.get("/products")
def list_products():
    with Session(engine) as session:
        products = session.exec(Product.select()).all()
        return products