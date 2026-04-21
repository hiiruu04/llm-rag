from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

# Asset(=Equipment) <-> Worker (many-to-many)
asset_worker_assignment = Table(
    "asset_worker_assignment",
    Base.metadata,
    Column(
        "asset_id",
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "worker_id",
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("asset_id", "worker_id"),
)

# Worker <-> Competence (many-to-many)
worker_competence = Table(
    "worker_competence",
    Base.metadata,
    Column(
        "worker_id",
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "competence_id",
        UUID(as_uuid=True),
        ForeignKey("competences.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "level_id",
        UUID(as_uuid=True),
        ForeignKey("levels.id", ondelete="SET NULL"),
        nullable=True,
    ),
    UniqueConstraint("worker_id", "competence_id"),
)

# Task <-> Competence (many-to-many)
task_competence = Table(
    "task_competence",
    Base.metadata,
    Column(
        "task_id",
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "competence_id",
        UUID(as_uuid=True),
        ForeignKey("competences.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "level_id",
        UUID(as_uuid=True),
        ForeignKey("levels.id", ondelete="SET NULL"),
        nullable=True,
    ),
    UniqueConstraint("task_id", "competence_id"),
)

# Task <-> Material (many-to-many)
task_material = Table(
    "task_material",
    Base.metadata,
    Column(
        "task_id",
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "material_id",
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("quantity_required", nullable=True),
    UniqueConstraint("task_id", "material_id"),
)

# Cause <-> Role (many-to-many)
cause_role = Table(
    "cause_role",
    Base.metadata,
    Column(
        "cause_id",
        UUID(as_uuid=True),
        ForeignKey("causes.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("cause_id", "role_id"),
)

# Role <-> Task (many-to-many)
role_task = Table(
    "role_task",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "task_id",
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("role_id", "task_id"),
)

# MaintenanceSchedule <-> Competence (many-to-many)
maintenance_competence = Table(
    "maintenance_competence",
    Base.metadata,
    Column(
        "maintenance_schedule_id",
        UUID(as_uuid=True),
        ForeignKey("maintenance_schedules.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "competence_id",
        UUID(as_uuid=True),
        ForeignKey("competences.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("maintenance_schedule_id", "competence_id"),
)

# Worker <-> Shift (many-to-many)
worker_shift = Table(
    "worker_shift",
    Base.metadata,
    Column(
        "worker_id",
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "shift_id",
        UUID(as_uuid=True),
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("worker_id", "shift_id"),
)

# Task <-> Worker (many-to-many)
task_worker = Table(
    "task_worker",
    Base.metadata,
    Column(
        "task_id",
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "worker_id",
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("task_id", "worker_id"),
)

# Level <-> Competence (many-to-many)
level_competence = Table(
    "level_competence",
    Base.metadata,
    Column(
        "level_id",
        UUID(as_uuid=True),
        ForeignKey("levels.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "competence_id",
        UUID(as_uuid=True),
        ForeignKey("competences.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("level_id", "competence_id"),
)

# Asset(=Equipment) <-> System (many-to-many)
asset_system = Table(
    "asset_system",
    Base.metadata,
    Column(
        "asset_id",
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "system_id",
        UUID(as_uuid=True),
        ForeignKey("systems.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("asset_id", "system_id"),
)

# System <-> Aggregate (many-to-many)
system_aggregate = Table(
    "system_aggregate",
    Base.metadata,
    Column(
        "system_id",
        UUID(as_uuid=True),
        ForeignKey("systems.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "aggregate_id",
        UUID(as_uuid=True),
        ForeignKey("aggregates.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("system_id", "aggregate_id"),
)

# DownEvent <-> Cause (many-to-many)
down_event_cause = Table(
    "down_event_cause",
    Base.metadata,
    Column(
        "down_event_id",
        UUID(as_uuid=True),
        ForeignKey("down_events.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "cause_id",
        UUID(as_uuid=True),
        ForeignKey("causes.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("down_event_id", "cause_id"),
)

# Order <-> Asset(=Equipment) (many-to-many)
order_asset = Table(
    "order_asset",
    Base.metadata,
    Column(
        "order_id",
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "asset_id",
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("order_id", "asset_id"),
)

# Asset(=Equipment) <-> Location (many-to-many)
asset_location = Table(
    "asset_location",
    Base.metadata,
    Column(
        "asset_id",
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "location_id",
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("asset_id", "location_id"),
)
