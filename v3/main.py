from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlmodel import Session, select
import secrets
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.security import get_password_hash, verify_password
from core import limiter
from database import create_db_and_tables, get_session, engine
from models import User
from api import stores_router, products_router, stock_router, users_router, reports_router, audit_logs_router
from cache import redis_client
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from websockets import manager
from locks import init_locks


app = FastAPI(title="Store Inventory API")

# Setup rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# Cache invalidation middleware
@app.middleware("http")
async def cache_and_events_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Invalidate cache and broadcast events on write operations
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        path = request.url.path
        
        # Extract store_id from path if present
        store_id = None
        if "/stores/" in path:
            path_parts = path.split("/")
            try:
                stores_index = path_parts.index("stores")
                if len(path_parts) > stores_index + 1:
                    potential_id = path_parts[stores_index + 1]
                    if potential_id.isdigit():
                        store_id = int(potential_id)
            except ValueError:
                pass
        
        # Clear specific cache keys based on path
        if "stores" in path:
            keys = redis_client.keys("*stores*")
            if keys:
                redis_client.delete(*keys)
            # Broadcast update to WebSocket clients
            if store_id:
                event_data = {"type": "store_update", "store_id": store_id}
                asyncio.create_task(manager.broadcast_to_store(store_id, event_data))
            else:
                event_data = {"type": "stores_update"}
                asyncio.create_task(manager.broadcast_global(event_data))
        
        elif "products" in path:
            keys = redis_client.keys("*products*")
            if keys:
                redis_client.delete(*keys)
            # Broadcast product update
            event_data = {"type": "products_update"}
            asyncio.create_task(manager.broadcast_global(event_data))
        
        elif "stock" in path:
            keys = redis_client.keys("*stock*")
            if keys:
                redis_client.delete(*keys)
            # Broadcast stock update
            if store_id:
                event_data = {"type": "stock_update", "store_id": store_id}
                asyncio.create_task(manager.broadcast_to_store(store_id, event_data))
        
        elif "users" in path:
            keys = redis_client.keys("*users*")
            if keys:
                redis_client.delete(*keys)
    
    return response

# WebSocket endpoint for real-time stock updates
@app.websocket("/ws/stock-updates")
async def stock_updates(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# WebSocket endpoint for store-specific stock updates
@app.websocket("/ws/stores/{store_id}/stock-updates")
async def store_stock_updates(websocket: WebSocket, store_id: int):
    await manager.connect(websocket, store_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, store_id)


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
app.include_router(
    reports_router,
    prefix="/reports",
    tags=["Reports"]
)
app.include_router(
    audit_logs_router,
    prefix="/audit-logs",
    tags=["Audit Logs"],
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