"""Migration to add group_chats association table for linking chats to role groups."""
import sqlite3

DATABASE_URL = "sqlite:///./usercontrol.db"

def migrate():
    conn = sqlite3.connect(DATABASE_URL.replace("sqlite:///", ""))
    cursor = conn.cursor()
    
    try:
        print("Creating 'group_chats' association table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                FOREIGN KEY (group_id) REFERENCES role_groups(id) ON DELETE CASCADE,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
                UNIQUE (group_id, chat_id)
            )
        """)
        print("[OK] Table 'group_chats' created successfully!")
        
        # Create index for better performance
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_group_chats_group_id ON group_chats(group_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_group_chats_chat_id ON group_chats(chat_id)
        """)
        print("[OK] Indexes created successfully!")
        
        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        print("Chats can now be assigned to role groups.")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

