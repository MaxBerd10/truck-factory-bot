"""Modellarni import qilish (Alembic uchun muhim)."""
from src.database.models.audit_log import AuditLog
from src.database.models.base import Base, TimestampMixin
from src.database.models.invite import Invite
from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.database.models.user import User


__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Invite",
    "Truck",
    "TruckStep",
    "AuditLog",
]
