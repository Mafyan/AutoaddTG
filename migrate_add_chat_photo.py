"""Migration script to add chat_photo field to chats table."""
import sqlite3
from pathlib import Path

def migrate():
    """Add chat_photo column to chats table."""
    db_path = Path("usercontrol.db")
    
    if not db_path.exists():
        print(f"❌ Database file not found: {db_path}")
        print("   Run this script from the project root directory where usercontrol.db is located")
        return
    
    print(f"📊 Opening database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(chats)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'chat_photo' in columns:
            print("✅ Column 'chat_photo' already exists in 'chats' table")
        else:
            print("➕ Adding 'chat_photo' column to 'chats' table...")
            cursor.execute("ALTER TABLE chats ADD COLUMN chat_photo VARCHAR(500)")
            conn.commit()
            print("✅ Column 'chat_photo' added successfully!")
        
        # Verify
        cursor.execute("PRAGMA table_info(chats)")
        columns = cursor.fetchall()
        print(f"\n📋 Current chats table schema:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n✅ Migration completed!")

if __name__ == "__main__":
    print("="*60)
    print("🔄 DATABASE MIGRATION: Add chat_photo field")
    print("="*60)
    migrate()

