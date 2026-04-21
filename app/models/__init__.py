from app.models.aggregate import Aggregate
from app.models.asset import Asset
from app.models.cause import Cause
from app.models.competence import Competence
from app.models.down_event import DownEvent
from app.models.fault import Fault, fault_cause_effect
from app.models.graph_associations import (
    asset_location,
    asset_system,
    asset_worker_assignment,
    cause_role,
    down_event_cause,
    level_competence,
    maintenance_competence,
    order_asset,
    role_task,
    system_aggregate,
    task_competence,
    task_material,
    task_worker,
    worker_competence,
    worker_shift,
)
from app.models.graph_sync_log import GraphSyncLog
from app.models.level import Level
from app.models.location import Location
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.material import Material
from app.models.order import Order
from app.models.role import Role
from app.models.sensor import Sensor
from app.models.sensor_data import SensorData
from app.models.shift import Shift
from app.models.system import System
from app.models.task import Task
from app.models.worker import Worker

__all__ = [
    "Aggregate",
    "Asset",
    "Cause",
    "Competence",
    "DownEvent",
    "Fault",
    "GraphSyncLog",
    "Level",
    "Location",
    "MaintenanceSchedule",
    "Material",
    "Order",
    "Role",
    "Sensor",
    "SensorData",
    "Shift",
    "System",
    "Task",
    "Worker",
    # Association tables
    "fault_cause_effect",
    "maintenance_competence",
    "asset_location",
    "asset_system",
    "asset_worker_assignment",
    "cause_role",
    "down_event_cause",
    "level_competence",
    "order_asset",
    "role_task",
    "system_aggregate",
    "task_competence",
    "task_material",
    "task_worker",
    "worker_competence",
    "worker_shift",
]
