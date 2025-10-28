"""Migration to create separate admin_logs database for tracking admin actions."""
import sqlite3
from pathlib import Path

# Separate database for logs
LOGS_DB_FILE = "./admin_logs.db"

def migrate():
    """Create separate database for admin logs."""
    print(f"Creating separate logs database: {LOGS_DB_FILE}")
    
    conn = sqlite3.connect(LOGS_DB_FILE)
    cursor = conn.cursor()
    
    try:
        print("Creating 'admin_logs' table in separate database...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                admin_name VARCHAR(255) NOT NULL,
                admin_id INTEGER NOT NULL,
                action VARCHAR(255) NOT NULL,
                target VARCHAR(255),
                details TEXT,
                ip_address VARCHAR(45)
            )
        """)
        print("[OK] Table 'admin_logs' created successfully!")
        
        # Create indexes for better performance
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_logs_timestamp ON admin_logs(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_name ON admin_logs(admin_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON admin_logs(admin_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_logs(action)
        """)
        print("[OK] Indexes created successfully!")
        
        conn.commit()
        print("\n[SUCCESS] Separate logs database created successfully!")
        print(f"📁 Database file: {LOGS_DB_FILE}")
        print("📊 Admin logs will be stored separately from main database")
        print("✅ This improves performance and allows independent log management")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

