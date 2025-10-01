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
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    role = relationship("Role", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.phone_number} - {self.status}>"

class Role(Base):
    """Role model for defining user roles."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
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

