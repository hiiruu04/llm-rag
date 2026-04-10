from sqlalchemy import BigInteger, Column, DateTime, Double, ForeignKey, Index, desc, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"
    __table_args__ = (
        Index(
            "ix_sensor_data_sensor_id_timestamp",
            "sensor_id",
            desc("timestamp"),
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sensor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sensors.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp = Column(
        "timestamp",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    value = Column(Double, nullable=False)

    sensor = relationship("Sensor", back_populates="readings")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sensor_id": str(self.sensor_id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "value": self.value,
        }
