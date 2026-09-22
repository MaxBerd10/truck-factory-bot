"""add truck fields: customer, deadline, priority, created_by, source

Revision ID: 9126250b961e
Revises: 0b381e5c7e7d
Create Date: 2026-09-22 15:41:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9126250b961e'
down_revision: Union[str, None] = '0b381e5c7e7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== 1. Enum turlarini yaratish =====
    truck_priority_enum = sa.Enum(
        "low", "normal", "high", "urgent",
        name="truck_priority",
    )
    truck_priority_enum.create(op.get_bind(), checkfirst=True)

    truck_source_enum = sa.Enum(
        "admin", "erp",
        name="truck_source",
    )
    truck_source_enum.create(op.get_bind(), checkfirst=True)

    # ===== 2. Ustunlarni qo'shish =====
    op.add_column(
        "trucks",
        sa.Column("customer", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "trucks",
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "trucks",
        sa.Column(
            "priority",
            sa.Enum(
                "low", "normal", "high", "urgent",
                name="truck_priority",
                create_type=False,  # Enum allaqachon yaratilgan
            ),
            nullable=False,
            server_default="normal",
        ),
    )
    op.add_column(
        "trucks",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "trucks",
        sa.Column(
            "source",
            sa.Enum(
                "admin", "erp",
                name="truck_source",
                create_type=False,  # Enum allaqachon yaratilgan
            ),
            nullable=False,
            server_default="admin",
        ),
    )

    # ===== 3. Indexlar =====
    op.create_index(
        op.f("ix_trucks_deadline"), "trucks", ["deadline"], unique=False
    )
    op.create_index(
        op.f("ix_trucks_priority"), "trucks", ["priority"], unique=False
    )
    op.create_index(
        op.f("ix_trucks_source"), "trucks", ["source"], unique=False
    )


def downgrade() -> None:
    # ===== 1. Indexlarni o'chirish =====
    op.drop_index(op.f("ix_trucks_source"), table_name="trucks")
    op.drop_index(op.f("ix_trucks_priority"), table_name="trucks")
    op.drop_index(op.f("ix_trucks_deadline"), table_name="trucks")

    # ===== 2. Ustunlarni o'chirish =====
    op.drop_column("trucks", "source")
    op.drop_column("trucks", "created_by")
    op.drop_column("trucks", "priority")
    op.drop_column("trucks", "deadline")
    op.drop_column("trucks", "customer")

    # ===== 3. Enum turlarini o'chirish =====
    sa.Enum(name="truck_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="truck_priority").drop(op.get_bind(), checkfirst=True)
