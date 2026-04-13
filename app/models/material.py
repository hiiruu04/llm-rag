from sqlalchemy import Column, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    part_number = Column(String(100))
    description = Column(Text)
    quantity_in_stock = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "part_number": self.part_number,
            "description": self.description,
            "quantity_in_stock": self.quantity_in_stock,
            "unit": self.unit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
