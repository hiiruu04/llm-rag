from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text)
    task_type = Column(String(100), nullable=False, default="general")
    status = Column(String(50), nullable=False, default="pending")
    estimated_duration_hours = Column(Float)
    doc_link = Column(String(500))
    maintenance_schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )
    shift_id = Column(
        UUID(as_uuid=True), ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True
    )
    action_type = Column(String(100), nullable=False, default="standard")
    sequence_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    maintenance_schedule = relationship("MaintenanceSchedule", back_populates="tasks")
    shift = relationship("Shift")
    workers = relationship("Worker", secondary="task_worker", back_populates="tasks")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status,
            "estimated_duration_hours": self.estimated_duration_hours,
            "doc_link": self.doc_link,
            "maintenance_schedule_id": str(self.maintenance_schedule_id),
            "shift_id": str(self.shift_id) if self.shift_id else None,
            "worker_ids": [str(w.id) for w in self.workers] if self.workers else [],
            "action_type": self.action_type,
            "sequence_order": self.sequence_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
