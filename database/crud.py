"""CRUD operations for database models."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database.models import User, Role, Chat, Admin, ChatMember, role_chats
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================== USER OPERATIONS ====================

def create_user(db: Session, phone_number: str, telegram_id: Optional[int] = None,
                username: Optional[str] = None, first_name: Optional[str] = None,
                last_name: Optional[str] = None) -> User:
    """Create a new user."""
    user = User(
        phone_number=phone_number,
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        status='pending'
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID."""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def get_user_by_phone(db: Session, phone_number: str) -> Optional[User]:
    """Get user by phone number."""
    return db.query(User).filter(User.phone_number == phone_number).first()

def get_users(db: Session, skip: int = 0, limit: int = 100,
              status: Optional[str] = None) -> List[User]:
    """Get list of users with optional filtering."""
    query = db.query(User)
    if status:
        query = query.filter(User.status == status)
    return query.offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Update user information."""
    user = get_user_by_id(db, user_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

def approve_user(db: Session, user_id: int, role_id: int) -> Optional[User]:
    """Approve user and assign role."""
    user = get_user_by_id(db, user_id)
    if user:
        user.status = 'approved'
        user.role_id = role_id
        db.commit()
        db.refresh(user)
    return user

def reject_user(db: Session, user_id: int) -> Optional[User]:
    """Reject user application."""
    user = get_user_by_id(db, user_id)
    if user:
        user.status = 'rejected'
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete user."""
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def count_users_by_status(db: Session, status: str) -> int:
    """Count users by status."""
    return db.query(User).filter(User.status == status).count()

def fire_user(db: Session, user_id: int) -> Optional[User]:
    """Fire user (change status to fired) and remove from all chats."""
    user = get_user_by_id(db, user_id)
    if user:
        # Mark user as fired
        user.status = 'fired'
        
        # Remove user from all role chats
        remove_user_from_role_chats(db, user_id)
        
        db.commit()
        db.refresh(user)
    return user

def get_fired_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get list of fired users."""
    return db.query(User).filter(User.status == 'fired').offset(skip).limit(limit).all()

# ==================== ROLE OPERATIONS ====================

def create_role(db: Session, name: str, description: Optional[str] = None) -> Role:
    """Create a new role."""
    role = Role(name=name, description=description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def get_role_by_id(db: Session, role_id: int) -> Optional[Role]:
    """Get role by ID."""
    return db.query(Role).filter(Role.id == role_id).first()

def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    """Get role by name."""
    return db.query(Role).filter(Role.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    """Get list of roles."""
    return db.query(Role).offset(skip).limit(limit).all()

def update_role(db: Session, role_id: int, **kwargs) -> Optional[Role]:
    """Update role information."""
    role = get_role_by_id(db, role_id)
    if role:
        for key, value in kwargs.items():
            if hasattr(role, key) and key != 'chats':
                setattr(role, key, value)
        db.commit()
        db.refresh(role)
    return role

def delete_role(db: Session, role_id: int) -> bool:
    """Delete role."""
    role = get_role_by_id(db, role_id)
    if role:
        db.delete(role)
        db.commit()
        return True
    return False

def assign_chats_to_role(db: Session, role_id: int, chat_ids: List[int]) -> Optional[Role]:
    """Assign chats to a role."""
    role = get_role_by_id(db, role_id)
    if role:
        # Clear existing chats
        role.chats.clear()
        # Add new chats
        for chat_id in chat_ids:
            chat = get_chat_by_id(db, chat_id)
            if chat:
                role.chats.append(chat)
        db.commit()
        db.refresh(role)
    return role

# ==================== CHAT OPERATIONS ====================

def create_chat(db: Session, chat_name: str, chat_link: Optional[str] = None,
                chat_id: Optional[int] = None, description: Optional[str] = None) -> Chat:
    """Create a new chat."""
    chat = Chat(
        chat_name=chat_name,
        chat_link=chat_link,
        chat_id=chat_id,
        description=description
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

def get_chat_by_id(db: Session, chat_id: int) -> Optional[Chat]:
    """Get chat by ID."""
    return db.query(Chat).filter(Chat.id == chat_id).first()

def get_chat_by_chat_id(db: Session, chat_id: int) -> Optional[Chat]:
    """Get chat by Telegram chat ID."""
    return db.query(Chat).filter(Chat.chat_id == chat_id).first()

def get_chats(db: Session, skip: int = 0, limit: int = 100) -> List[Chat]:
    """Get list of chats."""
    return db.query(Chat).offset(skip).limit(limit).all()

def update_chat(db: Session, chat_id: int, **kwargs) -> Optional[Chat]:
    """Update chat information."""
    chat = get_chat_by_id(db, chat_id)
    if chat:
        for key, value in kwargs.items():
            if hasattr(chat, key):
                setattr(chat, key, value)
        db.commit()
        db.refresh(chat)
    return chat

def delete_chat(db: Session, chat_id: int) -> bool:
    """Delete chat."""
    chat = get_chat_by_id(db, chat_id)
    if chat:
        db.delete(chat)
        db.commit()
        return True
    return False

def get_chats_by_role(db: Session, role_id: int) -> List[Chat]:
    """Get all chats assigned to a role."""
    role = get_role_by_id(db, role_id)
    return role.chats if role else []

# ==================== ADMIN OPERATIONS ====================

def create_admin(db: Session, username: str, password: str,
                 telegram_id: Optional[int] = None) -> Admin:
    """Create a new admin."""
    password_hash = pwd_context.hash(password)
    admin = Admin(
        username=username,
        password_hash=password_hash,
        telegram_id=telegram_id
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

def get_admin_by_username(db: Session, username: str) -> Optional[Admin]:
    """Get admin by username."""
    return db.query(Admin).filter(Admin.username == username).first()

def get_admin_by_telegram_id(db: Session, telegram_id: int) -> Optional[Admin]:
    """Get admin by Telegram ID."""
    return db.query(Admin).filter(Admin.telegram_id == telegram_id).first()

def add_user_to_role_chats(db: Session, user_id: int) -> bool:
    """Add user to all chats associated with their role."""
    try:
        from database.models import role_chats as role_chats_table
        
        user = get_user_by_id(db, user_id)
        if not user or not user.role_id or not user.telegram_id:
            print(f"DEBUG: Cannot add user to role chats - user: {user}, role_id: {user.role_id if user else None}, telegram_id: {user.telegram_id if user else None}")
            return False
        
        # Get all chats for this role using the relationship
        role = get_role_by_id(db, user.role_id)
        if not role:
            print(f"DEBUG: Role {user.role_id} not found")
            return False
        
        chats = role.chats
        print(f"DEBUG: Found {len(chats)} chats for role '{role.name}' (ID: {role.id})")
        
        # Add user to each chat in database
        for chat in chats:
            if chat.chat_id:  # Only if chat has Telegram ID
                print(f"DEBUG: Adding user {user.telegram_id} to chat {chat.chat_id} ({chat.chat_name}) in database")
                add_chat_member(db, chat.chat_id, user.telegram_id, 
                              user.username, user.first_name, user.last_name)
            else:
                print(f"DEBUG: Skipping chat '{chat.chat_name}' - no Telegram ID")
        
        return True
    except Exception as e:
        print(f"Error adding user to role chats: {e}")
        import traceback
        traceback.print_exc()
        return False

def remove_user_from_role_chats(db: Session, user_id: int) -> bool:
    """Remove user from all chats associated with their role."""
    try:
        user = get_user_by_id(db, user_id)
        if not user or not user.telegram_id:
            return False
        
        # Mark all user's chat memberships as left
        user_chats = get_user_chats(db, user.telegram_id)
        for chat_member in user_chats:
            chat_member.is_active = 'left'
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error removing user from role chats: {e}")
        return False

def update_user_role_chats(db: Session, user_id: int, old_role_id: int = None, new_role_id: int = None) -> bool:
    """Update user's chat memberships when role changes."""
    try:
        user = get_user_by_id(db, user_id)
        if not user or not user.telegram_id:
            return False
        
        # Remove from old role chats
        if old_role_id:
            old_chats = db.query(Chat).join(role_chats).filter(
                role_chats.c.role_id == old_role_id
            ).all()
            
            for chat in old_chats:
                chat_member = db.query(ChatMember).filter(
                    ChatMember.chat_id == chat.chat_id,
                    ChatMember.user_telegram_id == user.telegram_id
                ).first()
                
                if chat_member:
                    chat_member.is_active = 'left'
        
        # Add to new role chats
        if new_role_id:
            new_chats = db.query(Chat).join(role_chats).filter(
                role_chats.c.role_id == new_role_id
            ).all()
            
            for chat in new_chats:
                add_chat_member(db, chat.chat_id, user.telegram_id, 
                              user.username, user.first_name, user.last_name)
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error updating user role chats: {e}")
        return False

def get_user_chat_memberships(db: Session, user_id: int) -> List[dict]:
    """Get user's chat memberships with chat details."""
    try:
        user = get_user_by_id(db, user_id)
        if not user or not user.telegram_id:
            return []
        
        # Get user's active chat memberships
        memberships = db.query(ChatMember, Chat).join(Chat, ChatMember.chat_id == Chat.chat_id).filter(
            ChatMember.user_telegram_id == user.telegram_id,
            ChatMember.is_active == 'active'
        ).all()
        
        result = []
        for membership, chat in memberships:
            result.append({
                'chat_id': chat.chat_id,
                'chat_name': chat.chat_name,
                'chat_link': chat.chat_link,
                'joined_at': membership.joined_at,
                'role_name': user.role.name if user.role else None
            })
        
        return result
    except Exception as e:
        print(f"Error getting user chat memberships: {e}")
        return []

def verify_admin_password(admin: Admin, password: str) -> bool:
    """Verify admin password."""
    return pwd_context.verify(password, admin.password_hash)

def authenticate_admin(username: str, password: str, db: Session):
    """Authenticate admin user."""
    admin = get_admin_by_username(db, username)
    if not admin:
        return None
    if not verify_admin_password(admin, password):
        return None
    return admin

def update_admin_password(db: Session, admin_id: int, new_password: str) -> bool:
    """Update admin password."""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin:
        admin.password_hash = pwd_context.hash(new_password)
        db.commit()
        return True
    return False

# ==================== STATISTICS ====================

# ==================== CHAT MEMBER OPERATIONS ====================

def add_chat_member(db: Session, chat_id: int, user_telegram_id: int,
                   username: Optional[str] = None, first_name: Optional[str] = None,
                   last_name: Optional[str] = None) -> ChatMember:
    """Add user to chat members list."""
    # Check if already exists
    existing = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_telegram_id == user_telegram_id
    ).first()
    
    if existing:
        existing.is_active = 'active'
        existing.joined_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    member = ChatMember(
        chat_id=chat_id,
        user_telegram_id=user_telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

def remove_chat_member(db: Session, chat_id: int, user_telegram_id: int) -> bool:
    """Mark user as left chat."""
    member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_telegram_id == user_telegram_id
    ).first()
    
    if member:
        member.is_active = 'left'
        db.commit()
        return True
    return False

def get_chat_members(db: Session, chat_id: int) -> List[ChatMember]:
    """Get all active members of a chat."""
    return db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.is_active == 'active'
    ).all()

def get_user_chats(db: Session, user_telegram_id: int) -> List[ChatMember]:
    """Get all chats where user is a member."""
    return db.query(ChatMember).filter(
        ChatMember.user_telegram_id == user_telegram_id,
        ChatMember.is_active == 'active'
    ).all()

# ==================== STATISTICS ====================

def get_statistics(db: Session) -> dict:
    """Get general statistics."""
    return {
        "total_users": db.query(User).count(),
        "pending_requests": count_users_by_status(db, 'pending'),
        "approved_users": count_users_by_status(db, 'approved'),
        "rejected_users": count_users_by_status(db, 'rejected'),
        "fired_users": count_users_by_status(db, 'fired'),
        "total_roles": db.query(Role).count(),
        "total_chats": db.query(Chat).count(),
    }

