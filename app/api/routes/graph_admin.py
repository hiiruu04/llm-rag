from typing import Optional

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from app.api.models import SuccessResponse
from app.core.neo4j import get_neo4j_info
from app.services.graph_sync_service import get_graph_sync_service

router = APIRouter(prefix="/api/v1", tags=["graph-admin"])


class SyncStatusData(BaseModel):
    synced: bool
    sync_in_progress: bool
    last_full_sync: Optional[str] = None
    last_incremental_sync: Optional[str] = None
    total_assets: Optional[int] = None
    total_sensors: Optional[int] = None
    total_faults: Optional[int] = None
    total_schedules: Optional[int] = None


class SyncResultData(BaseModel):
    status: str
    records_processed: int = 0
    error: Optional[str] = None
    counts: Optional[dict] = None


class GraphInfoData(BaseModel):
    connected: bool
    error: Optional[str] = None
    total_assets: Optional[int] = None
    total_sensors: Optional[int] = None
    total_faults: Optional[int] = None
    total_maintenanceschedules: Optional[int] = None
    total_sensorsummaries: Optional[int] = None
    last_full_sync: Optional[str] = None
    last_incremental_sync: Optional[str] = None
    sync_in_progress: Optional[bool] = None


@router.post("/admin/graph/sync/full")
async def trigger_full_sync():
    logger.info("Full sync triggered via API")
    sync_service = get_graph_sync_service()
    result = await sync_service.full_sync()
    data = SyncResultData(**result)
    return SuccessResponse.create(data=data, status_code=200, details="Full sync triggered")


@router.post("/admin/graph/sync/incremental")
async def trigger_incremental_sync():
    logger.info("Incremental sync triggered via API")
    sync_service = get_graph_sync_service()
    result = await sync_service.incremental_sync()
    data = SyncResultData(**result)
    return SuccessResponse.create(data=data, status_code=200, details="Incremental sync triggered")


@router.get("/admin/graph/sync/status")
async def get_sync_status():
    sync_service = get_graph_sync_service()
    status = await sync_service.get_sync_status()
    data = SyncStatusData(**status)
    return SuccessResponse.create(data=data, status_code=200, details="Sync status retrieved")


@router.get("/graph/info")
async def get_graph_info():
    info = await get_neo4j_info()
    data = GraphInfoData(**info)
    return SuccessResponse.create(data=data, status_code=200, details="Graph info retrieved")
