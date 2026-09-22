"""Truck modeli."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base, TimestampMixin


if TYPE_CHECKING:
    from src.database.models.truck_step import TruckStep


class Truck(Base, TimestampMixin):
    """Har bir ishlab chiqarilayotgan mashina."""

    __tablename__ = "trucks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Serial raqam (unikal)
    serial_number: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # Model (ixtiyoriy)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Hozirgi step (1-6)
    current_step: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, index=True
    )

    # Umumiy holat
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

    # Yakunlangan vaqt
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
