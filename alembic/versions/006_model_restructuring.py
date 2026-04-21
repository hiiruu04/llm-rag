"""006 model_restructuring

Revision ID: 006_model_restructuring
Revises: 005_model_improvements
Create Date: 2026-04-17

Redefine model relationships:
- Fault -> DownEvent -> MaintenanceSchedule -> Task -> (Workers, Roles, Shift)
- Add task_worker and level_competence association tables
- Add workers.level_id FK
- Add tasks.maintenance_schedule_id, shift_id, assigned_to, action_type, sequence_order
- Add down_events.maintenance_schedule_id
- Make down_events.fault_id NOT NULL with CASCADE
- Remove fault_id, assigned_to, action_type, sequence_order from maintenance_schedules

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_model_restructuring"
down_revision: Union[str, None] = "005_model_improvements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Step 1: Create new association tables ──

    op.create_table(
        "level_competence",
        sa.Column(
            "level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("levels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "competence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competences.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("level_id", "competence_id"),
    )

    op.create_table(
        "task_worker",
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("task_id", "worker_id"),
    )

    # ── Step 2: Add workers.level_id ──

    op.add_column(
        "workers",
        sa.Column(
            "level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ── Step 3: Add new columns to tasks ──

    op.add_column(
        "tasks",
        sa.Column(
            "maintenance_schedule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("maintenance_schedules.id", ondelete="CASCADE"),
            nullable=True,  # nullable first, will be NOT NULL after clean seed
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "shift_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shifts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column("assigned_to", sa.String(255), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "action_type",
            sa.String(100),
            nullable=False,
            server_default="standard",
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "sequence_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # ── Step 4: Add down_events.maintenance_schedule_id ──

    op.add_column(
        "down_events",
        sa.Column(
            "maintenance_schedule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("maintenance_schedules.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ── Step 5: Make down_events.fault_id NOT NULL with CASCADE ──
    # First drop the existing FK constraint, then re-add with CASCADE
    op.drop_constraint("down_events_fault_id_fkey", "down_events", type_="foreignkey")
    op.alter_column("down_events", "fault_id", nullable=False)
    op.create_foreign_key(
        "down_events_fault_id_fkey",
        "down_events",
        "faults",
        ["fault_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── Step 6: Drop old columns from maintenance_schedules ──

    op.drop_column("maintenance_schedules", "assigned_to")
    op.drop_column("maintenance_schedules", "action_type")
    op.drop_column("maintenance_schedules", "sequence_order")
    op.drop_column("maintenance_schedules", "fault_id")


def downgrade() -> None:
    # ── Re-add columns to maintenance_schedules ──
    op.add_column(
        "maintenance_schedules",
        sa.Column(
            "fault_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("faults.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "maintenance_schedules",
        sa.Column("assigned_to", sa.String(255), nullable=True),
    )
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

    # ── Revert down_events.fault_id to nullable with SET NULL ──
    op.drop_constraint("down_events_fault_id_fkey", "down_events", type_="foreignkey")
    op.alter_column("down_events", "fault_id", nullable=True)
    op.create_foreign_key(
        "down_events_fault_id_fkey",
        "down_events",
        "faults",
        ["fault_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── Remove down_events.maintenance_schedule_id ──
    op.drop_column("down_events", "maintenance_schedule_id")

    # ── Remove new columns from tasks ──
    op.drop_column("tasks", "sequence_order")
    op.drop_column("tasks", "action_type")
    op.drop_column("tasks", "assigned_to")
    op.drop_column("tasks", "shift_id")
    op.drop_column("tasks", "maintenance_schedule_id")

    # ── Remove workers.level_id ──
    op.drop_column("workers", "level_id")

    # ── Drop new association tables ──
    op.drop_table("task_worker")
    op.drop_table("level_competence")
