"""Migration script to add position field to users table."""
import sqlite3
import sys

def migrate():
    """Add position column to users table."""
    try:
        conn = sqlite3.connect('usercontrol.db')
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'position' not in columns:
            print("Adding 'position' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN position VARCHAR(255)")
            conn.commit()
            print("✅ Migration completed successfully!")
        else:
            print("ℹ️ Column 'position' already exists. Nothing to do.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()

