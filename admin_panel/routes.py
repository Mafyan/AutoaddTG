"""API routes for admin panel."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from telegram import Bot
from telegram.error import TelegramError
import os
import uuid
import logging
from pathlib import Path

from database.database import get_db, get_logs_db
from database.crud import (
    get_users, get_user_by_id, approve_user, reject_user, delete_user, update_user,
    get_roles, get_role_by_id, create_role, update_role, delete_role, assign_chats_to_role,
    get_chats, get_chat_by_id, create_chat, update_chat, delete_chat,
    get_chats_by_role, get_statistics, authenticate_admin, fire_user, get_fired_users,
    get_user_chats, add_user_to_role_chats, get_user_chat_memberships,
    get_all_admins, get_admin_by_id, create_admin, delete_admin, update_admin_password,
    get_admin_by_username
)
from database.logs_crud import (
    get_admin_logs, count_admin_logs, get_unique_admin_names_from_logs,
    get_unique_actions_from_logs
)
from database.models import Admin, ChatMember
from admin_panel.auth import create_access_token, get_current_admin
from bot.utils import format_chat_links
from config import settings

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# Pydantic models for API
class LoginRequest(BaseModel):
    username: str
    password: str

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    group_id: Optional[int] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    group_id: Optional[int] = None
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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[int] = None
    status: Optional[str] = None

class AdminCreate(BaseModel):
    username: str
    password: str
    telegram_id: Optional[int] = None

class AdminPasswordUpdate(BaseModel):
    password: str

# ==================== AUTHENTICATION ROUTES ====================

@router.post("/api/login")
async def login(login_request: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Admin login endpoint."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    admin = authenticate_admin(login_request.username, login_request.password, db)
    if not admin:
        # Log failed login attempt
        # Create a temporary admin object for logging
        from database.models import Admin as AdminModel
        temp_admin = AdminModel(id=0, username=login_request.username)
        log_admin_action(
            admin=temp_admin,
            action=AdminAction.LOGIN_FAILED,
            details=f"Failed login attempt for username: {login_request.username}",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Log successful login
    log_admin_action(
        admin=admin,
        action=AdminAction.LOGIN,
        details="Successful login",
        request=request
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

@router.get("/role-groups", response_class=HTMLResponse)
async def role_groups_page(request: Request):
    """Role groups page."""
    return templates.TemplateResponse("role_groups.html", {"request": request})

@router.get("/roles", response_class=HTMLResponse)
async def roles_page(request: Request):
    """Roles page."""
    return templates.TemplateResponse("roles.html", {"request": request})

@router.get("/chats", response_class=HTMLResponse)
async def chats_page(request: Request):
    """Chats page."""
    return templates.TemplateResponse("chats.html", {"request": request})

@router.get("/admins", response_class=HTMLResponse)
async def admins_page(request: Request):
    """Admins page."""
    return templates.TemplateResponse("admins.html", {"request": request})

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
        "position": user.position,
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
    
    # Add user to role chats in database
    if user.telegram_id:
        try:
            print(f"\n{'='*60}")
            print(f"✅ APPROVING USER {user_id}")
            print(f"{'='*60}")
            print(f"👤 User: {user.first_name} {user.last_name or ''}")
            print(f"📱 Telegram ID: {user.telegram_id}")
            print(f"👔 Role ID: {role_id}")
            print(f"{'='*60}\n")
            
            # Add user to role chats in database
            print(f"📝 Step 1: Adding user to role chats in database...")
            success = add_user_to_role_chats(db, user_id)
            print(f"{'✅' if success else '❌'} Database update: {success}\n")
            
            # Ensure user is not banned from chats
            from bot.chat_manager import ChatManager
            chat_manager = ChatManager(settings.BOT_TOKEN)
            
            # Get all chats for this role
            chats = get_chats_by_role(db, role_id)
            print(f"📊 Step 2: Found {len(chats)} chats for role {role_id}")
            
            # Unban user from each Telegram chat (if they were banned)
            print(f"🚀 Step 3: Ensuring user is not banned in chats...\n")
            for idx, chat in enumerate(chats, 1):
                if chat.chat_id:  # Only if chat has Telegram ID
                    try:
                        print(f"  [{idx}/{len(chats)}] Chat: {chat.chat_name} (ID: {chat.chat_id})")
                        # Ensure user is not banned (does NOT add them - they must join via invite link)
                        success = await chat_manager.ensure_user_not_banned(chat.chat_id, user.telegram_id)
                        if success:
                            print(f"  ✅ User is not banned\n")
                        else:
                            print(f"  ⚠️  Could not verify ban status\n")
                        
                        # Rate limiting: small delay between chats
                        if idx < len(chats):
                            import asyncio
                            await asyncio.sleep(0.5)
                            
                    except Exception as e:
                        print(f"  ❌ Error: {e}\n")
                else:
                    print(f"  [{idx}/{len(chats)}] Chat: {chat.chat_name} - ⚠️  No Telegram ID, skipping\n")
            
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"❌ ERROR in chat management: {e}")
            import traceback
            traceback.print_exc()
    
    # Send notification to user via Telegram with temporary invite links
    if user.telegram_id and settings.BOT_TOKEN:
        try:
            from bot.chat_manager import ChatManager
            chat_manager = ChatManager(settings.BOT_TOKEN)
            
            # Get temporary invite links (12 hours, single use)
            print(f"📨 Creating temporary invite links (12 hours) for user {user_id}...")
            temp_links = await chat_manager.get_role_temporary_invite_links(role_id, hours=12)
            
            # Format message with temporary links
            message = (
                f"✅ Ваша заявка одобрена!\n\n"
                f"👤 Роль: {user.role.name}\n\n"
                f"🔗 Ваши персональные ссылки на чаты:\n"
                f"⏰ Срок действия: 12 часов\n"
                f"👤 Использований: 1 раз\n\n"
            )
            
            # Add links
            for idx, link_info in enumerate(temp_links, 1):
                if link_info['success'] and link_info['invite_link']:
                    message += f"{idx}. {link_info['chat_name']}\n{link_info['invite_link']}\n\n"
                else:
                    message += f"{idx}. {link_info['chat_name']} - ⚠️ Ошибка создания ссылки\n\n"
            
            message += (
                f"⚠️ ВАЖНО:\n"
                f"• Ссылки действуют только 12 часов\n"
                f"• Каждая ссылка одноразовая (1 использование)\n"
                f"• Присоединяйтесь к чатам как можно скорее!\n\n"
                f"Если ссылка истекла, обратитесь к администратору."
            )
            
            bot = Bot(token=settings.BOT_TOKEN)
            await bot.send_message(chat_id=user.telegram_id, text=message, disable_web_page_preview=True)
            print(f"✅ Temporary links sent to user {user.telegram_id}")
            
        except TelegramError as e:
            print(f"Failed to send notification: {e}")
        except Exception as e:
            print(f"Error creating temporary links: {e}")
            import traceback
            traceback.print_exc()
    
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
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update user."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    # Get user BEFORE update to check if role changed
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_status = user.status
    old_role_id = user.role_id
    new_role_id = user_update.role_id
    
    # Check if role is being changed
    role_changed = new_role_id is not None and old_role_id != new_role_id
    
    # If role is changing, remove user from old role chats first
    if role_changed and user.telegram_id and old_role_id:
        print(f"\n{'='*60}")
        print(f"🔄 CHANGING ROLE FOR USER {user_id}")
        print(f"{'='*60}")
        print(f"👤 User: {user.first_name} {user.last_name or ''}")
        print(f"📱 Telegram ID: {user.telegram_id}")
        print(f"👔 Old Role ID: {old_role_id} → New Role ID: {new_role_id}")
        print(f"{'='*60}\n")
        
        try:
            # Get chats from OLD role
            old_role_chats = get_chats_by_role(db, old_role_id)
            old_chat_ids = [chat.chat_id for chat in old_role_chats if chat.chat_id]
            
            if old_chat_ids and settings.BOT_TOKEN:
                print(f"🚀 Removing user from {len(old_chat_ids)} chats of old role...")
                
                from bot.chat_manager import ChatManager
                chat_manager = ChatManager(settings.BOT_TOKEN)
                
                # Remove user from all old role chats
                removal_results = await chat_manager.remove_user_from_all_chats(user.telegram_id, old_chat_ids)
                
                print(f"\n📊 REMOVAL RESULTS:")
                for chat_id, result in removal_results.items():
                    status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                    error_msg = f" - {result['error']}" if result['error'] else ""
                    print(f"  Chat {chat_id}: {status}{error_msg}")
                print()
                
                success_count = sum(1 for r in removal_results.values() if r['success'])
                print(f"✅ Removed from {success_count}/{len(old_chat_ids)} old role chats\n")
            else:
                print(f"⚠️  No chats found for old role {old_role_id}\n")
                
        except Exception as e:
            print(f"❌ ERROR removing from old role chats: {e}")
            import traceback
            traceback.print_exc()
    
    # Update user with new data
    user = update_user(db, user_id, **user_update.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If role was changed and user is approved, add to new role chats
    if role_changed and user.telegram_id and new_role_id and user.status == 'approved':
        try:
            print(f"➕ Adding user to new role chats...")
            
            # Add user to new role chats in database
            success = add_user_to_role_chats(db, user_id)
            print(f"{'✅' if success else '❌'} Database update: {success}\n")
            
            # Ensure user is not banned from new chats
            if settings.BOT_TOKEN:
                from bot.chat_manager import ChatManager
                chat_manager = ChatManager(settings.BOT_TOKEN)
                
                # Get all chats for new role
                new_role_chats = get_chats_by_role(db, new_role_id)
                print(f"📊 Found {len(new_role_chats)} chats for new role {new_role_id}")
                
                # Unban user from each Telegram chat (if they were banned)
                print(f"🚀 Ensuring user is not banned in new role chats...\n")
                for idx, chat in enumerate(new_role_chats, 1):
                    if chat.chat_id:
                        try:
                            print(f"  [{idx}/{len(new_role_chats)}] Chat: {chat.chat_name} (ID: {chat.chat_id})")
                            success = await chat_manager.ensure_user_not_banned(chat.chat_id, user.telegram_id)
                            if success:
                                print(f"  ✅ User is not banned\n")
                            else:
                                print(f"  ⚠️  Could not verify ban status\n")
                            
                            # Rate limiting
                            if idx < len(new_role_chats):
                                import asyncio
                                await asyncio.sleep(0.5)
                                
                        except Exception as e:
                            print(f"  ❌ Error: {e}\n")
                    else:
                        print(f"  [{idx}/{len(new_role_chats)}] Chat: {chat.chat_name} - ⚠️  No Telegram ID\n")
                
                # Send notification with new temporary invite links
                print(f"📨 Creating temporary invite links (12 hours) for new role...")
                temp_links = await chat_manager.get_role_temporary_invite_links(new_role_id, hours=12)
                
                # Format message
                message = (
                    f"🔄 Ваша роль была изменена!\n\n"
                    f"👤 Новая роль: {user.role.name}\n\n"
                    f"🔗 Ваши персональные ссылки на чаты:\n"
                    f"⏰ Срок действия: 12 часов\n"
                    f"👤 Использований: 1 раз\n\n"
                )
                
                # Add links
                for idx, link_info in enumerate(temp_links, 1):
                    if link_info['success'] and link_info['invite_link']:
                        message += f"{idx}. {link_info['chat_name']}\n{link_info['invite_link']}\n\n"
                    else:
                        message += f"{idx}. {link_info['chat_name']} - ⚠️ Ошибка создания ссылки\n\n"
                
                message += (
                    f"⚠️ ВАЖНО:\n"
                    f"• Вы были удалены из чатов старой роли\n"
                    f"• Ссылки действуют только 12 часов\n"
                    f"• Каждая ссылка одноразовая (1 использование)\n"
                    f"• Присоединяйтесь к чатам как можно скорее!\n\n"
                    f"Если ссылка истекла, обратитесь к администратору."
                )
                
                try:
                    bot = Bot(token=settings.BOT_TOKEN)
                    await bot.send_message(chat_id=user.telegram_id, text=message, disable_web_page_preview=True)
                    print(f"✅ Temporary links sent to user {user.telegram_id}\n")
                except TelegramError as e:
                    print(f"❌ Failed to send notification: {e}\n")
                
                print(f"{'='*60}\n")
                
        except Exception as e:
            print(f"❌ ERROR adding to new role chats: {e}")
            import traceback
            traceback.print_exc()
    
    # Log the action
    details_parts = []
    if user_update.status and old_status != user_update.status:
        if user_update.status == 'approved':
            action = AdminAction.USER_APPROVE
            details_parts.append(f"Статус: {old_status} → {user_update.status}")
        elif user_update.status == 'rejected':
            action = AdminAction.USER_REJECT
            details_parts.append(f"Статус: {old_status} → {user_update.status}")
        else:
            action = AdminAction.USER_EDIT
            details_parts.append(f"Статус: {old_status} → {user_update.status}")
    else:
        action = AdminAction.USER_EDIT
    
    if role_changed:
        old_role_name = get_role_by_id(db, old_role_id).name if old_role_id else "Нет"
        new_role_name = get_role_by_id(db, new_role_id).name if new_role_id else "Нет"
        details_parts.append(f"Роль: {old_role_name} → {new_role_name}")
    
    if user_update.first_name:
        details_parts.append(f"Имя: {user_update.first_name}")
    if user_update.last_name:
        details_parts.append(f"Фамилия: {user_update.last_name}")
    
    log_admin_action(
        admin=current_admin,
        action=action,
        target=f"user_id:{user_id}",
        details=f"{user.first_name} {user.last_name or ''} ({user.phone_number}). " + ", ".join(details_parts),
        request=request
    )
    
    return {"status": "success", "message": "User updated"}

@router.post("/api/users/{user_id}/fire")
async def api_fire_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Fire user and remove from all chats."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    # ✅ FIX: Get user and active chats BEFORE firing
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get active chats BEFORE marking them as 'left'
    # Use role-based chats instead of chat_members table (more reliable)
    active_chat_ids = []
    if user.telegram_id and user.role_id:
        role_chats = get_chats_by_role(db, user.role_id)
        active_chat_ids = [chat.chat_id for chat in role_chats if chat.chat_id]
        print(f"DEBUG: Found {len(active_chat_ids)} chats from role {user.role_id} BEFORE firing")
    elif user.telegram_id:
        # Fallback: try to get from chat_members table
        user_chats = get_user_chats(db, user.telegram_id)
        active_chat_ids = [chat.chat_id for chat in user_chats if chat.is_active == 'active']
        print(f"DEBUG: Found {len(active_chat_ids)} active chats from chat_members BEFORE firing")
    
    # Now fire the user (this will mark chats as 'left' in DB)
    user = fire_user(db, user_id)
    
    # Remove user from all Telegram chats
    if user.telegram_id and settings.BOT_TOKEN:
        try:
            print(f"\n{'='*60}")
            print(f"🔥 FIRING USER {user_id}")
            print(f"{'='*60}")
            print(f"👤 User Telegram ID: {user.telegram_id}")
            print(f"📝 User Name: {user.first_name} {user.last_name or ''}")
            print(f"📊 Active Chat IDs: {active_chat_ids}")
            print(f"🔢 Total Chats: {len(active_chat_ids)}")
            print(f"{'='*60}\n")
            
            from bot.chat_manager import ChatManager
            chat_manager = ChatManager(settings.BOT_TOKEN)
            
            if active_chat_ids:
                # Remove user from all chats
                print(f"🚀 Starting removal from {len(active_chat_ids)} chats...")
                removal_results = await chat_manager.remove_user_from_all_chats(user.telegram_id, active_chat_ids)
                
                print(f"\n📊 REMOVAL RESULTS:")
                for chat_id, result in removal_results.items():
                    status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                    error_msg = f" - {result['error']}" if result['error'] else ""
                    print(f"  Chat {chat_id}: {status}{error_msg}")
                print()
                
                # Count successes
                success_count = sum(1 for r in removal_results.values() if r['success'])
                print(f"✅ Successfully removed from {success_count}/{len(active_chat_ids)} chats")
            else:
                print("⚠️  WARNING: No active chats found for user")
            
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
    
    # Log the action
    log_admin_action(
        admin=current_admin,
        action=AdminAction.USER_FIRE,
        target=f"user_id:{user_id}",
        details=f"Уволен пользователь: {user.first_name} {user.last_name or ''} ({user.phone_number}). Удален из {len(active_chat_ids)} чатов.",
        request=request
    )
    
    return {"status": "success", "message": "User fired and removed from all chats"}

@router.post("/api/users/{user_id}/reset-link-cooldown")
async def api_reset_link_cooldown(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Reset user's link request cooldown (allows immediate link request)."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Reset the last_links_request to None
    user.last_links_request = None
    db.commit()
    
    logger.info(f"Admin {current_admin.username} reset link cooldown for user {user_id}")
    
    # Log the action
    log_admin_action(
        admin=current_admin,
        action=AdminAction.USER_RESET_COOLDOWN,
        target=f"user_id:{user_id}",
        details=f"Сброшено ограничение на запрос ссылок для: {user.first_name} {user.last_name or ''} ({user.phone_number})",
        request=request
    )
    
    # Send notification to user if they have telegram_id
    if user.telegram_id and settings.BOT_TOKEN:
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            message = (
                "✅ Администратор сбросил ограничение на запрос ссылок.\n\n"
                "Теперь вы можете запросить новые ссылки на чаты командой /mychats"
            )
            await bot.send_message(chat_id=user.telegram_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send notification to user {user.telegram_id}: {e}")
    
    return {
        "status": "success", 
        "message": "Link cooldown reset successfully",
        "user_id": user_id
    }

@router.post("/api/chats/sync")
async def api_sync_chats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Sync bot chats with database."""
    print("DEBUG: Starting chat sync process")
    
    if not settings.BOT_TOKEN:
        print("ERROR: Bot token not configured")
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    try:
        print("DEBUG: Importing ChatManager")
        from bot.chat_manager import ChatManager
        chat_manager = ChatManager(settings.BOT_TOKEN)
        
        print("DEBUG: Starting sync process")
        # Sync chats to database
        results = await chat_manager.sync_chats_to_database(db)
        print(f"DEBUG: Sync completed with results: {results}")
        
        return {
            "status": "success", 
            "message": "Chats synced successfully",
            "results": results
        }
        
    except Exception as e:
        print(f"ERROR: Error syncing chats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to sync chats: {str(e)}")

@router.post("/api/chats/sync-members")
async def api_sync_chat_members(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Sync members for all chats."""
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    try:
        from bot.chat_manager import ChatManager
        chat_manager = ChatManager(settings.BOT_TOKEN)
        
        # Sync all chat members
        await chat_manager.sync_all_chat_members()
        
        return {
            "status": "success", 
            "message": "Chat members synced successfully"
        }
        
    except Exception as e:
        print(f"Error syncing chat members: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync chat members: {str(e)}")

@router.post("/api/chats/start-auto-sync")
async def api_start_auto_sync(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Start automatic member synchronization."""
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    try:
        from bot.chat_manager import ChatManager
        chat_manager = ChatManager(settings.BOT_TOKEN)
        
        # Start auto sync
        await chat_manager.start_auto_sync()
        
        return {
            "status": "success", 
            "message": "Automatic synchronization started"
        }
        
    except Exception as e:
        print(f"Error starting auto sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start auto sync: {str(e)}")

@router.post("/api/chats/stop-auto-sync")
async def api_stop_auto_sync(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Stop automatic member synchronization."""
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    try:
        from bot.chat_manager import ChatManager
        chat_manager = ChatManager(settings.BOT_TOKEN)
        
        # Stop auto sync
        await chat_manager.stop_auto_sync()
        
        return {
            "status": "success", 
            "message": "Automatic synchronization stopped"
        }
        
    except Exception as e:
        print(f"Error stopping auto sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop auto sync: {str(e)}")

@router.post("/api/chats/force-refresh-members")
async def api_force_refresh_members(
    chat_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Force refresh members for a specific chat."""
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    try:
        from bot.chat_manager import ChatManager
        chat_manager = ChatManager(settings.BOT_TOKEN)
        
        # Get all members from the chat
        members = await chat_manager.get_chat_members_from_telegram(chat_id)
        
        return {
            "status": "success", 
            "message": f"Found {len(members)} members in chat {chat_id}",
            "members": members
        }
        
    except Exception as e:
        print(f"Error refreshing members: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh members: {str(e)}")

@router.get("/api/users/{user_id}/chats")
async def api_get_user_chats(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get user's chat memberships."""
    try:
        # Get user info
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        print(f"DEBUG: Getting chats for user {user_id}")
        print(f"DEBUG: User telegram_id: {user.telegram_id}")
        print(f"DEBUG: User role_id: {user.role_id}")
        print(f"DEBUG: User status: {user.status}")
        
        # Get user's chat memberships
        memberships = get_user_chat_memberships(db, user_id)
        print(f"DEBUG: Found {len(memberships)} memberships")
        
        # If no memberships and user is approved, try to add them to role chats
        if len(memberships) == 0 and user.status == 'approved' and user.role_id and user.telegram_id:
            print(f"DEBUG: User has no memberships, trying to add to role chats")
            success = add_user_to_role_chats(db, user_id)
            print(f"DEBUG: Added to role chats: {success}")
            
            # Get memberships again
            memberships = get_user_chat_memberships(db, user_id)
            print(f"DEBUG: After adding to role chats: {len(memberships)} memberships")
        
        return {
            "status": "success",
            "memberships": memberships,
            "user_info": {
                "telegram_id": user.telegram_id,
                "role_id": user.role_id,
                "status": user.status
            }
        }
    except Exception as e:
        print(f"Error getting user chats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user chats: {str(e)}")

@router.post("/api/users/{user_id}/remove-from-chat")
async def api_remove_user_from_chat(
    user_id: int,
    chat_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Remove user from specific chat."""
    try:
        user = get_user_by_id(db, user_id)
        if not user or not user.telegram_id:
            raise HTTPException(status_code=404, detail="User not found or no Telegram ID")
        
        # Remove from database
        chat_member = db.query(ChatMember).filter(
            ChatMember.chat_id == chat_id,
            ChatMember.user_telegram_id == user.telegram_id
        ).first()
        
        if chat_member:
            chat_member.is_active = 'left'
            db.commit()
        
        # Try to remove from actual Telegram chat
        if settings.BOT_TOKEN:
            try:
                from bot.chat_manager import ChatManager
                chat_manager = ChatManager(settings.BOT_TOKEN)
                await chat_manager.remove_user_from_chat(chat_id, user.telegram_id)
            except Exception as e:
                print(f"Error removing from Telegram chat: {e}")
        
        return {
            "status": "success",
            "message": f"User removed from chat {chat_id}"
        }
        
    except Exception as e:
        print(f"Error removing user from chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove user from chat: {str(e)}")

@router.get("/api/debug/role-chat-connections")
async def api_debug_role_chat_connections(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Debug role-chat connections."""
    try:
        # Get all roles
        roles = get_roles(db)
        role_data = []
        
        for role in roles:
            # Get chats for this role
            chats = get_chats_by_role(db, role.id)
            role_data.append({
                "role_id": role.id,
                "role_name": role.name,
                "chats": [{"chat_id": chat.chat_id, "chat_name": chat.chat_name} for chat in chats]
            })
        
        # Get all chats
        all_chats = get_chats(db)
        chat_data = [{"chat_id": chat.chat_id, "chat_name": chat.chat_name} for chat in all_chats]
        
        return {
            "status": "success",
            "roles": role_data,
            "all_chats": chat_data
        }
    except Exception as e:
        print(f"Error getting role-chat connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get role-chat connections: {str(e)}")

@router.post("/api/users/{user_id}/rehire")
async def api_rehire_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Rehire user (restore access)."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    user = update_user(db, user_id, status='approved')
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add user back to role chats
    if user.telegram_id and user.role_id:
        try:
            success = add_user_to_role_chats(db, user_id)
            print(f"DEBUG: Added user back to role chats: {success}")
            
            # Ensure user is not banned in chats
            from bot.chat_manager import ChatManager
            chat_manager = ChatManager(settings.BOT_TOKEN)
            
            # Get all chats for this role
            chats = get_chats_by_role(db, user.role_id)
            print(f"DEBUG: Found {len(chats)} chats for role {user.role_id}")
            
            # Unban user from each Telegram chat (if they were banned)
            for chat in chats:
                if chat.chat_id:  # Only if chat has Telegram ID
                    try:
                        success = await chat_manager.ensure_user_not_banned(chat.chat_id, user.telegram_id)
                        if success:
                            print(f"DEBUG: User is not banned in chat {chat.chat_id}")
                        else:
                            print(f"DEBUG: Could not verify ban status for chat {chat.chat_id}")
                    except Exception as e:
                        print(f"DEBUG: Error checking ban status in chat {chat.chat_id}: {e}")
        except Exception as e:
            print(f"DEBUG: Error in chat management: {e}")
    
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
    
    # Log the action
    role_name = user.role.name if user.role else "Нет роли"
    log_admin_action(
        admin=current_admin,
        action=AdminAction.USER_RESTORE,
        target=f"user_id:{user_id}",
        details=f"Восстановлен пользователь: {user.first_name} {user.last_name or ''} ({user.phone_number}). Роль: {role_name}",
        request=request
    )
    
    return {"status": "success", "message": "User rehired"}

@router.delete("/api/users/{user_id}")
async def api_delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete user completely (including from Telegram chats). Only 'admin' account can delete users."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    # Check if current admin is the main admin account
    if current_admin.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only the main admin account can delete users"
        )
    
    # ✅ Get user and active chats BEFORE deleting
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Save user info for logging
    user_name = f"{user.first_name} {user.last_name or ''}"
    user_phone = user.phone_number
    
    # Get active chats BEFORE deletion
    # Use role-based chats instead of chat_members table (more reliable)
    active_chat_ids = []
    if user.telegram_id and user.role_id:
        role_chats = get_chats_by_role(db, user.role_id)
        active_chat_ids = [chat.chat_id for chat in role_chats if chat.chat_id]
        print(f"DEBUG: Found {len(active_chat_ids)} chats from role {user.role_id} for deletion")
    elif user.telegram_id:
        # Fallback: try to get from chat_members table
        user_chats = get_user_chats(db, user.telegram_id)
        active_chat_ids = [chat.chat_id for chat in user_chats if chat.is_active == 'active']
        print(f"DEBUG: Found {len(active_chat_ids)} active chats from chat_members for deletion")
    
    telegram_id = user.telegram_id
    
    # Delete user from database
    if delete_user(db, user_id):
        # Remove from Telegram chats after database deletion
        if telegram_id and settings.BOT_TOKEN and active_chat_ids:
            try:
                from bot.chat_manager import ChatManager
                chat_manager = ChatManager(settings.BOT_TOKEN)
                
                print(f"\n{'='*60}")
                print(f"🗑️  DELETING USER {user_id}")
                print(f"{'='*60}")
                print(f"👤 User Telegram ID: {telegram_id}")
                print(f"📊 Active Chat IDs: {active_chat_ids}")
                print(f"🔢 Total Chats: {len(active_chat_ids)}")
                print(f"{'='*60}\n")
                
                print(f"🚀 Starting removal from {len(active_chat_ids)} chats...")
                removal_results = await chat_manager.remove_user_from_all_chats(telegram_id, active_chat_ids)
                
                print(f"\n📊 REMOVAL RESULTS:")
                for chat_id, result in removal_results.items():
                    status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                    error_msg = f" - {result['error']}" if result['error'] else ""
                    print(f"  Chat {chat_id}: {status}{error_msg}")
                print()
                
                success_count = sum(1 for r in removal_results.values() if r['success'])
                print(f"✅ Successfully removed from {success_count}/{len(active_chat_ids)} chats")
                
                # Send notification
                bot = Bot(token=settings.BOT_TOKEN)
                message = (
                    "🚫 Ваш аккаунт был удален из системы.\n\n"
                    "Вы были удалены из всех корпоративных чатов."
                )
                await bot.send_message(chat_id=telegram_id, text=message)
            except Exception as e:
                print(f"ERROR: Failed to remove deleted user from chats: {e}")
        
        # Log the action
        log_admin_action(
            admin=current_admin,
            action=AdminAction.USER_DELETE,
            target=f"user_id:{user_id}",
            details=f"Удален пользователь: {user_name} ({user_phone}). Удален из {len(active_chat_ids)} чатов.",
            request=request
        )
        
        return {"status": "success", "message": "User deleted and removed from all chats"}
    
    raise HTTPException(status_code=404, detail="User not found")

# ==================== ROLE GROUP API ====================

@router.get("/api/role-groups")
async def api_get_role_groups(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all role groups."""
    from database.crud import get_role_groups
    groups = get_role_groups(db, limit=1000)
    return [{
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "roles_count": len(group.roles) if group.roles else 0,
        "chats_count": len(group.chats) if group.chats else 0
    } for group in groups]

class RoleGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

@router.post("/api/role-groups")
async def api_create_role_group(
    group_data: RoleGroupCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create a new role group."""
    from database.crud import create_role_group, get_role_group_by_name
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    # Check if group with same name already exists
    existing = get_role_group_by_name(db, group_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Role group with this name already exists")
    
    group = create_role_group(db, name=group_data.name, description=group_data.description)
    
    # Log the action
    log_admin_action(
        admin=current_admin,
        action=AdminAction.ROLE_GROUP_CREATE,
        target=f"group_id:{group.id}",
        details=f"Создана группа ролей: {group.name}",
        request=request
    )
    
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description
    }

class RoleGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

@router.put("/api/role-groups/{group_id}")
async def api_update_role_group(
    group_id: int,
    group_data: RoleGroupUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update role group."""
    from database.crud import update_role_group, get_role_group_by_id
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    group = get_role_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Role group not found")
    
    update_data = group_data.dict(exclude_unset=True)
    updated_group = update_role_group(db, group_id, **update_data)
    
    # Log the action
    log_admin_action(
        admin=current_admin,
        action=AdminAction.ROLE_GROUP_EDIT,
        target=f"group_id:{group_id}",
        details=f"Обновлена группа ролей: {updated_group.name}",
        request=request
    )
    
    return {
        "id": updated_group.id,
        "name": updated_group.name,
        "description": updated_group.description
    }

@router.delete("/api/role-groups/{group_id}")
async def api_delete_role_group(
    group_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete role group."""
    from database.crud import delete_role_group, get_role_group_by_id
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    group = get_role_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Role group not found")
    
    group_name = group.name
    
    # Check if group has roles
    if group.roles and len(group.roles) > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete group with {len(group.roles)} roles. Remove roles first."
        )
    
    delete_role_group(db, group_id)
    
    # Log the action
    log_admin_action(
        admin=current_admin,
        action=AdminAction.ROLE_GROUP_DELETE,
        target=f"group_id:{group_id}",
        details=f"Удалена группа ролей: {group_name}",
        request=request
    )
    
    return {"status": "success", "message": "Role group deleted"}

# ==================== ROLE GROUP CHATS API ====================

@router.get("/api/role-groups/{group_id}/chats")
async def api_get_group_chats(
    group_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all chats assigned to a role group."""
    from database.crud import get_role_group_by_id
    
    group = get_role_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Role group not found")
    
    return [{
        "id": chat.id,
        "chat_id": chat.chat_id,
        "chat_name": chat.chat_name,
        "chat_link": chat.chat_link,
        "chat_photo": chat.chat_photo,
        "description": chat.description
    } for chat in group.chats]

class GroupChatsUpdate(BaseModel):
    chat_ids: List[int]

@router.put("/api/role-groups/{group_id}/chats")
async def api_update_group_chats(
    group_id: int,
    data: GroupChatsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Assign chats to a role group."""
    from database.crud import get_role_group_by_id, get_chat_by_id
    from database.models import group_chats
    from sqlalchemy import delete, insert
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    group = get_role_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Role group not found")
    
    try:
        # Validate that all chat IDs exist
        valid_chat_ids = []
        for chat_id in data.chat_ids:
            chat = get_chat_by_id(db, chat_id)
            if chat:
                valid_chat_ids.append(chat_id)
        
        # Delete existing associations
        db.execute(delete(group_chats).where(group_chats.c.group_id == group_id))
        
        # Insert new associations
        if valid_chat_ids:
            for chat_id in valid_chat_ids:
                db.execute(
                    insert(group_chats).values(
                        group_id=group_id,
                        chat_id=chat_id
                    )
                )
        
        db.commit()
        
        logger.info(f"Admin {current_admin.username} assigned {len(valid_chat_ids)} chats to group {group_id}")
        
        # Log the action
        log_admin_action(
            admin=current_admin,
            action=AdminAction.ROLE_GROUP_ASSIGN_CHATS,
            target=f"group_id:{group_id}",
            details=f"Привязано {len(valid_chat_ids)} чатов к группе: {group.name}",
            request=request
        )
        
        return {
            "status": "success",
            "message": f"Assigned {len(valid_chat_ids)} chats to group",
            "chat_ids": valid_chat_ids
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning chats to group {group_id}: {str(e)}", exc_info=True)
        
        # Check if it's a database schema error
        if "no such table: group_chats" in str(e):
            raise HTTPException(
                status_code=500, 
                detail="Database migration required. Please run: python migrate_add_group_chats.py"
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to assign chats: {str(e)}")

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
        "group": {"id": role.group.id, "name": role.group.name} if role.group else None,
        "group_id": role.group_id,
        "chats": [{"id": chat.id, "name": chat.chat_name} for chat in role.chats],
        "user_count": len(role.users)
    } for role in roles]

@router.post("/api/roles")
async def api_create_role(
    role: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create new role."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    from database.crud import get_role_group_by_id
    
    new_role = create_role(db, name=role.name, description=role.description, group_id=role.group_id)
    
    # Log the action
    if role.group_id:
        group = get_role_group_by_id(db, role.group_id)
        group_name = group.name if group else "Без группы"
    else:
        group_name = "Без группы"
        
    log_admin_action(
        admin=current_admin,
        action=AdminAction.ROLE_CREATE,
        target=f"role_id:{new_role.id}",
        details=f"Создана роль: {role.name}. Группа: {group_name}",
        request=request
    )
    
    return {"status": "success", "role_id": new_role.id}

@router.put("/api/roles/{role_id}")
async def api_update_role(
    role_id: int,
    role_update: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update role."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    update_data = role_update.model_dump(exclude_unset=True)
    chat_ids = update_data.pop('chat_ids', None)
    
    role = update_role(db, role_id, **update_data)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    details_parts = [f"Роль: {role.name}"]
    if chat_ids is not None:
        assign_chats_to_role(db, role_id, chat_ids)
        details_parts.append(f"Привязано чатов: {len(chat_ids)}")
    
    # Log the action
    log_admin_action(
        admin=current_admin,
        action=AdminAction.ROLE_EDIT,
        target=f"role_id:{role_id}",
        details=". ".join(details_parts),
        request=request
    )
    
    return {"status": "success", "message": "Role updated"}

@router.get("/api/roles/{role_id}/available-chats")
async def api_get_role_available_chats(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get chats available for a role (chats from the role's group)."""
    role = get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # If role has no group, return all chats
    if not role.group:
        chats = get_chats(db)
        return [{
            "id": chat.id,
            "chat_id": chat.chat_id,
            "chat_name": chat.chat_name,
            "description": chat.description
        } for chat in chats]
    
    # Return only chats from the role's group
    return [{
        "id": chat.id,
        "chat_id": chat.chat_id,
        "chat_name": chat.chat_name,
        "description": chat.description
    } for chat in role.group.chats]

@router.delete("/api/roles/{role_id}")
async def api_delete_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete role."""
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    # Get role name before deletion
    role = get_role_by_id(db, role_id)
    role_name = role.name if role else f"ID:{role_id}"
    
    if delete_role(db, role_id):
        # Log the action
        log_admin_action(
            admin=current_admin,
            action=AdminAction.ROLE_DELETE,
            target=f"role_id:{role_id}",
            details=f"Удалена роль: {role_name}",
            request=request
        )
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
        "chat_photo": chat.chat_photo,
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

@router.post("/api/chats/{chat_id}/fetch-photo")
async def api_fetch_chat_photo(
    chat_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Fetch current chat photo from Telegram and save it."""
    try:
        # Get chat from database
        chat = get_chat_by_id(db, chat_id)
        if not chat or not chat.chat_id:
            raise HTTPException(status_code=404, detail="Chat not found or no Telegram ID")
        
        if not settings.BOT_TOKEN:
            raise HTTPException(status_code=500, detail="Bot token not configured")
        
        from bot.chat_manager import ChatManager
        chat_manager = ChatManager(settings.BOT_TOKEN)
        
        print(f"📷 Fetching photo for chat {chat.chat_id}")
        photo_path = await chat_manager.get_chat_photo(chat.chat_id)
        
        if photo_path:
            # Update database with photo path
            update_chat(db, chat_id, chat_photo=photo_path)
            
            print(f"✅ Chat photo fetched and saved: {photo_path}")
            return {
                "status": "success",
                "message": "Chat photo fetched successfully",
                "photo_path": photo_path
            }
        else:
            return {
                "status": "no_photo",
                "message": "Chat has no photo",
                "photo_path": None
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching chat photo: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch photo: {str(e)}")

@router.post("/api/chats/fetch-all-photos")
async def api_fetch_all_chat_photos(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Fetch photos for all chats from Telegram."""
    try:
        if not settings.BOT_TOKEN:
            raise HTTPException(status_code=500, detail="Bot token not configured")
        
        chats = get_chats(db)
        from bot.chat_manager import ChatManager
        chat_manager = ChatManager(settings.BOT_TOKEN)
        
        results = {
            "success": 0,
            "no_photo": 0,
            "failed": 0
        }
        
        for chat in chats:
            if chat.chat_id:
                try:
                    photo_path = await chat_manager.get_chat_photo(chat.chat_id)
                    if photo_path:
                        update_chat(db, chat.id, chat_photo=photo_path)
                        results["success"] += 1
                    else:
                        results["no_photo"] += 1
                except Exception as e:
                    print(f"Failed to fetch photo for chat {chat.id}: {e}")
                    results["failed"] += 1
        
        return {
            "status": "success",
            "message": f"Processed {len(chats)} chats",
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Error fetching all chat photos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch photos: {str(e)}")

@router.post("/api/chats/{chat_id}/upload-photo")
async def api_upload_chat_photo(
    chat_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Upload and set chat photo."""
    try:
        # Get chat from database
        chat = get_chat_by_id(db, chat_id)
        if not chat or not chat.chat_id:
            raise HTTPException(status_code=404, detail="Chat not found or no Telegram ID")
        
        # Validate file type
        if not photo.content_type or not photo.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image (JPG/PNG)")
        
        # Create uploads directory if not exists
        settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = settings.UPLOADS_DIR / unique_filename
        
        # Save file
        print(f"💾 Saving uploaded photo to: {file_path}")
        with open(file_path, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
        
        print(f"✅ Photo saved, file size: {len(content)} bytes")
        
        # Set photo in Telegram
        if settings.BOT_TOKEN:
            from bot.chat_manager import ChatManager
            chat_manager = ChatManager(settings.BOT_TOKEN)
            
            print(f"🤖 Setting photo in Telegram chat {chat.chat_id}")
            success = await chat_manager.set_chat_photo(chat.chat_id, str(file_path))
            
            if success:
                # Update database with photo path
                relative_path = f"uploads/chat_photos/{unique_filename}"
                update_chat(db, chat_id, chat_photo=relative_path)
                
                print(f"✅ Chat photo updated successfully")
                return {
                    "status": "success",
                    "message": "Chat photo updated successfully",
                    "photo_path": relative_path
                }
            else:
                # Clean up file if failed
                os.remove(file_path)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to set chat photo in Telegram. Check bot permissions."
                )
        else:
            raise HTTPException(status_code=500, detail="Bot token not configured")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error uploading chat photo: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")

# ==================== ADMIN MANAGEMENT API ====================

@router.get("/api/current-admin")
async def api_get_current_admin(
    current_admin: Admin = Depends(get_current_admin)
):
    """Get current admin information."""
    return {
        "id": current_admin.id,
        "username": current_admin.username,
        "telegram_id": current_admin.telegram_id,
        "is_main_admin": current_admin.username == "admin"
    }

@router.get("/api/admins")
async def api_get_admins(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all administrators. Only admin user can access this."""
    # Check if current user is the main admin
    if current_admin.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only main admin can manage administrators"
        )
    
    admins = get_all_admins(db, limit=1000)
    return [{
        "id": admin.id,
        "username": admin.username,
        "telegram_id": admin.telegram_id,
        "created_at": admin.created_at.isoformat() if admin.created_at else None
    } for admin in admins]

@router.post("/api/admins")
async def api_create_admin(
    admin_data: AdminCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create new administrator. Only admin user can do this."""
    # Check if current user is the main admin
    if current_admin.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only main admin can create administrators"
        )
    
    # Check if username already exists
    existing_admin = get_admin_by_username(db, admin_data.username)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Validate password strength
    if len(admin_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    try:
        new_admin = create_admin(
            db,
            username=admin_data.username,
            password=admin_data.password,
            telegram_id=admin_data.telegram_id
        )
        
        print(f"✅ New administrator created: {new_admin.username} (ID: {new_admin.id})")
        
        return {
            "status": "success",
            "message": "Administrator created successfully",
            "admin": {
                "id": new_admin.id,
                "username": new_admin.username,
                "telegram_id": new_admin.telegram_id
            }
        }
    except Exception as e:
        print(f"❌ Error creating administrator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create administrator: {str(e)}"
        )

@router.put("/api/admins/{admin_id}/password")
async def api_update_admin_password(
    admin_id: int,
    password_data: AdminPasswordUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update administrator password. Admin can change any password, others only their own."""
    # Check if current user is main admin or updating their own password
    if current_admin.username != "admin" and current_admin.id != admin_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password"
        )
    
    # Validate password strength
    if len(password_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    try:
        # Get admin first to verify it exists
        print(f"DEBUG: Getting admin with ID {admin_id}")
        admin_to_update = get_admin_by_id(db, admin_id)
        print(f"DEBUG: admin_to_update type: {type(admin_to_update)}, value: {admin_to_update}")
        
        if not admin_to_update:
            raise HTTPException(status_code=404, detail="Administrator not found")
        
        print(f"DEBUG: Admin found: {admin_to_update.username}")
        
        # Update password
        print(f"DEBUG: Calling update_admin_password")
        updated_admin = update_admin_password(db, admin_id, password_data.password)
        print(f"DEBUG: updated_admin type: {type(updated_admin)}, value: {updated_admin}")
        
        if not updated_admin:
            raise HTTPException(status_code=404, detail="Administrator not found")
        
        print(f"DEBUG: About to access username attribute")
        print(f"✅ Password updated for administrator: {updated_admin.username}")
        
        return {
            "status": "success",
            "message": "Password updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}"
        )

@router.delete("/api/admins/{admin_id}")
async def api_delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete administrator. Only main admin can do this."""
    # Check if current user is the main admin
    if current_admin.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only main admin can delete administrators"
        )
    
    # Prevent deleting self
    if current_admin.id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own administrator account"
        )
    
    # Get admin info before deleting
    admin_to_delete = get_admin_by_id(db, admin_id)
    if not admin_to_delete:
        raise HTTPException(status_code=404, detail="Administrator not found")
    
    try:
        if delete_admin(db, admin_id):
            print(f"✅ Administrator deleted: {admin_to_delete.username} (ID: {admin_id})")
            return {
                "status": "success",
                "message": "Administrator deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Administrator not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting administrator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete administrator: {str(e)}"
        )

# ==================== ADMIN LOGS PAGE & API ====================

@router.get("/admin-logs", response_class=HTMLResponse)
async def admin_logs_page(request: Request):
    """Admin logs page (hidden, accessible only by direct URL)."""
    return templates.TemplateResponse("admin_logs.html", {"request": request})

@router.get("/api/admin-logs")
async def api_get_admin_logs(
    skip: int = 0,
    limit: int = 20,
    admin_name: Optional[str] = None,
    action: Optional[str] = None,
    search: Optional[str] = None,
    logs_db: Session = Depends(get_logs_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get admin logs with pagination and filters."""
    try:
        # Get logs with filters
        logs = get_admin_logs(
            db=logs_db,
            skip=skip,
            limit=limit,
            admin_name=admin_name,
            action=action,
            search=search
        )
        
        # Get total count for pagination
        total = count_admin_logs(
            db=logs_db,
            admin_name=admin_name,
            action=action,
            search=search
        )
        
        return {
            "logs": [{
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "admin_name": log.admin_name,
                "admin_id": log.admin_id,
                "action": log.action,
                "target": log.target,
                "details": log.details,
                "ip_address": log.ip_address
            } for log in logs],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting admin logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get admin logs: {str(e)}")

@router.get("/api/admin-logs/filters")
async def api_get_log_filters(
    logs_db: Session = Depends(get_logs_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get available filter options for logs."""
    try:
        admin_names = get_unique_admin_names_from_logs(logs_db)
        actions = get_unique_actions_from_logs(logs_db)
        
        return {
            "admin_names": admin_names,
            "actions": actions
        }
    except Exception as e:
        logger.error(f"Error getting log filters: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get filters: {str(e)}")

@router.get("/api/admin-logs/export")
async def api_export_admin_logs(
    format: str = "csv",  # csv or json
    admin_name: Optional[str] = None,
    action: Optional[str] = None,
    search: Optional[str] = None,
    logs_db: Session = Depends(get_logs_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Export admin logs to CSV or JSON."""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    import json
    from admin_panel.logger_helper import log_admin_action, AdminAction
    
    try:
        # Log the export action
        log_admin_action(
            admin=current_admin,
            action=AdminAction.EXPORT_LOGS,
            details=f"Format: {format}, Filters: admin={admin_name}, action={action}, search={search}"
        )
        
        # Get all matching logs (no pagination for export)
        logs = get_admin_logs(
            db=logs_db,
            skip=0,
            limit=10000,  # reasonable limit for export
            admin_name=admin_name,
            action=action,
            search=search
        )
        
        if format == "csv":
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['ID', 'Timestamp', 'Admin Name', 'Admin ID', 'Action', 'Target', 'Details', 'IP Address'])
            
            # Write data
            for log in logs:
                writer.writerow([
                    log.id,
                    log.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                    log.admin_name,
                    log.admin_id,
                    log.action,
                    log.target or '',
                    log.details or '',
                    log.ip_address or ''
                ])
            
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=admin_logs.csv"}
            )
        
        elif format == "json":
            # Create JSON
            logs_data = [{
                "id": log.id,
                "timestamp": log.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                "admin_name": log.admin_name,
                "admin_id": log.admin_id,
                "action": log.action,
                "target": log.target,
                "details": log.details,
                "ip_address": log.ip_address
            } for log in logs]
            
            json_str = json.dumps(logs_data, ensure_ascii=False, indent=2)
            
            return StreamingResponse(
                iter([json_str]),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=admin_logs.json"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting admin logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export logs: {str(e)}")

