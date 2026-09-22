"""Audit log modeli — kim, qachon, nima qildi."""
from typing import Any

from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    """Har bir muhim amalni yozib borish."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Kim qildi
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True
    )  # Telegram ID

    # Amal turi
    action: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # masalan: "user_created", "step_approved"

    # Obyekt turi va ID
    entity_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )  # "user", "truck", "truck_step", "invite"
    entity_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    # Qo'shimcha ma'lumotlar (JSON)
    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    # Izoh
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action='{self.action}', entity='{self.entity_type}:{self.entity_id}')>"
        )
