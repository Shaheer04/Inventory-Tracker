from sqlmodel import SQLModel, create_engine, Session
from core.config import settings
from sqlalchemy.pool import QueuePool  
import contextlib


DB_URL = settings.DATABASE_URL
# Create write engine with connection pooling
write_engine = create_engine(
    DB_URL,
    poolclass=QueuePool,
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Maximum number of connections to create beyond pool_size
    pool_timeout=30,  # Timeout in seconds for getting a connection from the pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True  # Verify connections before using them from the pool
)

# Create read engine with connection pooling
read_engine = create_engine(
    DB_URL,
    poolclass=QueuePool,
    pool_size=10,  
    max_overflow=20,  
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)

# For backward compatibility
engine = write_engine

def create_db_and_tables():
    # Only create tables using the write engine
    SQLModel.metadata.create_all(write_engine)

# Session for write operations
def get_write_session():
    with Session(write_engine) as session:
        yield session

# Session for read operations
def get_read_session():
    with Session(read_engine) as session:
        yield session

# General session for backward compatibility
def get_session():
    with Session(write_engine) as session:
        yield session

# Alternative synchronous session context managers
@contextlib.contextmanager
def get_write_session_context():
    session = Session(write_engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@contextlib.contextmanager
def get_read_session_context():
    session = Session(read_engine)
    try:
        yield session
    finally:
        session.close()