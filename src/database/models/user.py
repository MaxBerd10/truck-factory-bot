"""Foydalanuvchi modeli."""
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base, TimestampMixin
from src.utils.constants import UserRole


if TYPE_CHECKING:
    from src.database.models.truck_step import TruckStep


class User(Base, TimestampMixin):
    """Bot foydalanuvchisi (admin, QC, ishchi)."""

    __tablename__ = "users"

    # ==== Asosiy ====
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    full_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    # ==== Rol ====
    role: Mapped[str] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    # ==== Worker uchun ====
    step_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # ==== Status ====
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    # ==== Kim taklif qilgan (Telegram ID) ====
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    # ==== Til ====
    language: Mapped[str] = mapped_column(
        String(10), default="uz", server_default="uz"
    )

    # ==== Relationships ====
    submitted_steps: Mapped[list["TruckStep"]] = relationship(
        "TruckStep",
        foreign_keys="TruckStep.worker_id",
        back_populates="worker",
        lazy="selectin",
    )

    reviewed_steps: Mapped[list["TruckStep"]] = relationship(
        "TruckStep",
        foreign_keys="TruckStep.qc_id",
        back_populates="qc",
        lazy="selectin",
    )

    # ==== Properties ====
    @property
    def is_admin(self) -> bool:
        """Administratormi?"""
        return self.role == UserRole.ADMIN

    @property
    def is_qc(self) -> bool:
        """Sifat nazoratchisimi?"""
        return self.role == UserRole.QC

    @property
    def is_worker(self) -> bool:
        """Ishchimi?"""
        return self.role == UserRole.WORKER

    @property
    def is_worker_step(self) -> int | None:
        """Ishchining step raqami (faqat worker uchun)."""
        return self.step_number if self.is_worker else None

    def __repr__(self) -> str:
        """Repr."""
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, "
            f"role={self.role}, step={self.step_number})>"
        )
