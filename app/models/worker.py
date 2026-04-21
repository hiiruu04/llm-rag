from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    status = Column(String(50), nullable=False, default="active")
    level_id = Column(
        UUID(as_uuid=True), ForeignKey("levels.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    level = relationship("Level", back_populates="workers")
    tasks = relationship("Task", secondary="task_worker", back_populates="workers")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "employee_id": self.employee_id,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "level_id": str(self.level_id) if self.level_id else None,
            "level_name": self.level.name if self.level else None,
            "role_id": str(self.level.role_id) if self.level and self.level.role_id else None,
            "role_name": self.level.role.name if self.level and self.level.role else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
