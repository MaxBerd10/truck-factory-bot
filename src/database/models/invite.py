"""Taklifnoma (invite link) modeli."""
from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models.base import Base, TimestampMixin


class Invite(Base, TimestampMixin):
    """Taklifnoma havolasi (bir martalik yoki muddatli)."""

    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Unikal kod
    code: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # Rol va step
    role: Mapped[str] = mapped_column(
        Enum(
            "worker", "qc", "admin",
            name="invite_role",
            native_enum=True,
        ),
        nullable=False,
    )
    step_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Kim yaratdi
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Telegram ID

    # Ishlatilganmi
    is_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    used_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Muddati
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # ===== Properties =====
    @property
    def is_expired(self) -> bool:
        """Muddati o'tganmi?"""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Havola hali ishlatilishi mumkinmi?"""
        return not self.is_used and not self.is_expired

    def __repr__(self) -> str:
        return (
            f"<Invite(id={self.id}, code='{self.code}', "
            f"role='{self.role}', step={self.step_number}, "
            f"used={self.is_used})>"
        )
