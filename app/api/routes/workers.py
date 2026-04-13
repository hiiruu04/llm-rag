import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.competence import Competence
from app.models.graph_associations import worker_competence
from app.models.level import Level
from app.models.schemas import (
    WorkerCreate,
    WorkerResponse,
    WorkerUpdate,
)
from app.services import worker_service

router = APIRouter(prefix="/api/v1", tags=["workers"])


@router.post("/workers", status_code=201)
async def create_worker(
    data: WorkerCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating worker: {data.name}")

    try:
        worker = await worker_service.create_worker(db, data)
        return SuccessResponse.create(
            data=WorkerResponse(**worker.to_dict()),
            status_code=201,
            details="Worker created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating worker: {e}")
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


@router.get("/workers")
async def list_workers(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    employee_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing workers (page={page}, per_page={per_page})")

    try:
        workers, total = await worker_service.list_workers(
            db,
            page=page,
            per_page=per_page,
            status=status,
            employee_id=employee_id,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [WorkerResponse(**w.to_dict()) for w in workers]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} workers",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing workers: {e}")
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


@router.get("/workers/{worker_id}")
async def get_worker(worker_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting worker {worker_id}")

    worker = await worker_service.get_worker(db, worker_id)
    if not worker:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Worker not found",
                    "errors": [f"Worker {worker_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=WorkerResponse(**worker.to_dict()),
        status_code=200,
        details="Worker retrieved",
    )


@router.put("/workers/{worker_id}")
async def update_worker(
    worker_id: UUID,
    data: WorkerUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating worker {worker_id}")

    worker = await worker_service.get_worker(db, worker_id)
    if not worker:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Worker not found",
                    "errors": [f"Worker {worker_id} does not exist"],
                },
            },
        )

    try:
        updated = await worker_service.update_worker(db, worker, data)
        return SuccessResponse.create(
            data=WorkerResponse(**updated.to_dict()),
            status_code=200,
            details="Worker updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating worker: {e}")
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


@router.delete("/workers/{worker_id}")
async def delete_worker(worker_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting worker {worker_id}")

    worker = await worker_service.get_worker(db, worker_id)
    if not worker:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Worker not found",
                    "errors": [f"Worker {worker_id} does not exist"],
                },
            },
        )

    try:
        await worker_service.delete_worker(db, worker)
        return SuccessResponse.create(
            data={"id": str(worker_id)},
            status_code=200,
            details="Worker deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting worker: {e}")
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


@router.get("/workers/{worker_id}/competences")
async def get_worker_competences(
    worker_id: UUID, db: AsyncSession = Depends(get_db)
):
    worker = await worker_service.get_worker(db, worker_id)
    if not worker:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Worker not found",
                    "errors": [f"Worker {worker_id} does not exist"],
                },
            },
        )

    stmt = (
        select(Competence, Level)
        .join(worker_competence, worker_competence.c.competence_id == Competence.id)
        .outerjoin(Level, worker_competence.c.level_id == Level.id)
        .where(worker_competence.c.worker_id == worker_id)
    )
    result = await db.execute(stmt)
    rows = result.all()
    data = []
    for comp, level in rows:
        item = {
            "competence": comp.to_dict(),
            "level": level.to_dict() if level else None,
        }
        data.append(item)

    return SuccessResponse.create(
        data=data,
        status_code=200,
        details=f"Found {len(data)} competences",
    )
