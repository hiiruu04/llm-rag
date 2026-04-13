import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    CauseCreate,
    CauseResponse,
    CauseUpdate,
)
from app.services import cause_service

router = APIRouter(prefix="/api/v1", tags=["causes"])


@router.post("/causes", status_code=201)
async def create_cause(
    data: CauseCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating cause: {data.name}")

    try:
        cause = await cause_service.create_cause(db, data)
        return SuccessResponse.create(
            data=CauseResponse(**cause.to_dict()),
            status_code=201,
            details="Cause created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating cause: {e}")
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


@router.get("/causes")
async def list_causes(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing causes (page={page}, per_page={per_page})")

    try:
        causes, total = await cause_service.list_causes(
            db,
            page=page,
            per_page=per_page,
            category=category,
            severity=severity,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [CauseResponse(**c.to_dict()) for c in causes]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} causes",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing causes: {e}")
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


@router.get("/causes/{cause_id}")
async def get_cause(cause_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting cause {cause_id}")

    cause = await cause_service.get_cause(db, cause_id)
    if not cause:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Cause not found",
                    "errors": [f"Cause {cause_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=CauseResponse(**cause.to_dict()),
        status_code=200,
        details="Cause retrieved",
    )


@router.put("/causes/{cause_id}")
async def update_cause(
    cause_id: UUID,
    data: CauseUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating cause {cause_id}")

    cause = await cause_service.get_cause(db, cause_id)
    if not cause:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Cause not found",
                    "errors": [f"Cause {cause_id} does not exist"],
                },
            },
        )

    try:
        updated = await cause_service.update_cause(db, cause, data)
        return SuccessResponse.create(
            data=CauseResponse(**updated.to_dict()),
            status_code=200,
            details="Cause updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating cause: {e}")
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


@router.delete("/causes/{cause_id}")
async def delete_cause(cause_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting cause {cause_id}")

    cause = await cause_service.get_cause(db, cause_id)
    if not cause:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Cause not found",
                    "errors": [f"Cause {cause_id} does not exist"],
                },
            },
        )

    try:
        await cause_service.delete_cause(db, cause)
        return SuccessResponse.create(
            data={"id": str(cause_id)},
            status_code=200,
            details="Cause deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting cause: {e}")
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
