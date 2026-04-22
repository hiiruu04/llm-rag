import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    MaintenanceScheduleCreate,
    MaintenanceScheduleDetailResponse,
    MaintenanceScheduleResponse,
    MaintenanceScheduleUpdate,
)
from app.services import asset_service
from app.services import maintenance_schedule_service as schedule_service

router = APIRouter(prefix="/api/v1", tags=["maintenance-schedules"])


@router.post("/assets/{asset_id}/maintenance-schedules", status_code=201)
async def create_schedule(
    asset_id: UUID,
    data: MaintenanceScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating maintenance schedule for asset {asset_id}: {data.title}")

    asset = await asset_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Asset not found",
                    "errors": [f"Asset {asset_id} does not exist"],
                },
            },
        )

    try:
        schedule = await schedule_service.create_schedule(db, asset_id, data)
        return SuccessResponse.create(
            data=MaintenanceScheduleResponse(**schedule.to_dict()),
            status_code=201,
            details="Maintenance schedule created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating maintenance schedule: {e}")
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


@router.get("/assets/{asset_id}/maintenance-schedules")
async def list_asset_schedules(
    asset_id: UUID,
    status: str | None = Query(None),
    maintenance_type: str | None = Query(None),
    priority: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing maintenance schedules for asset {asset_id}")

    asset = await asset_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Asset not found",
                    "errors": [f"Asset {asset_id} does not exist"],
                },
            },
        )

    try:
        schedules, total = await schedule_service.list_schedules(
            db,
            asset_id=asset_id,
            status=status,
            maintenance_type=maintenance_type,
            priority=priority,
            page=page,
            per_page=per_page,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [MaintenanceScheduleResponse(**s.to_dict()) for s in schedules]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} maintenance schedules",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing maintenance schedules: {e}")
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


@router.get("/maintenance-schedules")
async def list_all_schedules(
    asset_id: UUID | None = Query(None),
    status: str | None = Query(None),
    maintenance_type: str | None = Query(None),
    priority: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info("Listing all maintenance schedules")

    try:
        schedules, total = await schedule_service.list_schedules(
            db,
            asset_id=asset_id,
            status=status,
            maintenance_type=maintenance_type,
            priority=priority,
            page=page,
            per_page=per_page,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [MaintenanceScheduleResponse(**s.to_dict()) for s in schedules]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} maintenance schedules",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing maintenance schedules: {e}")
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


@router.get("/maintenance-schedules/overdue")
async def list_overdue_schedules(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info("Listing overdue maintenance schedules")

    try:
        schedules, total = await schedule_service.get_overdue_schedules(db, page, per_page)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [MaintenanceScheduleResponse(**s.to_dict()) for s in schedules]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} overdue maintenance schedules",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing overdue schedules: {e}")
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


@router.post("/maintenance-schedules/detect-overdue")
async def detect_overdue(db: AsyncSession = Depends(get_db)):
    logger.info("Detecting and marking overdue maintenance schedules")

    try:
        overdue = await schedule_service.detect_and_mark_overdue(db)
        data = [MaintenanceScheduleResponse(**s.to_dict()) for s in overdue]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Marked {len(data)} schedules as overdue",
        )
    except Exception as e:
        logger.error(f"Error detecting overdue schedules: {e}")
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


@router.get("/maintenance-schedules/{schedule_id}/detail")
async def get_schedule_detail(schedule_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting maintenance schedule detail {schedule_id}")

    schedule = await schedule_service.get_schedule_detail(db, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Maintenance schedule not found",
                    "errors": [f"Schedule {schedule_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=MaintenanceScheduleDetailResponse(**schedule.to_dict(include_relations=True)),
        status_code=200,
        details="Maintenance schedule detail retrieved",
    )


@router.get("/maintenance-schedules/{schedule_id}")
async def get_schedule(schedule_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting maintenance schedule {schedule_id}")

    schedule = await schedule_service.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Maintenance schedule not found",
                    "errors": [f"Schedule {schedule_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=MaintenanceScheduleResponse(**schedule.to_dict()),
        status_code=200,
        details="Maintenance schedule retrieved",
    )


@router.put("/maintenance-schedules/{schedule_id}")
async def update_schedule(
    schedule_id: UUID,
    data: MaintenanceScheduleUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating maintenance schedule {schedule_id}")

    schedule = await schedule_service.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Maintenance schedule not found",
                    "errors": [f"Schedule {schedule_id} does not exist"],
                },
            },
        )

    try:
        updated = await schedule_service.update_schedule(db, schedule, data)
        return SuccessResponse.create(
            data=MaintenanceScheduleResponse(**updated.to_dict()),
            status_code=200,
            details="Maintenance schedule updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating maintenance schedule: {e}")
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


@router.delete("/maintenance-schedules/{schedule_id}")
async def delete_schedule(schedule_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting maintenance schedule {schedule_id}")

    schedule = await schedule_service.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Maintenance schedule not found",
                    "errors": [f"Schedule {schedule_id} does not exist"],
                },
            },
        )

    try:
        await schedule_service.delete_schedule(db, schedule)
        return SuccessResponse.create(
            data={"id": str(schedule_id)},
            status_code=200,
            details="Maintenance schedule deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting maintenance schedule: {e}")
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


@router.post("/maintenance-schedules/{schedule_id}/complete")
async def complete_schedule(schedule_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Completing maintenance schedule {schedule_id}")

    schedule = await schedule_service.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Maintenance schedule not found",
                    "errors": [f"Schedule {schedule_id} does not exist"],
                },
            },
        )

    try:
        completed = await schedule_service.mark_completed(db, schedule)

        next_occurrence = await schedule_service.generate_next_recurrence(db, completed)

        response_data = {
            "completed": MaintenanceScheduleResponse(**completed.to_dict()),
            "next_occurrence": (
                MaintenanceScheduleResponse(**next_occurrence.to_dict())
                if next_occurrence
                else None
            ),
        }

        return SuccessResponse.create(
            data=response_data,
            status_code=200,
            details="Maintenance schedule completed"
            + (" and next occurrence created" if next_occurrence else ""),
        )
    except Exception as e:
        logger.error(f"Error completing maintenance schedule: {e}")
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
