import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.down_event import DownEvent
from app.models.schemas import (
    DownEventCreate,
    DownEventResponse,
    DownEventUpdate,
)
from app.services import down_event_service

router = APIRouter(prefix="/api/v1", tags=["down-events"])


@router.post("/down-events", status_code=201)
async def create_down_event(
    data: DownEventCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Creating down event")

    try:
        down_event = await down_event_service.create_down_event(db, data)
        return SuccessResponse.create(
            data=DownEventResponse(**down_event.to_dict()),
            status_code=201,
            details="Down event created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating down event: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.get("/down-events/statistics")
async def get_down_event_statistics(db: AsyncSession = Depends(get_db)):
    logger.info("Getting down event statistics")

    try:
        total = await db.scalar(select(func.count(DownEvent.id)))
        total_downtime = await db.scalar(
            select(func.coalesce(func.sum(DownEvent.downtime_minutes), 0))
        )
        avg_downtime = await db.scalar(
            select(func.coalesce(func.avg(DownEvent.downtime_minutes), 0))
        )

        result = await db.execute(
            select(
                DownEvent.severity,
                func.count(DownEvent.id),
                func.sum(DownEvent.downtime_minutes),
            ).group_by(DownEvent.severity)
        )
        by_severity = [
            {"severity": r[0], "count": r[1], "total_downtime": r[2]}
            for r in result.all()
        ]

        data = {
            "total_events": total,
            "total_downtime_minutes": total_downtime,
            "avg_downtime_minutes": round(avg_downtime, 2),
            "by_severity": by_severity,
        }

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details="Downtime statistics",
        )
    except Exception as e:
        logger.error(f"Error getting down event statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.get("/down-events")
async def list_down_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    asset_id: Optional[str] = None,
    maintenance_schedule_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing down events (page={page}, per_page={per_page})")

    try:
        down_events, total = await down_event_service.list_down_events(
            db,
            page=page,
            per_page=per_page,
            severity=severity,
            status=status,
            asset_id=asset_id,
            maintenance_schedule_id=maintenance_schedule_id,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [DownEventResponse(**d.to_dict()) for d in down_events]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} down events",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing down events: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.get("/down-events/{down_event_id}")
async def get_down_event(
    down_event_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Getting down event {down_event_id}")

    down_event = await down_event_service.get_down_event(db, down_event_id)
    if not down_event:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Down event not found",
                    "errors": [
                        f"Down event {down_event_id} does not exist"
                    ],
                },
            },
        )

    return SuccessResponse.create(
        data=DownEventResponse(**down_event.to_dict()),
        status_code=200,
        details="Down event retrieved",
    )


@router.put("/down-events/{down_event_id}")
async def update_down_event(
    down_event_id: UUID,
    data: DownEventUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating down event {down_event_id}")

    down_event = await down_event_service.get_down_event(db, down_event_id)
    if not down_event:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Down event not found",
                    "errors": [
                        f"Down event {down_event_id} does not exist"
                    ],
                },
            },
        )

    try:
        updated = await down_event_service.update_down_event(
            db, down_event, data
        )
        return SuccessResponse.create(
            data=DownEventResponse(**updated.to_dict()),
            status_code=200,
            details="Down event updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating down event: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.delete("/down-events/{down_event_id}")
async def delete_down_event(
    down_event_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Deleting down event {down_event_id}")

    down_event = await down_event_service.get_down_event(db, down_event_id)
    if not down_event:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Down event not found",
                    "errors": [
                        f"Down event {down_event_id} does not exist"
                    ],
                },
            },
        )

    try:
        await down_event_service.delete_down_event(db, down_event)
        return SuccessResponse.create(
            data={"id": str(down_event_id)},
            status_code=200,
            details="Down event deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting down event: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )
