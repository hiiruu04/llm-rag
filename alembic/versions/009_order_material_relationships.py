"""009_order_material_relationships

Revision ID: 009_order_material_relationships
Revises: 008_level_role_fk
Create Date: 2026-04-20

Add one-to-one relationship between Order and MaintenanceSchedule.
Add one-to-many relationship between Order and Material (order_id FK on materials).

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009_order_material_relationships"
down_revision: Union[str, None] = "008_level_role_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Order -> MaintenanceSchedule (one-to-one)
    op.add_column(
        "orders",
        sa.Column(
            "maintenance_schedule_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_orders_maintenance_schedule_id",
        "orders",
        "maintenance_schedules",
        ["maintenance_schedule_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_orders_maintenance_schedule_id",
        "orders",
        ["maintenance_schedule_id"],
    )

    # Material -> Order (many-to-one, making Order-to-Material one-to-many)
    op.add_column(
        "materials",
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_materials_order_id",
        "materials",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_materials_order_id", "materials", type_="foreignkey")
    op.drop_column("materials", "order_id")

    op.drop_constraint("uq_orders_maintenance_schedule_id", "orders", type_="unique")
    op.drop_constraint("fk_orders_maintenance_schedule_id", "orders", type_="foreignkey")
    op.drop_column("orders", "maintenance_schedule_id")
