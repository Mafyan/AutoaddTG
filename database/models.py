"""Database models for the application."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger, Text
from sqlalchemy.orm import relationship
from database.database import Base

# Association table for many-to-many relationship between roles and chats
role_chats = Table(
    'role_chats',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE')),
    Column('chat_id', Integer, ForeignKey('chats.id', ondelete='CASCADE'))
)

class User(Base):
    """User model for storing employee information."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)  # Job position
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(20), default='pending')  # pending, approved, rejected, fired
    last_links_request = Column(DateTime, nullable=True)  # Last time user requested chat links
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    role = relationship("Role", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.phone_number} - {self.status}>"

class RoleGroup(Base):
    """Role group model for organizing roles."""
    
    __tablename__ = "role_groups"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    roles = relationship("Role", back_populates="group")
    
    def __repr__(self):
        return f"<RoleGroup {self.name}>"

class Role(Base):
    """Role model for defining user roles."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    group_id = Column(Integer, ForeignKey('role_groups.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("RoleGroup", back_populates="roles")
    users = relationship("User", back_populates="role")
    chats = relationship("Chat", secondary=role_chats, back_populates="roles")
    
    def __repr__(self):
        return f"<Role {self.name}>"

class Chat(Base):
    """Chat model for storing Telegram chat information."""
    
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, index=True, nullable=True)
    chat_name = Column(String(255), nullable=False)
    chat_link = Column(String(500), nullable=True)
    chat_photo = Column(String(500), nullable=True)  # Path to chat photo file
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    roles = relationship("Role", secondary=role_chats, back_populates="chats")
    
    def __repr__(self):
        return f"<Chat {self.chat_name}>"

class Admin(Base):
    """Admin model for panel administrators."""
    
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Admin {self.username}>"

class ChatMember(Base):
    """Model for tracking chat members."""
    
    __tablename__ = "chat_members"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    user_telegram_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(String(10), default='active')  # active, left, kicked
    
    def __repr__(self):
        return f"<ChatMember {self.user_telegram_id} in {self.chat_id}>"

