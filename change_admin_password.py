"""Script to change admin password."""
import getpass
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.database import SessionLocal
from database.crud import get_admin_by_username, update_admin_password
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_strong_password():
    """Generate a strong random password."""
    import secrets
    import string
    
    # Generate 16 character password with letters, digits, and special chars
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(16))
    return password

def change_password():
    """Change admin password."""
    print("="*60)
    print("🔐 СМЕНА ПАРОЛЯ АДМИНИСТРАТОРА")
    print("="*60)
    
    # Get username
    username = input("\nВведите имя пользователя (по умолчанию: admin): ").strip()
    if not username:
        username = "admin"
    
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = get_admin_by_username(db, username)
        if not admin:
            print(f"\n❌ Администратор '{username}' не найден!")
            return
        
        print(f"\n✅ Администратор найден: {username}")
        
        # Ask for password option
        print("\nВыберите вариант:")
        print("1. Ввести свой пароль")
        print("2. Сгенерировать случайный безопасный пароль")
        
        choice = input("\nВаш выбор (1/2): ").strip()
        
        if choice == "2":
            # Generate random password
            new_password = generate_strong_password()
            print(f"\n🔑 Сгенерирован новый пароль:")
            print(f"{'='*60}")
            print(f"   {new_password}")
            print(f"{'='*60}")
            print("⚠️  СОХРАНИТЕ ЕГО В БЕЗОПАСНОМ МЕСТЕ!")
            
            confirm = input("\nПродолжить смену пароля? (y/n): ").strip().lower()
            if confirm != 'y':
                print("\n❌ Отменено")
                return
        else:
            # Manual password input
            while True:
                new_password = getpass.getpass("\nВведите новый пароль: ")
                if len(new_password) < 8:
                    print("❌ Пароль должен быть минимум 8 символов!")
                    continue
                
                confirm_password = getpass.getpass("Подтвердите пароль: ")
                if new_password != confirm_password:
                    print("❌ Пароли не совпадают!")
                    continue
                
                # Check password strength
                has_upper = any(c.isupper() for c in new_password)
                has_lower = any(c.islower() for c in new_password)
                has_digit = any(c.isdigit() for c in new_password)
                has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password)
                
                strength = sum([has_upper, has_lower, has_digit, has_special])
                
                if strength < 3:
                    print("\n⚠️  СЛАБЫЙ ПАРОЛЬ! Рекомендуется использовать:")
                    print("   - Заглавные и строчные буквы")
                    print("   - Цифры")
                    print("   - Специальные символы")
                    retry = input("\nПродолжить со слабым паролем? (y/n): ").strip().lower()
                    if retry != 'y':
                        continue
                
                break
        
        # Update password
        password_hash = pwd_context.hash(new_password)
        
        from database.models import Admin
        admin.password_hash = password_hash
        db.commit()
        
        print("\n" + "="*60)
        print("✅ ПАРОЛЬ УСПЕШНО ИЗМЕНЕН!")
        print("="*60)
        print(f"\nЛогин: {username}")
        print(f"Новый пароль установлен")
        print("\nТеперь вы можете войти в веб-панель с новым паролем.")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    change_password()

