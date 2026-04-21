"""005 model_improvements

Revision ID: 005_model_improvements
Revises: 004_kg
Create Date: 2026-04-16

- Add fault_id FK to down_events (Fault -> DownEvent)
- Add action_type and sequence_order to maintenance_schedules
- Drop action_competence junction table
- Create maintenance_competence junction table
- Drop actions table

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_model_improvements"
down_revision: Union[str, None] = "004_kg"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Change 1: Fault -> DownEvent ──
    op.add_column(
        "down_events",
        sa.Column(
            "fault_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("faults.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ── Change 2: Merge Action into MaintenanceSchedule ──

    # Add action_type and sequence_order to maintenance_schedules
    op.add_column(
        "maintenance_schedules",
        sa.Column(
            "action_type",
            sa.String(100),
            nullable=False,
            server_default="standard",
        ),
    )
    op.add_column(
        "maintenance_schedules",
        sa.Column(
            "sequence_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # Drop old action_competence junction table
    op.drop_table("action_competence")

    # Create new maintenance_competence junction table
    op.create_table(
        "maintenance_competence",
        sa.Column(
            "maintenance_schedule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("maintenance_schedules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "competence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competences.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("maintenance_schedule_id", "competence_id"),
    )

    # Drop actions table
    op.drop_table("actions")


def downgrade() -> None:
    # ── Recreate actions table ──
    op.create_table(
        "actions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "action_type",
            sa.String(100),
            nullable=False,
            server_default="standard",
        ),
        sa.Column(
            "sequence_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
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

    # Recreate action_competence
    op.create_table(
        "action_competence",
        sa.Column(
            "action_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("actions.id"),
            nullable=False,
        ),
        sa.Column(
            "competence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competences.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("action_id", "competence_id"),
    )

    # Drop maintenance_competence
    op.drop_table("maintenance_competence")

    # Remove columns from maintenance_schedules
    op.drop_column("maintenance_schedules", "sequence_order")
    op.drop_column("maintenance_schedules", "action_type")

    # Remove fault_id from down_events
    op.drop_column("down_events", "fault_id")
