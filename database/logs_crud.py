"""CRUD operations for admin logs (separate database)."""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database.logs_models import AdminLog


def create_admin_log(
    db: Session,
    admin_name: str,
    admin_id: int,
    action: str,
    target: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> AdminLog:
    """Create a new admin log entry."""
    log = AdminLog(
        admin_name=admin_name,
        admin_id=admin_id,
        action=action,
        target=target,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_admin_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    admin_name: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None
) -> List[AdminLog]:
    """Get admin logs with optional filters."""
    query = db.query(AdminLog)
    
    # Apply filters
    if admin_name:
        query = query.filter(AdminLog.admin_name == admin_name)
    
    if action:
        query = query.filter(AdminLog.action == action)
    
    if date_from:
        query = query.filter(AdminLog.timestamp >= date_from)
    
    if date_to:
        query = query.filter(AdminLog.timestamp <= date_to)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                AdminLog.admin_name.ilike(search_pattern),
                AdminLog.action.ilike(search_pattern),
                AdminLog.target.ilike(search_pattern),
                AdminLog.details.ilike(search_pattern)
            )
        )
    
    # Order by timestamp descending (newest first)
    query = query.order_by(AdminLog.timestamp.desc())
    
    return query.offset(skip).limit(limit).all()


def count_admin_logs(
    db: Session,
    admin_name: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None
) -> int:
    """Count admin logs with optional filters."""
    query = db.query(AdminLog)
    
    if admin_name:
        query = query.filter(AdminLog.admin_name == admin_name)
    
    if action:
        query = query.filter(AdminLog.action == action)
    
    if date_from:
        query = query.filter(AdminLog.timestamp >= date_from)
    
    if date_to:
        query = query.filter(AdminLog.timestamp <= date_to)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                AdminLog.admin_name.ilike(search_pattern),
                AdminLog.action.ilike(search_pattern),
                AdminLog.target.ilike(search_pattern),
                AdminLog.details.ilike(search_pattern)
            )
        )
    
    return query.count()


def get_unique_admin_names_from_logs(db: Session) -> List[str]:
    """Get list of unique admin names from logs."""
    result = db.query(AdminLog.admin_name).distinct().all()
    return [row[0] for row in result]


def get_unique_actions_from_logs(db: Session) -> List[str]:
    """Get list of unique actions from logs."""
    result = db.query(AdminLog.action).distinct().all()
    return [row[0] for row in result]


def delete_old_logs(db: Session, days: int = 90) -> int:
    """Delete logs older than specified days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(AdminLog).filter(AdminLog.timestamp < cutoff_date).delete()
    db.commit()
    return deleted


def get_logs_statistics(db: Session) -> dict:
    """Get statistics about logs."""
    total_logs = db.query(AdminLog).count()
    
    # Get logs from last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    last_24h = db.query(AdminLog).filter(AdminLog.timestamp >= yesterday).count()
    
    # Get logs from last 7 days
    last_week = datetime.utcnow() - timedelta(days=7)
    last_7d = db.query(AdminLog).filter(AdminLog.timestamp >= last_week).count()
    
    # Get most active admin
    from sqlalchemy import func
    most_active = db.query(
        AdminLog.admin_name,
        func.count(AdminLog.id).label('count')
    ).group_by(AdminLog.admin_name).order_by(func.count(AdminLog.id).desc()).first()
    
    return {
        "total_logs": total_logs,
        "last_24h": last_24h,
        "last_7d": last_7d,
        "most_active_admin": most_active[0] if most_active else None,
        "most_active_count": most_active[1] if most_active else 0
    }

