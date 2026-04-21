from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    part_number = Column(String(100))
    description = Column(Text)
    quantity_in_stock = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50))
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    order = relationship("Order", back_populates="materials")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "part_number": self.part_number,
            "description": self.description,
            "quantity_in_stock": self.quantity_in_stock,
            "unit": self.unit,
            "order_id": str(self.order_id) if self.order_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
