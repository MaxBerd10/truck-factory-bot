"""Notification settings modeli."""
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class NotificationSettings(Base):
    """Foydalanuvchi bildirishnoma sozlamalari."""
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    on_new_task: Mapped[bool] = mapped_column(Boolean, default=True)
    on_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    on_rejected: Mapped[bool] = mapped_column(Boolean, default=True)
    on_next_step: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_report: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", backref="notification_settings")
