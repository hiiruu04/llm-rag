"""011_drop_task_assigned_to

Revision ID: 011_drop_task_assigned_to
Revises: 010_chat_sessions
Create Date: 2026-04-22

Drop the assigned_to column from tasks table.
Worker assignment is now tracked exclusively via the task_worker association table.

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "011_drop_task_assigned_to"
down_revision: Union[str, None] = "010_chat_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("tasks", "assigned_to")


def downgrade() -> None:
    op.add_column("tasks", sa.Column("assigned_to", sa.String(255), nullable=True))
