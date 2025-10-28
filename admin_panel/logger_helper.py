"""Helper functions for admin action logging."""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Request
from database.logs_crud import create_admin_log
from database.database import LogsSessionLocal
from database.models import Admin


def log_admin_action(
    admin: Admin,
    action: str,
    target: Optional[str] = None,
    details: Optional[str] = None,
    request: Optional[Request] = None
):
    """
    Log an admin action to the separate logs database.
    
    Args:
        admin: Admin object who performed the action
        action: Type of action (e.g., "Создание пользователя", "Блокировка пользователя")
        target: Target of the action (e.g., "user_id:52")
        details: Additional details about the action
        request: FastAPI Request object (optional, for IP address extraction)
    """
    ip_address = None
    if request:
        # Extract IP address from request
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if there are multiple
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None
    
    # Use separate logs database session
    logs_db = LogsSessionLocal()
    try:
        create_admin_log(
            db=logs_db,
            admin_name=admin.username,
            admin_id=admin.id,
            action=action,
            target=target,
            details=details,
            ip_address=ip_address
        )
    except Exception as e:
        # Don't fail the main action if logging fails
        print(f"Warning: Failed to log admin action: {e}")
    finally:
        logs_db.close()


# Action type constants for consistency
class AdminAction:
    """Constants for admin action types."""
    
    # Authentication
    LOGIN = "Вход в систему"
    LOGOUT = "Выход из системы"
    LOGIN_FAILED = "Неудачная попытка входа"
    
    # User management
    USER_APPROVE = "Одобрение пользователя"
    USER_REJECT = "Отклонение пользователя"
    USER_FIRE = "Увольнение пользователя"
    USER_EDIT = "Редактирование пользователя"
    USER_DELETE = "Удаление пользователя"
    USER_RESTORE = "Восстановление пользователя"
    USER_RESET_COOLDOWN = "Сброс ограничения на запрос ссылок"
    
    # Role management
    ROLE_CREATE = "Создание роли"
    ROLE_EDIT = "Редактирование роли"
    ROLE_DELETE = "Удаление роли"
    
    # Role group management
    ROLE_GROUP_CREATE = "Создание группы ролей"
    ROLE_GROUP_EDIT = "Редактирование группы ролей"
    ROLE_GROUP_DELETE = "Удаление группы ролей"
    ROLE_GROUP_ASSIGN_CHATS = "Привязка чатов к группе ролей"
    
    # Chat management
    CHAT_CREATE = "Создание чата"
    CHAT_EDIT = "Редактирование чата"
    CHAT_DELETE = "Удаление чата"
    CHAT_SYNC = "Синхронизация чата"
    CHAT_FETCH_PHOTO = "Получение фото чата"
    
    # Admin management
    ADMIN_CREATE = "Создание администратора"
    ADMIN_DELETE = "Удаление администратора"
    ADMIN_CHANGE_PASSWORD = "Изменение пароля администратора"
    
    # System
    EXPORT_LOGS = "Экспорт логов"
    VIEW_LOGS = "Просмотр логов"

