from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

fault_cause_effect = Table(
    "fault_cause_effect",
    Base.metadata,
    Column(
        "causing_fault_id",
        UUID(as_uuid=True),
        ForeignKey("faults.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "affected_fault_id",
        UUID(as_uuid=True),
        ForeignKey("faults.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("link_type", String(20), nullable=False),
    UniqueConstraint("causing_fault_id", "affected_fault_id"),
)


class Fault(Base):
    __tablename__ = "faults"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    asset_id = Column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(String(20), nullable=False, default="medium")
    status = Column(String(50), nullable=False, default="open")
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("asset_id", "code"),)

    asset = relationship("Asset", back_populates="faults")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
