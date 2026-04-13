import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    LocationCreate,
    LocationResponse,
    LocationUpdate,
)
from app.services import location_service

router = APIRouter(prefix="/api/v1", tags=["locations"])


@router.post("/locations", status_code=201)
async def create_location(
    data: LocationCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating location: {data.name}")

    try:
        location = await location_service.create_location(db, data)
        return SuccessResponse.create(
            data=LocationResponse(**location.to_dict()),
            status_code=201,
            details="Location created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating location: {e}")
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


@router.get("/locations/tree")
async def get_location_tree(db: AsyncSession = Depends(get_db)):
    logger.info("Getting location tree")

    try:
        tree = await location_service.get_location_tree(db)
        return SuccessResponse.create(
            data=tree,
            status_code=200,
            details="Location tree",
        )
    except Exception as e:
        logger.error(f"Error getting location tree: {e}")
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


@router.get("/locations")
async def list_locations(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    location_type: Optional[str] = None,
    parent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing locations (page={page}, per_page={per_page})")

    try:
        locations, total = await location_service.list_locations(
            db,
            page=page,
            per_page=per_page,
            location_type=location_type,
            parent_id=parent_id,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [LocationResponse(**loc.to_dict()) for loc in locations]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} locations",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing locations: {e}")
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


@router.get("/locations/{location_id}")
async def get_location(
    location_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Getting location {location_id}")

    location = await location_service.get_location(db, location_id)
    if not location:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Location not found",
                    "errors": [f"Location {location_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=LocationResponse(**location.to_dict()),
        status_code=200,
        details="Location retrieved",
    )


@router.put("/locations/{location_id}")
async def update_location(
    location_id: UUID,
    data: LocationUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating location {location_id}")

    location = await location_service.get_location(db, location_id)
    if not location:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Location not found",
                    "errors": [f"Location {location_id} does not exist"],
                },
            },
        )

    try:
        updated = await location_service.update_location(db, location, data)
        return SuccessResponse.create(
            data=LocationResponse(**updated.to_dict()),
            status_code=200,
            details="Location updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating location: {e}")
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


@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(f"Deleting location {location_id}")

    location = await location_service.get_location(db, location_id)
    if not location:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Location not found",
                    "errors": [f"Location {location_id} does not exist"],
                },
            },
        )

    try:
        await location_service.delete_location(db, location)
        return SuccessResponse.create(
            data={"id": str(location_id)},
            status_code=200,
            details="Location deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting location: {e}")
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


@router.get("/locations/{location_id}/children")
async def get_location_children(
    location_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Getting children of location {location_id}")

    location = await location_service.get_location(db, location_id)
    if not location:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Location not found",
                    "errors": [f"Location {location_id} does not exist"],
                },
            },
        )

    try:
        children, total = await location_service.get_children(
            db, location_id, page, per_page
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [LocationResponse(**c.to_dict()) for c in children]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} children",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error getting location children: {e}")
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
