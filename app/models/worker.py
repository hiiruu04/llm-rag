from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "employee_id": self.employee_id,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
