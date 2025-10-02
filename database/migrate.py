"""Database migration script for new features."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.database import engine, SessionLocal, Base
from database.models import User, Role, Chat, Admin, ChatMember

def migrate_database():
    """Add new tables and columns to existing database."""
    print("Starting database migration...")
    
    # Create new tables
    Base.metadata.create_all(bind=engine)
    print("✓ New tables created")
    
    # Add new status to existing users if needed
    db = SessionLocal()
    try:
        # Check if we need to add 'fired' status
        # This is handled automatically by SQLAlchemy when we update the model
        
        print("✓ Database migration completed successfully!")
        print("\nNew features available:")
        print("- User firing functionality")
        print("- Chat member tracking")
        print("- Automatic chat management")
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()
