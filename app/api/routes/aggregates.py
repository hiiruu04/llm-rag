import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    AggregateCreate,
    AggregateResponse,
    AggregateUpdate,
)
from app.services import aggregate_service

router = APIRouter(prefix="/api/v1", tags=["aggregates"])


@router.post("/aggregates", status_code=201)
async def create_aggregate(
    data: AggregateCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating aggregate: {data.name}")

    try:
        aggregate = await aggregate_service.create_aggregate(db, data)
        return SuccessResponse.create(
            data=AggregateResponse(**aggregate.to_dict()),
            status_code=201,
            details="Aggregate created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating aggregate: {e}")
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


@router.get("/aggregates")
async def list_aggregates(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing aggregates (page={page}, per_page={per_page})")

    try:
        aggregates, total = await aggregate_service.list_aggregates(
            db,
            page=page,
            per_page=per_page,
            name=name,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [AggregateResponse(**a.to_dict()) for a in aggregates]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} aggregates",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing aggregates: {e}")
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


@router.get("/aggregates/{aggregate_id}")
async def get_aggregate(
    aggregate_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Getting aggregate {aggregate_id}")

    aggregate = await aggregate_service.get_aggregate(db, aggregate_id)
    if not aggregate:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Aggregate not found",
                    "errors": [f"Aggregate {aggregate_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=AggregateResponse(**aggregate.to_dict()),
        status_code=200,
        details="Aggregate retrieved",
    )


@router.put("/aggregates/{aggregate_id}")
async def update_aggregate(
    aggregate_id: UUID,
    data: AggregateUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating aggregate {aggregate_id}")

    aggregate = await aggregate_service.get_aggregate(db, aggregate_id)
    if not aggregate:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Aggregate not found",
                    "errors": [f"Aggregate {aggregate_id} does not exist"],
                },
            },
        )

    try:
        updated = await aggregate_service.update_aggregate(db, aggregate, data)
        return SuccessResponse.create(
            data=AggregateResponse(**updated.to_dict()),
            status_code=200,
            details="Aggregate updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating aggregate: {e}")
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


@router.delete("/aggregates/{aggregate_id}")
async def delete_aggregate(
    aggregate_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Deleting aggregate {aggregate_id}")

    aggregate = await aggregate_service.get_aggregate(db, aggregate_id)
    if not aggregate:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Aggregate not found",
                    "errors": [f"Aggregate {aggregate_id} does not exist"],
                },
            },
        )

    try:
        await aggregate_service.delete_aggregate(db, aggregate)
        return SuccessResponse.create(
            data={"id": str(aggregate_id)},
            status_code=200,
            details="Aggregate deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting aggregate: {e}")
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
