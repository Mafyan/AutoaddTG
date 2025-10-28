"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from config import settings
import os

# ==================== MAIN DATABASE ====================

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

# ==================== LOGS DATABASE (SEPARATE) ====================

# Determine logs database URL
if "sqlite" in settings.DATABASE_URL:
    # For SQLite, create separate file
    base_dir = settings.BASE_DIR
    LOGS_DATABASE_URL = f"sqlite:///{base_dir}/admin_logs.db"
else:
    # For other databases, use separate database name
    # Example: postgresql://user:pass@localhost/logs_db
    LOGS_DATABASE_URL = os.getenv("LOGS_DATABASE_URL", settings.DATABASE_URL.replace("/usercontrol", "/admin_logs"))

# Create separate engine for logs
logs_engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if "sqlite" in LOGS_DATABASE_URL:
    logs_engine_kwargs["connect_args"] = {"check_same_thread": False}
    logs_engine_kwargs["poolclass"] = StaticPool
else:
    logs_engine_kwargs["pool_size"] = 10
    logs_engine_kwargs["max_overflow"] = 20
    logs_engine_kwargs["pool_timeout"] = 30
    logs_engine_kwargs["pool_recycle"] = 3600

logs_engine = create_engine(LOGS_DATABASE_URL, **logs_engine_kwargs)

# Session factory for logs
LogsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=logs_engine)

# Base class for logs models
LogsBase = declarative_base()

def get_logs_db():
    """
    Dependency for getting logs database session.
    
    Yields:
        Session: SQLAlchemy logs database session
    """
    db = LogsSessionLocal()
    try:
        yield db
    finally:
        db.close()

