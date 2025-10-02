"""API routes for admin panel."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from telegram import Bot
from telegram.error import TelegramError

from database.database import get_db
from database.crud import (
    get_users, get_user_by_id, approve_user, reject_user, delete_user, update_user,
    get_roles, get_role_by_id, create_role, update_role, delete_role, assign_chats_to_role,
    get_chats, get_chat_by_id, create_chat, update_chat, delete_chat,
    get_chats_by_role, get_statistics, authenticate_admin, fire_user, get_fired_users,
    get_user_chats
)
from database.models import Admin
from admin_panel.auth import create_access_token, get_current_admin
from bot.utils import format_chat_links
from config import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# Pydantic models for API
class LoginRequest(BaseModel):
    username: str
    password: str

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    chat_ids: Optional[List[int]] = None

class ChatCreate(BaseModel):
    chat_name: str
    chat_link: Optional[str] = None
    chat_id: Optional[int] = None
    description: Optional[str] = None

class ChatUpdate(BaseModel):
    chat_name: Optional[str] = None
    chat_link: Optional[str] = None
    chat_id: Optional[int] = None
    description: Optional[str] = None

class UserUpdate(BaseModel):
    role_id: Optional[int] = None
    status: Optional[str] = None

# ==================== AUTHENTICATION ROUTES ====================

@router.post("/api/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Admin login endpoint."""
    admin = authenticate_admin(request.username, request.password, db)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ==================== PAGE ROUTES ====================

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/requests", response_class=HTMLResponse)
async def requests_page(request: Request):
    """Requests page."""
    return templates.TemplateResponse("requests.html", {"request": request})

@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Users page."""
    return templates.TemplateResponse("users.html", {"request": request})

@router.get("/roles", response_class=HTMLResponse)
async def roles_page(request: Request):
    """Roles page."""
    return templates.TemplateResponse("roles.html", {"request": request})

@router.get("/chats", response_class=HTMLResponse)
async def chats_page(request: Request):
    """Chats page."""
    return templates.TemplateResponse("chats.html", {"request": request})

# ==================== STATISTICS API ====================

@router.get("/api/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get statistics."""
    return get_statistics(db)

# ==================== USER API ====================

@router.get("/api/users")
async def api_get_users(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all users with optional status filter."""
    users = get_users(db, status=status, limit=1000)
    return [{
        "id": user.id,
        "telegram_id": user.telegram_id,
        "phone_number": user.phone_number,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": {"id": user.role.id, "name": user.role.name} if user.role else None,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None
    } for user in users]

@router.post("/api/requests/{user_id}/approve")
async def api_approve_request(
    user_id: int,
    request_data: dict,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Approve user request."""
    print(f"DEBUG: Received approval request for user {user_id}")
    print(f"DEBUG: Request data: {request_data}")
    
    role_id = request_data.get('role_id')
    if not role_id:
        print(f"DEBUG: Missing role_id in request")
        raise HTTPException(status_code=400, detail="role_id is required")
    
    print(f"DEBUG: Approving user {user_id} with role {role_id}")
    user = approve_user(db, user_id, role_id)
    if not user:
        print(f"DEBUG: User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    print(f"DEBUG: User {user_id} approved successfully")
    
    # Send notification to user via Telegram
    if user.telegram_id and settings.BOT_TOKEN:
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            chats = get_chats_by_role(db, role_id)
            message = (
                f"✅ Ваша заявка одобрена!\n\n"
                f"👤 Роль: {user.role.name}\n\n"
                f"{format_chat_links(chats)}\n"
                f"Используйте команду /mychats чтобы получить ссылки снова."
            )
            await bot.send_message(chat_id=user.telegram_id, text=message)
        except TelegramError as e:
            print(f"Failed to send notification: {e}")
    
    return {"status": "success", "message": "User approved"}

@router.post("/api/requests/{user_id}/reject")
async def api_reject_request(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Reject user request."""
    user = reject_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Send notification to user via Telegram
    if user.telegram_id and settings.BOT_TOKEN:
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            message = (
                "❌ Ваша заявка была отклонена.\n\n"
                "Обратитесь к администратору для получения дополнительной информации."
            )
            await bot.send_message(chat_id=user.telegram_id, text=message)
        except TelegramError as e:
            print(f"Failed to send notification: {e}")
    
    return {"status": "success", "message": "User rejected"}

@router.put("/api/users/{user_id}")
async def api_update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update user."""
    user = update_user(db, user_id, **user_update.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "message": "User updated"}

@router.post("/api/users/{user_id}/fire")
async def api_fire_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Fire user and remove from all chats."""
    user = fire_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove user from all Telegram chats
    if user.telegram_id and settings.BOT_TOKEN:
        try:
            print(f"DEBUG: Starting fire process for user {user_id} with telegram_id {user.telegram_id}")
            
            from bot.chat_manager import ChatManager
            chat_manager = ChatManager(settings.BOT_TOKEN)
            
            # Get all chats where user is a member
            user_chats = get_user_chats(db, user.telegram_id)
            print(f"DEBUG: Found {len(user_chats)} chat memberships for user")
            
            chat_ids = [chat.chat_id for chat in user_chats if chat.is_active == 'active']
            print(f"DEBUG: Active chat IDs: {chat_ids}")
            
            if chat_ids:
                # Remove user from all chats
                print(f"DEBUG: Attempting to remove user from {len(chat_ids)} chats")
                removal_results = await chat_manager.remove_user_from_all_chats(user.telegram_id, chat_ids)
                print(f"DEBUG: Removal results: {removal_results}")
            else:
                print("DEBUG: No active chats found for user")
            
            # Send notification to user
            bot = Bot(token=settings.BOT_TOKEN)
            message = (
                "🚫 Ваш доступ к системе был отозван.\n\n"
                "Вы были удалены из всех корпоративных чатов.\n"
                "Обратитесь к администратору для получения дополнительной информации."
            )
            await bot.send_message(chat_id=user.telegram_id, text=message)
            print(f"DEBUG: Notification sent to user {user.telegram_id}")
            
        except Exception as e:
            print(f"ERROR: Failed to remove user from chats or send notification: {e}")
            import traceback
            traceback.print_exc()
    
    return {"status": "success", "message": "User fired and removed from all chats"}

@router.post("/api/users/{user_id}/rehire")
async def api_rehire_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Rehire user (restore access)."""
    user = update_user(db, user_id, status='approved')
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Send notification to user via Telegram
    if user.telegram_id and settings.BOT_TOKEN:
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            message = (
                "✅ Ваш доступ к системе восстановлен!\n\n"
                "Используйте команду /mychats чтобы получить ссылки на ваши чаты."
            )
            await bot.send_message(chat_id=user.telegram_id, text=message)
        except TelegramError as e:
            print(f"Failed to send notification: {e}")
    
    return {"status": "success", "message": "User rehired"}

@router.delete("/api/users/{user_id}")
async def api_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete user."""
    if delete_user(db, user_id):
        return {"status": "success", "message": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")

# ==================== ROLE API ====================

@router.get("/api/roles")
async def api_get_roles(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all roles."""
    roles = get_roles(db, limit=1000)
    return [{
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "chats": [{"id": chat.id, "name": chat.chat_name} for chat in role.chats],
        "user_count": len(role.users)
    } for role in roles]

@router.post("/api/roles")
async def api_create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create new role."""
    new_role = create_role(db, name=role.name, description=role.description)
    return {"status": "success", "role_id": new_role.id}

@router.put("/api/roles/{role_id}")
async def api_update_role(
    role_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update role."""
    update_data = role_update.model_dump(exclude_unset=True)
    chat_ids = update_data.pop('chat_ids', None)
    
    role = update_role(db, role_id, **update_data)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if chat_ids is not None:
        assign_chats_to_role(db, role_id, chat_ids)
    
    return {"status": "success", "message": "Role updated"}

@router.delete("/api/roles/{role_id}")
async def api_delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete role."""
    if delete_role(db, role_id):
        return {"status": "success", "message": "Role deleted"}
    raise HTTPException(status_code=404, detail="Role not found")

# ==================== CHAT API ====================

@router.get("/api/chats")
async def api_get_chats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all chats."""
    chats = get_chats(db, limit=1000)
    return [{
        "id": chat.id,
        "chat_id": chat.chat_id,
        "chat_name": chat.chat_name,
        "chat_link": chat.chat_link,
        "description": chat.description,
        "roles": [{"id": role.id, "name": role.name} for role in chat.roles]
    } for chat in chats]

@router.post("/api/chats")
async def api_create_chat(
    chat: ChatCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create new chat."""
    new_chat = create_chat(
        db,
        chat_name=chat.chat_name,
        chat_link=chat.chat_link,
        chat_id=chat.chat_id,
        description=chat.description
    )
    return {"status": "success", "chat_id": new_chat.id}

@router.put("/api/chats/{chat_id}")
async def api_update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update chat."""
    chat = update_chat(db, chat_id, **chat_update.model_dump(exclude_unset=True))
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "message": "Chat updated"}

@router.delete("/api/chats/{chat_id}")
async def api_delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete chat."""
    if delete_chat(db, chat_id):
        return {"status": "success", "message": "Chat deleted"}
    raise HTTPException(status_code=404, detail="Chat not found")

