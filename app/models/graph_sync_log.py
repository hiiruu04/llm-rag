from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class GraphSyncLog(Base):
    __tablename__ = "graph_sync_log"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    sync_type = Column(String(20), nullable=False)  # "full" or "incremental"
    status = Column(String(20), nullable=False)  # "started", "completed", "failed"
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    records_processed = Column(Integer, default=0)
    error_message = Column(Text)
    metadata_ = Column("metadata", JSONB)
