"""Migration to add admin_logs table for tracking admin actions."""
import sqlite3
from datetime import datetime

DATABASE_URL = "sqlite:///./usercontrol.db"

def migrate():
    conn = sqlite3.connect(DATABASE_URL.replace("sqlite:///", ""))
    cursor = conn.cursor()
    
    try:
        print("Creating 'admin_logs' table...")
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
        print("\n[SUCCESS] Migration completed successfully!")
        print("Admin logs system is now ready to track all admin actions.")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

