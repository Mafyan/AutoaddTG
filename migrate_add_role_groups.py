"""Migration script to add role_groups table and group_id field to roles table."""
import sqlite3
import sys

def migrate():
    """Add role_groups table and group_id column to roles table."""
    try:
        conn = sqlite3.connect('usercontrol.db')
        cursor = conn.cursor()
        
        # Check if role_groups table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='role_groups'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("Creating 'role_groups' table...")
            cursor.execute("""
                CREATE TABLE role_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX ix_role_groups_id ON role_groups (id)")
            cursor.execute("CREATE INDEX ix_role_groups_name ON role_groups (name)")
            print("✅ Table 'role_groups' created successfully!")
        else:
            print("ℹ️ Table 'role_groups' already exists.")
        
        # Check if group_id column exists in roles table
        cursor.execute("PRAGMA table_info(roles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'group_id' not in columns:
            print("Adding 'group_id' column to roles table...")
            cursor.execute("ALTER TABLE roles ADD COLUMN group_id INTEGER REFERENCES role_groups(id) ON DELETE SET NULL")
            print("✅ Column 'group_id' added successfully!")
        else:
            print("ℹ️ Column 'group_id' already exists in roles table.")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    migrate()

