from sqlalchemy import Column, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

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
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status,
            "estimated_duration_hours": self.estimated_duration_hours,
            "doc_link": self.doc_link,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
