from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    order_number = Column(String(100), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    order_type = Column(String(100), nullable=False, default="maintenance")
    status = Column(String(50), nullable=False, default="open")
    priority = Column(String(50), nullable=False, default="medium")
    requested_date = Column(DateTime(timezone=True))
    maintenance_schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_schedules.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    maintenance_schedule = relationship("MaintenanceSchedule", back_populates="order")
    materials = relationship("Material", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "order_number": self.order_number,
            "title": self.title,
            "description": self.description,
            "order_type": self.order_type,
            "status": self.status,
            "priority": self.priority,
            "requested_date": self.requested_date.isoformat() if self.requested_date else None,
            "maintenance_schedule_id": str(self.maintenance_schedule_id) if self.maintenance_schedule_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
