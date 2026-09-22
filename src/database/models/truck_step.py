"""Truck ning har bir stepi uchun model."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base, TimestampMixin


if TYPE_CHECKING:
    from src.database.models.truck import Truck
    from src.database.models.user import User


class TruckStep(Base, TimestampMixin):
    """Truck ning bitta stepi (masalan, Karkas yig'ish)."""

    __tablename__ = "truck_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Qaysi truck
    truck_id: Mapped[int] = mapped_column(
        ForeignKey("trucks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Step raqami (1-6)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Kim bajaradi (ishchi)
    worker_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Kim tekshiradi (QC)
    qc_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Holat
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "in_review", "approved", "rejected",
            name="step_status",
            native_enum=True,
        ),
        default="pending",
        nullable=False,
        index=True,
    )

    # Media (rasm/video)
    media_type: Mapped[str | None] = mapped_column(
        Enum(
            "photo", "video", "document",
            name="media_type",
            native_enum=True,
        ),
        nullable=True,
    )
    media_file_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Telegram file_id
    media_local_path: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )  # Server diskidagi yo'l

    # Izohlar
    worker_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    qc_comment: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Rad etish sababi

    # Vaqtlar
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ===== Relationships =====
    truck: Mapped["Truck"] = relationship(
        "Truck",
        back_populates="steps",
        lazy="selectin",
    )
    worker: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[worker_id],
        back_populates="submitted_steps",
        lazy="selectin",
    )
    qc: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[qc_id],
        back_populates="reviewed_steps",
        lazy="selectin",
    )

    # ===== Properties =====
    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_in_review(self) -> bool:
        return self.status == "in_review"

    @property
    def is_approved(self) -> bool:
        return self.status == "approved"

    @property
    def is_rejected(self) -> bool:
        return self.status == "rejected"

    @property
    def has_media(self) -> bool:
        return self.media_file_id is not None or self.media_local_path is not None

    def __repr__(self) -> str:
        return (
            f"<TruckStep(id={self.id}, truck_id={self.truck_id}, "
            f"step={self.step_number}, status='{self.status}')>"
        )
