"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from config import settings

# Create engine with optimized pool settings
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,  # Verify connections before using them
}

# SQLite-specific settings
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    # For SQLite, use StaticPool to reuse the same connection
    engine_kwargs["poolclass"] = StaticPool
else:
    # For other databases, configure connection pool
    engine_kwargs["pool_size"] = 20  # Increased from default 5
    engine_kwargs["max_overflow"] = 40  # Increased from default 10
    engine_kwargs["pool_timeout"] = 60  # Increased timeout
    engine_kwargs["pool_recycle"] = 3600  # Recycle connections after 1 hour

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency for getting database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

