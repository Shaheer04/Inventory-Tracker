from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session, select
import secrets
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.security import get_password_hash, verify_password
from core import limiter
from database import create_db_and_tables, get_session, engine
from models import User
from api import stores_router, products_router, stock_router, users_router

app = FastAPI(title="Store Inventory API")

# Setup rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    print("Database tables created.")
    # Create admin user if not exists
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.username == "admin")).first()
        if admin:        
            print(F"Admin user exists and key is : {admin.api_key}")
        else:
            api_key = secrets.token_urlsafe(32)
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                api_key=api_key,
                is_active=True,
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
            print(f"Admin user created with API key: {api_key}")
        
# Include routers
app.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)
app.include_router(
    stores_router,
    prefix="/stores",
    tags=["Stores"]
)
app.include_router(
    products_router,
    prefix="/products",
    tags=["Products"]
)
app.include_router(
    stock_router,
    prefix="/stores",
    tags=["Stock"]
)

@app.post("/generate-api-key")
def generate_api_key(
    username: str,
    password: str,
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Generate new API key
    user.api_key = secrets.token_urlsafe(32)
    session.add(user)
    session.commit()
    
    return {"api_key": user.api_key}

@app.get("/")
def read_root():
    return {"message": "Welcome to Store Inventory API"}