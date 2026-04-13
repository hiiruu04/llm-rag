import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
)
from app.services import material_service

router = APIRouter(prefix="/api/v1", tags=["materials"])


@router.post("/materials", status_code=201)
async def create_material(
    data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating material: {data.name}")

    try:
        material = await material_service.create_material(db, data)
        return SuccessResponse.create(
            data=MaterialResponse(**material.to_dict()),
            status_code=201,
            details="Material created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating material: {e}")
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


@router.get("/materials")
async def list_materials(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    part_number: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing materials (page={page}, per_page={per_page})")

    try:
        materials, total = await material_service.list_materials(
            db,
            page=page,
            per_page=per_page,
            part_number=part_number,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [MaterialResponse(**m.to_dict()) for m in materials]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} materials",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing materials: {e}")
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


@router.get("/materials/{material_id}")
async def get_material(
    material_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Getting material {material_id}")

    material = await material_service.get_material(db, material_id)
    if not material:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Material not found",
                    "errors": [f"Material {material_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=MaterialResponse(**material.to_dict()),
        status_code=200,
        details="Material retrieved",
    )


@router.put("/materials/{material_id}")
async def update_material(
    material_id: UUID,
    data: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating material {material_id}")

    material = await material_service.get_material(db, material_id)
    if not material:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Material not found",
                    "errors": [f"Material {material_id} does not exist"],
                },
            },
        )

    try:
        updated = await material_service.update_material(db, material, data)
        return SuccessResponse.create(
            data=MaterialResponse(**updated.to_dict()),
            status_code=200,
            details="Material updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating material: {e}")
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


@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Deleting material {material_id}")

    material = await material_service.get_material(db, material_id)
    if not material:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Material not found",
                    "errors": [f"Material {material_id} does not exist"],
                },
            },
        )

    try:
        await material_service.delete_material(db, material)
        return SuccessResponse.create(
            data={"id": str(material_id)},
            status_code=200,
            details="Material deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting material: {e}")
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
