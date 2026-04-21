from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DownEvent(Base):
    __tablename__ = "down_events"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    asset_id = Column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    fault_id = Column(UUID(as_uuid=True), ForeignKey("faults.id", ondelete="CASCADE"), nullable=False)
    maintenance_schedule_id = Column(
        UUID(as_uuid=True), ForeignKey("maintenance_schedules.id", ondelete="SET NULL"), nullable=True
    )
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    downtime_minutes = Column(Integer, nullable=False, default=0)
    severity = Column(String(50), nullable=False, default="medium")
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    fault = relationship("Fault", back_populates="down_events")
    maintenance_schedule = relationship("MaintenanceSchedule", back_populates="down_events")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "fault_id": str(self.fault_id),
            "fault_name": self.fault.name if self.fault else None,
            "maintenance_schedule_id": str(self.maintenance_schedule_id) if self.maintenance_schedule_id else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "downtime_minutes": self.downtime_minutes,
            "severity": self.severity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
