"""007_drop_down_event_description

Revision ID: 007_drop_down_event_description
Revises: 006_model_restructuring
Create Date: 2026-04-17

Drop description column from down_events (now redundant with fault.name).

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_drop_down_event_description"
down_revision: Union[str, None] = "006_model_restructuring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("down_events", "description")


def downgrade() -> None:
    op.add_column("down_events", sa.Column("description", sa.Text(), nullable=True))
