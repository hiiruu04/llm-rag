from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Cause(Base):
    __tablename__ = "causes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(100))
    severity = Column(String(50), nullable=False, default="medium")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
