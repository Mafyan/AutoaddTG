"""Database initialization script."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.database import engine, SessionLocal, Base
from database.models import User, Role, Chat, Admin
from database.crud import create_admin, create_role
from config import settings

def init_database():
    """Initialize database with tables and default data."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
    
    db = SessionLocal()
    try:
        # Create default admin if not exists
        print("\nCreating default admin...")
        existing_admin = db.query(Admin).filter(Admin.username == settings.DEFAULT_ADMIN_USERNAME).first()
        if not existing_admin:
            create_admin(
                db,
                username=settings.DEFAULT_ADMIN_USERNAME,
                password=settings.DEFAULT_ADMIN_PASSWORD,
                telegram_id=settings.DEFAULT_ADMIN_TELEGRAM_ID if settings.DEFAULT_ADMIN_TELEGRAM_ID != 0 else None
            )
            print(f"✓ Default admin created: {settings.DEFAULT_ADMIN_USERNAME}")
            print(f"  Password: {settings.DEFAULT_ADMIN_PASSWORD}")
            print("  ⚠️  ВАЖНО: Смените пароль после первого входа!")
        else:
            print("✓ Admin already exists")
        
        # Create default roles
        print("\nCreating default roles...")
        default_roles = [
            ("Управляющий", "Главный управляющий компании"),
            ("Сервис-менеджер", "Менеджер сервисного обслуживания"),
            ("Менеджер отдела продаж", "Менеджер по продажам"),
            ("Руководитель отдела продаж", "Руководитель отдела продаж"),
            ("Руководитель отдела сервиса", "Руководитель сервисного отдела"),
            ("Технический специалист", "Технический специалист"),
            ("HR-менеджер", "Менеджер по персоналу"),
            ("Бухгалтер", "Бухгалтер компании"),
        ]
        
        created_count = 0
        for role_name, role_desc in default_roles:
            existing_role = db.query(Role).filter(Role.name == role_name).first()
            if not existing_role:
                create_role(db, name=role_name, description=role_desc)
                created_count += 1
                print(f"  ✓ Created role: {role_name}")
        
        if created_count > 0:
            print(f"✓ Created {created_count} default roles")
        else:
            print("✓ All default roles already exist")
        
        print("\n" + "="*60)
        print("Database initialization completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Создайте файл .env на основе env.example")
        print("2. Укажите BOT_TOKEN от @BotFather")
        print("3. Укажите ADMIN_SECRET_KEY (любая длинная строка)")
        print("4. Запустите бота: python run_bot.py")
        print("5. Запустите админ-панель: python run_admin.py")
        print(f"6. Войдите в панель: http://localhost:{settings.ADMIN_PANEL_PORT}")
        print(f"   Логин: {settings.DEFAULT_ADMIN_USERNAME}")
        print(f"   Пароль: {settings.DEFAULT_ADMIN_PASSWORD}")
        print("="*60)
        
    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()

