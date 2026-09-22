"""Truck modeli."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base, TimestampMixin


if TYPE_CHECKING:
    from src.database.models.truck_step import TruckStep


class Truck(Base, TimestampMixin):
    """Har bir ishlab chiqarilayotgan mashina."""

    __tablename__ = "trucks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ==== Asosiy ma'lumotlar ====
    serial_number: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    customer: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Buyurtmachi

    # ==== Muddat va prioritet ====
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    priority: Mapped[str] = mapped_column(
        Enum(
            "low", "normal", "high", "urgent",
            name="truck_priority",
            native_enum=True,
        ),
        default="normal",
        nullable=False,
        index=True,
    )

    # ==== Holat ====
    current_step: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "in_progress", "completed",
            name="truck_status",
            native_enum=True,
        ),
        default="in_progress",
        nullable=False,
        index=True,
    )

    # ==== Kim yaratdi ====
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )  # Admin telegram_id yoki ERP ID
    source: Mapped[str] = mapped_column(
        Enum(
            "admin", "erp",
            name="truck_source",
            native_enum=True,
        ),
        default="admin",
        nullable=False,
        index=True,
    )

    # ==== Vaqtlar ====
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ===== Relationships =====
    steps: Mapped[list["TruckStep"]] = relationship(
        "TruckStep",
        back_populates="truck",
        cascade="all, delete-orphan",
        order_by="TruckStep.step_number",
        lazy="selectin",
    )

    # ===== Properties =====
    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_in_progress(self) -> bool:
        return self.status == "in_progress"

    def __repr__(self) -> str:
        return (
            f"<Truck(id={self.id}, serial='{self.serial_number}', "
            f"step={self.current_step}, status='{self.status}')>"
        )
