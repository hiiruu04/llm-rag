"""002 maintenance schedules

Revision ID: 002_maintenance_schedules
Revises: 001_initial_cmms
Create Date: 2026-04-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_maintenance_schedules"
down_revision: Union[str, None] = "001_initial_cmms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "maintenance_schedules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fault_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("faults.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("maintenance_type", sa.String(20), nullable=False, server_default="preventive"),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_date", sa.DateTime(timezone=True)),
        sa.Column("assigned_to", sa.String(255)),
        sa.Column("recurrence", sa.String(20), nullable=False, server_default="none"),
        sa.Column("estimated_duration_hours", sa.Float),
        sa.Column("notes", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index("ix_maintenance_schedules_asset_id", "maintenance_schedules", ["asset_id"])
    op.create_index("ix_maintenance_schedules_status", "maintenance_schedules", ["status"])
    op.create_index(
        "ix_maintenance_schedules_scheduled_date", "maintenance_schedules", ["scheduled_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_maintenance_schedules_scheduled_date", table_name="maintenance_schedules")
    op.drop_index("ix_maintenance_schedules_status", table_name="maintenance_schedules")
    op.drop_index("ix_maintenance_schedules_asset_id", table_name="maintenance_schedules")
    op.drop_table("maintenance_schedules")
