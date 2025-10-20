"""Migration script to add last_links_request field to users table."""
import sqlite3
import sys

def migrate():
    """Add last_links_request column to users table."""
    try:
        conn = sqlite3.connect('usercontrol.db')
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_links_request' not in columns:
            print("Adding 'last_links_request' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN last_links_request TIMESTAMP")
            conn.commit()
            print("✅ Migration completed successfully!")
        else:
            print("ℹ️ Column 'last_links_request' already exists. Nothing to do.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()

