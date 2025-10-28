"""Database models for admin logs (separate database)."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from database.database import LogsBase


class AdminLog(LogsBase):
    """Admin log model for tracking admin actions."""
    
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    admin_name = Column(String(255), nullable=False, index=True)
    admin_id = Column(Integer, nullable=False, index=True)
    action = Column(String(255), nullable=False, index=True)
    target = Column(String(255), nullable=True)  # ID or name of affected object
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    
    def __repr__(self):
        return f"<AdminLog {self.admin_name} - {self.action}>"

