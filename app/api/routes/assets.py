import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
)
from app.services import asset_service

router = APIRouter(prefix="/api/v1", tags=["assets"])


@router.post("/assets", status_code=201)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating asset: {data.name}")

    if data.parent_id:
        parent = await asset_service.get_asset(db, data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=400,
                detail={
                    "data": None,
                    "meta": {
                        "status_code": 400,
                        "details": "Invalid parent_id",
                        "errors": [f"Asset {data.parent_id} does not exist"],
                    },
                },
            )

    try:
        asset = await asset_service.create_asset(db, data)
        return SuccessResponse.create(
            data=AssetResponse(**asset.to_dict()),
            status_code=201,
            details="Asset created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating asset: {e}")
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


@router.get("/assets")
async def list_assets(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    asset_type: Optional[str] = None,
    parent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing assets (page={page}, per_page={per_page})")

    try:
        assets, total = await asset_service.list_assets(
            db,
            page=page,
            per_page=per_page,
            status=status,
            asset_type=asset_type,
            parent_id=parent_id,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [AssetResponse(**a.to_dict()) for a in assets]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} assets",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing assets: {e}")
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


@router.get("/assets/tree")
async def get_asset_tree(db: AsyncSession = Depends(get_db)):
    logger.info("Getting asset tree")

    try:
        tree = await asset_service.get_asset_tree(db)
        return SuccessResponse.create(
            data=tree,
            status_code=200,
            details="Asset tree retrieved",
        )
    except Exception as e:
        logger.error(f"Error getting asset tree: {e}")
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


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting asset {asset_id}")

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

    return SuccessResponse.create(
        data=AssetResponse(**asset.to_dict()),
        status_code=200,
        details="Asset retrieved",
    )


@router.put("/assets/{asset_id}")
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating asset {asset_id}")

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

    if data.parent_id is not None:
        if data.parent_id == asset_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "data": None,
                    "meta": {
                        "status_code": 400,
                        "details": "Self-referential parent",
                        "errors": ["Asset cannot be its own parent"],
                    },
                },
            )
        if await asset_service.check_circular_parent(db, asset_id, data.parent_id):
            raise HTTPException(
                status_code=400,
                detail={
                    "data": None,
                    "meta": {
                        "status_code": 400,
                        "details": "Circular parent reference",
                        "errors": ["Setting this parent_id would create a circular reference"],
                    },
                },
            )

    try:
        updated = await asset_service.update_asset(db, asset, data)
        return SuccessResponse.create(
            data=AssetResponse(**updated.to_dict()),
            status_code=200,
            details="Asset updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating asset: {e}")
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


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting asset {asset_id}")

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
        await asset_service.delete_asset(db, asset)
        return SuccessResponse.create(
            data={"id": str(asset_id)},
            status_code=200,
            details="Asset deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting asset: {e}")
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


@router.get("/assets/{asset_id}/children")
async def get_asset_children(
    asset_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Getting children of asset {asset_id}")

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
        children, total = await asset_service.get_children(db, asset_id, page, per_page)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [AssetResponse(**c.to_dict()) for c in children]

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
        logger.error(f"Error getting asset children: {e}")
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
