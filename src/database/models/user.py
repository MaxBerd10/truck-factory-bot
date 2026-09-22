"""Foydalanuvchi modeli."""
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base, TimestampMixin
from src.utils.constants import UserRole


if TYPE_CHECKING:
    from src.database.models.truck_step import TruckStep


class User(Base, TimestampMixin):
    """Foydalanuvchi: ishchi, QC, yoki admin."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Telegram ma'lumotlari
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Shaxsiy ma'lumotlar
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Rol va step
    role: Mapped[str] = mapped_column(
        Enum(
            "worker", "qc", "admin",
            name="user_role",
            native_enum=True,
        ),
        nullable=False,
        index=True,
    )
    step_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )  # 1-6 (faqat worker uchun)

    # Holat
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )

    # Kim qo'shdi (admin telegram_id)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # ===== Relationships =====
    # Ishchi bajargan steplar
    submitted_steps: Mapped[list["TruckStep"]] = relationship(
        "TruckStep",
        foreign_keys="TruckStep.worker_id",
        back_populates="worker",
        lazy="selectin",
    )

    # QC tekshirgan steplar
    reviewed_steps: Mapped[list["TruckStep"]] = relationship(
        "TruckStep",
        foreign_keys="TruckStep.qc_id",
        back_populates="qc",
        lazy="selectin",
    )

    # ===== Properties =====
    @property
    def is_worker(self) -> bool:
        return self.role == UserRole.WORKER.value

    @property
    def is_qc(self) -> bool:
        return self.role == UserRole.QC.value

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    @property
    def display_name(self) -> str:
        """Telegram uchun chiroyli ism."""
        if self.username:
            return f"{self.full_name} (@{self.username})"
        return self.full_name

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, "
            f"full_name='{self.full_name}', role='{self.role}', "
            f"step={self.step_number}, active={self.is_active})>"
        )
