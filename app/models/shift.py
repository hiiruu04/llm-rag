from sqlalchemy import Column, DateTime, String, Text, Time, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(100), nullable=False, unique=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
