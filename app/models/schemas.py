from datetime import datetime
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
