import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    CompetenceCreate,
    CompetenceResponse,
    CompetenceUpdate,
)
from app.services import competence_service

router = APIRouter(prefix="/api/v1", tags=["competences"])


@router.post("/competences", status_code=201)
async def create_competence(
    data: CompetenceCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating competence: {data.name}")

    try:
        competence = await competence_service.create_competence(db, data)
        return SuccessResponse.create(
            data=CompetenceResponse(**competence.to_dict()),
            status_code=201,
            details="Competence created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating competence: {e}")
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


@router.get("/competences")
async def list_competences(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing competences (page={page}, per_page={per_page})")

    try:
        competences, total = await competence_service.list_competences(
            db,
            page=page,
            per_page=per_page,
            category=category,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [CompetenceResponse(**c.to_dict()) for c in competences]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} competences",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing competences: {e}")
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


@router.get("/competences/{competence_id}")
async def get_competence(
    competence_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Getting competence {competence_id}")

    competence = await competence_service.get_competence(db, competence_id)
    if not competence:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Competence not found",
                    "errors": [f"Competence {competence_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=CompetenceResponse(**competence.to_dict()),
        status_code=200,
        details="Competence retrieved",
    )


@router.put("/competences/{competence_id}")
async def update_competence(
    competence_id: UUID,
    data: CompetenceUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating competence {competence_id}")

    competence = await competence_service.get_competence(db, competence_id)
    if not competence:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Competence not found",
                    "errors": [f"Competence {competence_id} does not exist"],
                },
            },
        )

    try:
        updated = await competence_service.update_competence(db, competence, data)
        return SuccessResponse.create(
            data=CompetenceResponse(**updated.to_dict()),
            status_code=200,
            details="Competence updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating competence: {e}")
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


@router.delete("/competences/{competence_id}")
async def delete_competence(
    competence_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Deleting competence {competence_id}")

    competence = await competence_service.get_competence(db, competence_id)
    if not competence:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Competence not found",
                    "errors": [f"Competence {competence_id} does not exist"],
                },
            },
        )

    try:
        await competence_service.delete_competence(db, competence)
        return SuccessResponse.create(
            data={"id": str(competence_id)},
            status_code=200,
            details="Competence deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting competence: {e}")
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
