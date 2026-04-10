from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text)
    asset_type = Column(String(100), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"))
    status = Column(String(50), nullable=False, default="active")
    location = Column(String(255))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    parent = relationship("Asset", remote_side=[id], backref="children")
    sensors = relationship("Sensor", back_populates="asset", cascade="all, delete-orphan")
    faults = relationship("Fault", back_populates="asset", cascade="all, delete-orphan")
    maintenance_schedules = relationship(
        "MaintenanceSchedule", back_populates="asset", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "asset_type": self.asset_type,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "status": self.status,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
