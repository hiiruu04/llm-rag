"""008_level_role_fk

Revision ID: 008_level_role_fk
Revises: 007_drop_down_event_description
Create Date: 2026-04-17

Add role_id FK to levels table (nullable, SET NULL on delete).
Each Role can now own multiple Levels.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_level_role_fk"
down_revision: Union[str, None] = "007_drop_down_event_description"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "levels",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_levels_role_id",
        "levels",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_levels_role_id", "levels", type_="foreignkey")
    op.drop_column("levels", "role_id")
