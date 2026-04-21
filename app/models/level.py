from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Level(Base):
    __tablename__ = "levels"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(100), nullable=False, unique=True)
    rank = Column(Integer, nullable=False, default=0)
    description = Column(Text)
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    role = relationship("Role", back_populates="levels")
    workers = relationship("Worker", back_populates="level")
    competences = relationship("Competence", secondary="level_competence", back_populates="levels")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "rank": self.rank,
            "description": self.description,
            "role_id": str(self.role_id) if self.role_id else None,
            "role_name": self.role.name if self.role else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
