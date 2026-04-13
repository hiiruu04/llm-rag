from datetime import datetime, time
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# --- Enums as Literals ---

AssetStatus = Literal["active", "inactive", "maintenance", "decommissioned"]
SensorStatus = Literal["active", "inactive", "faulty"]
FaultSeverity = Literal["low", "medium", "high", "critical"]
FaultStatus = Literal["open", "investigating", "resolved", "closed"]
FaultLinkType = Literal["cause", "effect"]


# --- Asset Schemas ---


class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[UUID] = None
    status: AssetStatus = "active"
    location: Optional[str] = Field(None, max_length=255)


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_id: Optional[UUID] = None
    status: Optional[AssetStatus] = None
    location: Optional[str] = Field(None, max_length=255)


class AssetResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    asset_type: str
    parent_id: Optional[UUID]
    status: str
    location: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AssetTreeNode(BaseModel):
    id: UUID
    name: str
    asset_type: str
    status: str
    children: list["AssetTreeNode"] = []


# --- Sensor Schemas ---


class SensorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sensor_type: str = Field(..., min_length=1, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    status: SensorStatus = "active"


class SensorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sensor_type: Optional[str] = Field(None, min_length=1, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    status: Optional[SensorStatus] = None


class SensorResponse(BaseModel):
    id: UUID
    asset_id: UUID
    name: str
    sensor_type: str
    unit: Optional[str]
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Sensor Data Schemas ---


class SensorDataCreate(BaseModel):
    timestamp: Optional[datetime] = None
    value: float


class SensorDataBatchCreate(BaseModel):
    readings: list[SensorDataCreate] = Field(..., max_length=1000)


class SensorDataResponse(BaseModel):
    id: int
    sensor_id: UUID
    timestamp: Optional[datetime] = None
    value: float


class BatchInsertResponse(BaseModel):
    count: int


class DeletedCountResponse(BaseModel):
    deleted_count: int


# --- Fault Schemas ---


class FaultCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: FaultSeverity = "medium"
    status: FaultStatus = "open"
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class FaultUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Optional[FaultSeverity] = None
    status: Optional[FaultStatus] = None
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class FaultResponse(BaseModel):
    id: UUID
    asset_id: UUID
    code: str
    name: str
    description: Optional[str]
    severity: str
    status: str
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FaultLinkCreate(BaseModel):
    linked_fault_id: UUID
    link_type: FaultLinkType


# --- Maintenance Schedule Schemas ---

MaintenanceType = Literal["preventive", "corrective", "predictive"]
MaintenanceStatus = Literal["scheduled", "in_progress", "completed", "cancelled", "overdue"]
MaintenancePriority = Literal["low", "medium", "high", "critical"]
MaintenanceRecurrence = Literal["none", "daily", "weekly", "monthly", "quarterly", "yearly"]


class MaintenanceScheduleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    maintenance_type: MaintenanceType = "preventive"
    priority: MaintenancePriority = "medium"
    scheduled_date: datetime
    fault_id: Optional[UUID] = None
    assigned_to: Optional[str] = Field(None, max_length=255)
    recurrence: MaintenanceRecurrence = "none"
    estimated_duration_hours: Optional[float] = None
    notes: Optional[str] = None


class MaintenanceScheduleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    maintenance_type: Optional[MaintenanceType] = None
    status: Optional[MaintenanceStatus] = None
    priority: Optional[MaintenancePriority] = None
    scheduled_date: Optional[datetime] = None
    fault_id: Optional[UUID] = None
    assigned_to: Optional[str] = Field(None, max_length=255)
    recurrence: Optional[MaintenanceRecurrence] = None
    estimated_duration_hours: Optional[float] = None
    notes: Optional[str] = None


class MaintenanceScheduleResponse(BaseModel):
    id: UUID
    asset_id: UUID
    fault_id: Optional[UUID]
    title: str
    description: Optional[str]
    maintenance_type: str
    status: str
    priority: str
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    assigned_to: Optional[str]
    recurrence: str
    estimated_duration_hours: Optional[float]
    notes: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- New Entity Literal Enums ---

WorkerStatus = Literal["active", "inactive", "on_leave"]
TaskStatus = Literal["pending", "in_progress", "completed", "cancelled"]
TaskType = Literal["general", "inspection", "repair", "installation", "calibration"]
CauseSeverity = Literal["low", "medium", "high", "critical"]
DownEventStatus = Literal["active", "resolved"]
OrderStatus = Literal["open", "in_progress", "completed", "cancelled"]
OrderPriority = Literal["low", "medium", "high", "critical"]
OrderType = Literal["maintenance", "repair", "inspection", "installation"]


# --- Worker Schemas ---


class WorkerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    employee_id: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    status: WorkerStatus = "active"


class WorkerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    employee_id: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    status: Optional[WorkerStatus] = None


class WorkerResponse(BaseModel):
    id: UUID
    name: str
    employee_id: str
    email: Optional[str]
    phone: Optional[str]
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Role Schemas ---


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Competence Schemas ---


class CompetenceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)


class CompetenceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)


class CompetenceResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Level Schemas ---


class LevelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rank: int = 0
    description: Optional[str] = None


class LevelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rank: Optional[int] = None
    description: Optional[str] = None


class LevelResponse(BaseModel):
    id: UUID
    name: str
    rank: int
    description: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Task Schemas ---


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: TaskType = "general"
    status: TaskStatus = "pending"
    estimated_duration_hours: Optional[float] = None
    doc_link: Optional[str] = Field(None, max_length=500)


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    estimated_duration_hours: Optional[float] = None
    doc_link: Optional[str] = Field(None, max_length=500)


class TaskResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    task_type: str
    status: str
    estimated_duration_hours: Optional[float]
    doc_link: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Action Schemas ---


class ActionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    action_type: str = Field("standard", max_length=100)
    sequence_order: int = 0


class ActionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    action_type: Optional[str] = Field(None, max_length=100)
    sequence_order: Optional[int] = None


class ActionResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    action_type: str
    sequence_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Cause Schemas ---


class CauseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    severity: CauseSeverity = "medium"


class CauseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    severity: Optional[CauseSeverity] = None


class CauseResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    severity: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Material Schemas ---


class MaterialCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    part_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    quantity_in_stock: float = 0.0
    unit: Optional[str] = Field(None, max_length=50)


class MaterialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    part_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    quantity_in_stock: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)


class MaterialResponse(BaseModel):
    id: UUID
    name: str
    part_number: Optional[str]
    description: Optional[str]
    quantity_in_stock: float
    unit: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Shift Schemas ---


class ShiftCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    start_time: time
    end_time: time
    description: Optional[str] = None


class ShiftUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    description: Optional[str] = None


class ShiftResponse(BaseModel):
    id: UUID
    name: str
    start_time: time
    end_time: time
    description: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- DownEvent Schemas ---


class DownEventCreate(BaseModel):
    asset_id: UUID
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    downtime_minutes: int = 0
    description: Optional[str] = None
    severity: CauseSeverity = "medium"
    status: DownEventStatus = "active"


class DownEventUpdate(BaseModel):
    asset_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    downtime_minutes: Optional[int] = None
    description: Optional[str] = None
    severity: Optional[CauseSeverity] = None
    status: Optional[DownEventStatus] = None


class DownEventResponse(BaseModel):
    id: UUID
    asset_id: UUID
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    downtime_minutes: int
    description: Optional[str]
    severity: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Order Schemas ---


class OrderCreate(BaseModel):
    order_number: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order_type: OrderType = "maintenance"
    status: OrderStatus = "open"
    priority: OrderPriority = "medium"
    requested_date: Optional[datetime] = None


class OrderUpdate(BaseModel):
    order_number: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_type: Optional[OrderType] = None
    status: Optional[OrderStatus] = None
    priority: Optional[OrderPriority] = None
    requested_date: Optional[datetime] = None


class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    title: str
    description: Optional[str]
    order_type: str
    status: str
    priority: str
    requested_date: Optional[datetime]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Location Schemas ---


class LocationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location_type: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[UUID] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location_type: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[UUID] = None


class LocationResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    location_type: Optional[str]
    parent_id: Optional[UUID]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- System Schemas ---


class SystemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class SystemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class SystemResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Aggregate Schemas ---


class AggregateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AggregateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class AggregateResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
