"""003 graph_sync_log

Revision ID: 003_graph_sync_log
Revises: 002_maintenance_schedules
Create Date: 2026-04-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_graph_sync_log"
down_revision: Union[str, None] = "002_maintenance_schedules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "graph_sync_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("sync_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("records_processed", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text),
        sa.Column("metadata", postgresql.JSONB),
    )


def downgrade() -> None:
    op.drop_table("graph_sync_log")
