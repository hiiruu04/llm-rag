import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    BatchInsertResponse,
    DeletedCountResponse,
    SensorDataBatchCreate,
    SensorDataCreate,
    SensorDataResponse,
)
from app.services import sensor_data_service, sensor_service

router = APIRouter(prefix="/api/v1", tags=["sensor-data"])


@router.post("/sensors/{sensor_id}/data", status_code=201)
async def create_reading(
    sensor_id: UUID,
    data: SensorDataCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating reading for sensor {sensor_id}")

    sensor = await sensor_service.get_sensor(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Sensor not found",
                    "errors": [f"Sensor {sensor_id} does not exist"],
                },
            },
        )

    try:
        reading = await sensor_data_service.create_reading(db, sensor_id, data)
        return SuccessResponse.create(
            data=SensorDataResponse(**reading.to_dict()),
            status_code=201,
            details="Reading recorded successfully",
        )
    except Exception as e:
        logger.error(f"Error creating reading: {e}")
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


@router.post("/sensors/{sensor_id}/data/batch", status_code=201)
async def create_readings_batch(
    sensor_id: UUID,
    data: SensorDataBatchCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating batch readings for sensor {sensor_id}: {len(data.readings)} readings")

    sensor = await sensor_service.get_sensor(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Sensor not found",
                    "errors": [f"Sensor {sensor_id} does not exist"],
                },
            },
        )

    try:
        count = await sensor_data_service.create_readings_batch(db, sensor_id, data.readings)
        return SuccessResponse.create(
            data=BatchInsertResponse(count=count),
            status_code=201,
            details=f"{count} readings recorded successfully",
        )
    except Exception as e:
        logger.error(f"Error creating batch readings: {e}")
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


@router.get("/sensors/{sensor_id}/data")
async def list_readings(
    sensor_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=1000),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing readings for sensor {sensor_id}")

    sensor = await sensor_service.get_sensor(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Sensor not found",
                    "errors": [f"Sensor {sensor_id} does not exist"],
                },
            },
        )

    try:
        readings, total = await sensor_data_service.list_readings(
            db,
            sensor_id,
            page,
            per_page,
            start_time,
            end_time,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [SensorDataResponse(**r.to_dict()) for r in readings]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} readings",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing readings: {e}")
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


@router.get("/sensors/{sensor_id}/data/latest")
async def get_latest_reading(
    sensor_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Getting latest reading for sensor {sensor_id}")

    sensor = await sensor_service.get_sensor(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Sensor not found",
                    "errors": [f"Sensor {sensor_id} does not exist"],
                },
            },
        )

    reading = await sensor_data_service.get_latest_reading(db, sensor_id)
    if not reading:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "No readings found",
                    "errors": [f"No readings found for sensor {sensor_id}"],
                },
            },
        )

    return SuccessResponse.create(
        data=SensorDataResponse(**reading.to_dict()),
        status_code=200,
        details="Latest reading retrieved",
    )


@router.delete("/sensors/{sensor_id}/data")
async def delete_readings(
    sensor_id: UUID,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Deleting readings for sensor {sensor_id}")

    sensor = await sensor_service.get_sensor(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Sensor not found",
                    "errors": [f"Sensor {sensor_id} does not exist"],
                },
            },
        )

    try:
        count = await sensor_data_service.delete_readings_in_range(
            db,
            sensor_id,
            start_time,
            end_time,
        )
        return SuccessResponse.create(
            data=DeletedCountResponse(deleted_count=count),
            status_code=200,
            details=f"Deleted {count} readings",
        )
    except Exception as e:
        logger.error(f"Error deleting readings: {e}")
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
