import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    LevelCreate,
    LevelResponse,
    LevelUpdate,
)
from app.services import level_service

router = APIRouter(prefix="/api/v1", tags=["levels"])


@router.post("/levels", status_code=201)
async def create_level(
    data: LevelCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating level: {data.name}")

    try:
        level = await level_service.create_level(db, data)
        return SuccessResponse.create(
            data=LevelResponse(**level.to_dict()),
            status_code=201,
            details="Level created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating level: {e}")
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


@router.get("/levels")
async def list_levels(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing levels (page={page}, per_page={per_page})")

    try:
        levels, total = await level_service.list_levels(
            db,
            page=page,
            per_page=per_page,
            name=name,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [LevelResponse(**level.to_dict()) for level in levels]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} levels",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing levels: {e}")
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


@router.get("/levels/{level_id}")
async def get_level(level_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting level {level_id}")

    level = await level_service.get_level(db, level_id)
    if not level:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Level not found",
                    "errors": [f"Level {level_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=LevelResponse(**level.to_dict()),
        status_code=200,
        details="Level retrieved",
    )


@router.put("/levels/{level_id}")
async def update_level(
    level_id: UUID,
    data: LevelUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating level {level_id}")

    level = await level_service.get_level(db, level_id)
    if not level:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Level not found",
                    "errors": [f"Level {level_id} does not exist"],
                },
            },
        )

    try:
        updated = await level_service.update_level(db, level, data)
        return SuccessResponse.create(
            data=LevelResponse(**updated.to_dict()),
            status_code=200,
            details="Level updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating level: {e}")
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


@router.delete("/levels/{level_id}")
async def delete_level(level_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting level {level_id}")

    level = await level_service.get_level(db, level_id)
    if not level:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Level not found",
                    "errors": [f"Level {level_id} does not exist"],
                },
            },
        )

    try:
        await level_service.delete_level(db, level)
        return SuccessResponse.create(
            data={"id": str(level_id)},
            status_code=200,
            details="Level deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting level: {e}")
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
