import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import SensorCreate, SensorResponse, SensorUpdate
from app.services import asset_service, sensor_service

router = APIRouter(prefix="/api/v1", tags=["sensors"])


@router.post("/assets/{asset_id}/sensors", status_code=201)
async def create_sensor(
    asset_id: UUID,
    data: SensorCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating sensor for asset {asset_id}: {data.name}")

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
        sensor = await sensor_service.create_sensor(db, asset_id, data)
        return SuccessResponse.create(
            data=SensorResponse(**sensor.to_dict()),
            status_code=201,
            details="Sensor created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating sensor: {e}")
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


@router.get("/assets/{asset_id}/sensors")
async def list_sensors(
    asset_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing sensors for asset {asset_id}")

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
        sensors, total = await sensor_service.list_sensors(db, asset_id, page, per_page)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [SensorResponse(**s.to_dict()) for s in sensors]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} sensors",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing sensors: {e}")
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


@router.get("/sensors/{sensor_id}")
async def get_sensor(sensor_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting sensor {sensor_id}")

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

    return SuccessResponse.create(
        data=SensorResponse(**sensor.to_dict()),
        status_code=200,
        details="Sensor retrieved",
    )


@router.put("/sensors/{sensor_id}")
async def update_sensor(
    sensor_id: UUID,
    data: SensorUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating sensor {sensor_id}")

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
        updated = await sensor_service.update_sensor(db, sensor, data)
        return SuccessResponse.create(
            data=SensorResponse(**updated.to_dict()),
            status_code=200,
            details="Sensor updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating sensor: {e}")
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


@router.delete("/sensors/{sensor_id}")
async def delete_sensor(sensor_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting sensor {sensor_id}")

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
        await sensor_service.delete_sensor(db, sensor)
        return SuccessResponse.create(
            data={"id": str(sensor_id)},
            status_code=200,
            details="Sensor deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting sensor: {e}")
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
