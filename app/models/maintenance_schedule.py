from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    asset_id = Column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text)
    maintenance_type = Column(String(20), nullable=False, server_default="preventive")
    status = Column(String(20), nullable=False, server_default="scheduled")
    priority = Column(String(20), nullable=False, server_default="medium")
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    completed_date = Column(DateTime(timezone=True))
    recurrence = Column(String(20), nullable=False, server_default="none")
    estimated_duration_hours = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    asset = relationship("Asset", back_populates="maintenance_schedules")
    tasks = relationship(
        "Task", back_populates="maintenance_schedule", cascade="all, delete-orphan"
    )
    down_events = relationship("DownEvent", back_populates="maintenance_schedule")
    order = relationship("Order", back_populates="maintenance_schedule", uselist=False)

    def to_dict(self, include_relations: bool = False) -> dict:
        data = {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "title": self.title,
            "description": self.description,
            "maintenance_type": self.maintenance_type,
            "status": self.status,
            "priority": self.priority,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "recurrence": self.recurrence,
            "estimated_duration_hours": self.estimated_duration_hours,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            data["asset"] = self.asset.to_dict() if self.asset else None
            data["down_events"] = [de.to_dict() for de in (self.down_events or [])]
            data["order"] = self.order.to_dict() if self.order else None
            data["tasks"] = [t.to_dict() for t in (self.tasks or [])]
        return data
