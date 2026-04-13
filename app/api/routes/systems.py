import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    SystemCreate,
    SystemResponse,
    SystemUpdate,
)
from app.services import system_service

router = APIRouter(prefix="/api/v1", tags=["systems"])


@router.post("/systems", status_code=201)
async def create_system(
    data: SystemCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating system: {data.name}")

    try:
        system = await system_service.create_system(db, data)
        return SuccessResponse.create(
            data=SystemResponse(**system.to_dict()),
            status_code=201,
            details="System created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating system: {e}")
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


@router.get("/systems")
async def list_systems(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing systems (page={page}, per_page={per_page})")

    try:
        systems, total = await system_service.list_systems(
            db,
            page=page,
            per_page=per_page,
            name=name,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [SystemResponse(**s.to_dict()) for s in systems]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} systems",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing systems: {e}")
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


@router.get("/systems/{system_id}")
async def get_system(system_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting system {system_id}")

    system = await system_service.get_system(db, system_id)
    if not system:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "System not found",
                    "errors": [f"System {system_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=SystemResponse(**system.to_dict()),
        status_code=200,
        details="System retrieved",
    )


@router.put("/systems/{system_id}")
async def update_system(
    system_id: UUID,
    data: SystemUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating system {system_id}")

    system = await system_service.get_system(db, system_id)
    if not system:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "System not found",
                    "errors": [f"System {system_id} does not exist"],
                },
            },
        )

    try:
        updated = await system_service.update_system(db, system, data)
        return SuccessResponse.create(
            data=SystemResponse(**updated.to_dict()),
            status_code=200,
            details="System updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating system: {e}")
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


@router.delete("/systems/{system_id}")
async def delete_system(system_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting system {system_id}")

    system = await system_service.get_system(db, system_id)
    if not system:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "System not found",
                    "errors": [f"System {system_id} does not exist"],
                },
            },
        )

    try:
        await system_service.delete_system(db, system)
        return SuccessResponse.create(
            data={"id": str(system_id)},
            status_code=200,
            details="System deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting system: {e}")
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
