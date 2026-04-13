"""004 knowledge_graph_schema

Revision ID: 004_kg
Revises: 003_graph_sync_log
Create Date: 2026-04-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_kg"
down_revision: Union[str, None] = "003_graph_sync_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Independent entity tables (no FK dependencies on each other) ──

    op.create_table(
        "levels",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text),
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

    op.create_table(
        "competences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(100)),
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

    op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
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

    op.create_table(
        "shifts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("description", sa.Text),
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

    op.create_table(
        "locations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("location_type", sa.String(100)),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
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

    op.create_table(
        "aggregates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
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

    op.create_table(
        "systems",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
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

    op.create_table(
        "workers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("employee_id", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="active",
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

    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "task_type",
            sa.String(100),
            nullable=False,
            server_default="general",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("estimated_duration_hours", sa.Float),
        sa.Column("doc_link", sa.String(500)),
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

    op.create_table(
        "causes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(100)),
        sa.Column(
            "severity",
            sa.String(50),
            nullable=False,
            server_default="medium",
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

    op.create_table(
        "materials",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("part_number", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column(
            "quantity_in_stock",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column("unit", sa.String(50)),
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

    # ── Entity tables with FK dependencies on assets (created in 001) ──

    op.create_table(
        "down_events",
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
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column(
            "downtime_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("description", sa.Text),
        sa.Column(
            "severity",
            sa.String(50),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="active",
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

    op.create_table(
        "orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("order_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "order_type",
            sa.String(100),
            nullable=False,
            server_default="maintenance",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "priority",
            sa.String(50),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("requested_date", sa.DateTime(timezone=True)),
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

    # ── Junction tables ──

    op.create_table(
        "asset_worker_assignment",
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id"),
            nullable=False,
        ),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("asset_id", "worker_id"),
    )

    op.create_table(
        "worker_competence",
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id"),
            nullable=False,
        ),
        sa.Column(
            "competence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competences.id"),
            nullable=False,
        ),
        sa.Column(
            "level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("levels.id", ondelete="SET NULL"),
        ),
        sa.UniqueConstraint("worker_id", "competence_id"),
    )

    op.create_table(
        "task_competence",
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id"),
            nullable=False,
        ),
        sa.Column(
            "competence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competences.id"),
            nullable=False,
        ),
        sa.Column(
            "level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("levels.id", ondelete="SET NULL"),
        ),
        sa.UniqueConstraint("task_id", "competence_id"),
    )

    op.create_table(
        "task_material",
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id"),
            nullable=False,
        ),
        sa.Column(
            "material_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materials.id"),
            nullable=False,
        ),
        sa.Column("quantity_required", sa.Float()),
        sa.UniqueConstraint("task_id", "material_id"),
    )

    op.create_table(
        "cause_role",
        sa.Column(
            "cause_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("causes.id"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("cause_id", "role_id"),
    )

    op.create_table(
        "role_task",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("role_id", "task_id"),
    )

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

    op.create_table(
        "worker_shift",
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id"),
            nullable=False,
        ),
        sa.Column(
            "shift_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shifts.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("worker_id", "shift_id"),
    )

    op.create_table(
        "asset_system",
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id"),
            nullable=False,
        ),
        sa.Column(
            "system_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("systems.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("asset_id", "system_id"),
    )

    op.create_table(
        "system_aggregate",
        sa.Column(
            "system_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("systems.id"),
            nullable=False,
        ),
        sa.Column(
            "aggregate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("aggregates.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("system_id", "aggregate_id"),
    )

    op.create_table(
        "down_event_cause",
        sa.Column(
            "down_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("down_events.id"),
            nullable=False,
        ),
        sa.Column(
            "cause_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("causes.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("down_event_id", "cause_id"),
    )

    op.create_table(
        "order_asset",
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("order_id", "asset_id"),
    )

    op.create_table(
        "asset_location",
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("asset_id", "location_id"),
    )


def downgrade() -> None:
    # Drop junction tables first (reverse of creation order)
    op.drop_table("asset_location")
    op.drop_table("order_asset")
    op.drop_table("down_event_cause")
    op.drop_table("system_aggregate")
    op.drop_table("asset_system")
    op.drop_table("worker_shift")
    op.drop_table("action_competence")
    op.drop_table("role_task")
    op.drop_table("cause_role")
    op.drop_table("task_material")
    op.drop_table("task_competence")
    op.drop_table("worker_competence")
    op.drop_table("asset_worker_assignment")

    # Drop entity tables (reverse of creation order)
    op.drop_table("orders")
    op.drop_table("down_events")
    op.drop_table("actions")
    op.drop_table("materials")
    op.drop_table("causes")
    op.drop_table("tasks")
    op.drop_table("workers")
    op.drop_table("systems")
    op.drop_table("aggregates")
    op.drop_table("locations")
    op.drop_table("shifts")
    op.drop_table("roles")
    op.drop_table("competences")
    op.drop_table("levels")
