import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    ShiftCreate,
    ShiftResponse,
    ShiftUpdate,
)
from app.services import shift_service

router = APIRouter(prefix="/api/v1", tags=["shifts"])


@router.post("/shifts", status_code=201)
async def create_shift(
    data: ShiftCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating shift: {data.name}")

    try:
        shift = await shift_service.create_shift(db, data)
        return SuccessResponse.create(
            data=ShiftResponse(**shift.to_dict()),
            status_code=201,
            details="Shift created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating shift: {e}")
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


@router.get("/shifts")
async def list_shifts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing shifts (page={page}, per_page={per_page})")

    try:
        shifts, total = await shift_service.list_shifts(
            db,
            page=page,
            per_page=per_page,
            name=name,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [ShiftResponse(**s.to_dict()) for s in shifts]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} shifts",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing shifts: {e}")
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


@router.get("/shifts/{shift_id}")
async def get_shift(shift_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting shift {shift_id}")

    shift = await shift_service.get_shift(db, shift_id)
    if not shift:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Shift not found",
                    "errors": [f"Shift {shift_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=ShiftResponse(**shift.to_dict()),
        status_code=200,
        details="Shift retrieved",
    )


@router.put("/shifts/{shift_id}")
async def update_shift(
    shift_id: UUID,
    data: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating shift {shift_id}")

    shift = await shift_service.get_shift(db, shift_id)
    if not shift:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Shift not found",
                    "errors": [f"Shift {shift_id} does not exist"],
                },
            },
        )

    try:
        updated = await shift_service.update_shift(db, shift, data)
        return SuccessResponse.create(
            data=ShiftResponse(**updated.to_dict()),
            status_code=200,
            details="Shift updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating shift: {e}")
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


@router.delete("/shifts/{shift_id}")
async def delete_shift(shift_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting shift {shift_id}")

    shift = await shift_service.get_shift(db, shift_id)
    if not shift:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Shift not found",
                    "errors": [f"Shift {shift_id} does not exist"],
                },
            },
        )

    try:
        await shift_service.delete_shift(db, shift)
        return SuccessResponse.create(
            data={"id": str(shift_id)},
            status_code=200,
            details="Shift deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting shift: {e}")
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
