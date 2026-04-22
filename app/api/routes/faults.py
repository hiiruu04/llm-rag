import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import FaultCreate, FaultLinkCreate, FaultResponse, FaultUpdate
from app.services import asset_service, fault_service

router = APIRouter(prefix="/api/v1", tags=["faults"])


@router.get("/faults")
async def list_all_faults(
    asset_id: UUID | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info("Listing all faults")

    try:
        faults, total = await fault_service.list_all_faults(
            db,
            asset_id=asset_id,
            severity=severity,
            status=status,
            page=page,
            per_page=per_page,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [FaultResponse(**f.to_dict()) for f in faults]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} faults",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing faults: {e}")
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


@router.post("/assets/{asset_id}/faults", status_code=201)
async def create_fault(
    asset_id: UUID,
    data: FaultCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating fault for asset {asset_id}: {data.code}")

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

    if data.resolved_at and data.status not in ("resolved", "closed"):
        raise HTTPException(
            status_code=400,
            detail={
                "data": None,
                "meta": {
                    "status_code": 400,
                    "details": "Invalid resolved_at",
                    "errors": [
                        "resolved_at can only be set when status is 'resolved' or 'closed'"
                    ],
                },
            },
        )

    try:
        fault = await fault_service.create_fault(db, asset_id, data)
        return SuccessResponse.create(
            data=FaultResponse(**fault.to_dict()),
            status_code=201,
            details="Fault created successfully",
        )
    except Exception as e:
        error_msg = str(e)
        if "unique constraint" in error_msg.lower() or "UniqueViolation" in error_msg:
            raise HTTPException(
                status_code=409,
                detail={
                    "data": None,
                    "meta": {
                        "status_code": 409,
                        "details": "Duplicate fault code",
                        "errors": [f"Fault code '{data.code}' already exists for this asset"],
                    },
                },
            )
        logger.error(f"Error creating fault: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [error_msg],
                },
            },
        )


@router.get("/assets/{asset_id}/faults")
async def list_faults(
    asset_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing faults for asset {asset_id}")

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
        faults, total = await fault_service.list_faults(db, asset_id, page, per_page)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [FaultResponse(**f.to_dict()) for f in faults]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} faults",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing faults: {e}")
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


@router.get("/faults/{fault_id}")
async def get_fault(fault_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting fault {fault_id}")

    fault = await fault_service.get_fault(db, fault_id)
    if not fault:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Fault not found",
                    "errors": [f"Fault {fault_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=FaultResponse(**fault.to_dict()),
        status_code=200,
        details="Fault retrieved",
    )


@router.put("/faults/{fault_id}")
async def update_fault(
    fault_id: UUID,
    data: FaultUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating fault {fault_id}")

    fault = await fault_service.get_fault(db, fault_id)
    if not fault:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Fault not found",
                    "errors": [f"Fault {fault_id} does not exist"],
                },
            },
        )

    new_status = data.status or fault.status
    new_resolved_at = data.resolved_at if data.resolved_at is not None else fault.resolved_at
    if new_resolved_at and new_status not in ("resolved", "closed"):
        raise HTTPException(
            status_code=400,
            detail={
                "data": None,
                "meta": {
                    "status_code": 400,
                    "details": "Invalid resolved_at",
                    "errors": [
                        "resolved_at can only be set when status is 'resolved' or 'closed'"
                    ],
                },
            },
        )

    try:
        updated = await fault_service.update_fault(db, fault, data)
        return SuccessResponse.create(
            data=FaultResponse(**updated.to_dict()),
            status_code=200,
            details="Fault updated successfully",
        )
    except Exception as e:
        error_msg = str(e)
        if "unique constraint" in error_msg.lower() or "UniqueViolation" in error_msg:
            raise HTTPException(
                status_code=409,
                detail={
                    "data": None,
                    "meta": {
                        "status_code": 409,
                        "details": "Duplicate fault code",
                        "errors": ["Fault code already exists for this asset"],
                    },
                },
            )
        logger.error(f"Error updating fault: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [error_msg],
                },
            },
        )


@router.delete("/faults/{fault_id}")
async def delete_fault(fault_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting fault {fault_id}")

    fault = await fault_service.get_fault(db, fault_id)
    if not fault:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Fault not found",
                    "errors": [f"Fault {fault_id} does not exist"],
                },
            },
        )

    try:
        await fault_service.delete_fault(db, fault)
        return SuccessResponse.create(
            data={"id": str(fault_id)},
            status_code=200,
            details="Fault deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting fault: {e}")
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


@router.post("/faults/{fault_id}/links")
async def add_fault_link(
    fault_id: UUID,
    data: FaultLinkCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Adding fault link: {fault_id} -> {data.linked_fault_id} ({data.link_type})")

    if fault_id == data.linked_fault_id:
        raise HTTPException(
            status_code=400,
            detail={
                "data": None,
                "meta": {
                    "status_code": 400,
                    "details": "Self-reference not allowed",
                    "errors": ["A fault cannot be linked to itself"],
                },
            },
        )

    fault = await fault_service.get_fault(db, fault_id)
    if not fault:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Fault not found",
                    "errors": [f"Fault {fault_id} does not exist"],
                },
            },
        )

    linked_fault = await fault_service.get_fault(db, data.linked_fault_id)
    if not linked_fault:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Linked fault not found",
                    "errors": [f"Fault {data.linked_fault_id} does not exist"],
                },
            },
        )

    try:
        await fault_service.add_fault_link(db, fault_id, data.linked_fault_id, data.link_type)
        return SuccessResponse.create(
            data={
                "fault_id": str(fault_id),
                "linked_fault_id": str(data.linked_fault_id),
                "link_type": data.link_type,
            },
            status_code=200,
            details="Fault link created successfully",
        )
    except Exception as e:
        logger.error(f"Error adding fault link: {e}")
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


@router.delete("/faults/{fault_id}/links/{linked_id}")
async def remove_fault_link(
    fault_id: UUID,
    linked_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Removing fault link: {fault_id} <-> {linked_id}")

    fault = await fault_service.get_fault(db, fault_id)
    if not fault:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Fault not found",
                    "errors": [f"Fault {fault_id} does not exist"],
                },
            },
        )

    try:
        await fault_service.remove_fault_link(db, fault_id, linked_id)
        return SuccessResponse.create(
            data={"fault_id": str(fault_id), "linked_fault_id": str(linked_id)},
            status_code=200,
            details="Fault link removed successfully",
        )
    except Exception as e:
        logger.error(f"Error removing fault link: {e}")
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


@router.get("/faults/{fault_id}/causes")
async def get_fault_causes(fault_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting causes for fault {fault_id}")

    fault = await fault_service.get_fault(db, fault_id)
    if not fault:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Fault not found",
                    "errors": [f"Fault {fault_id} does not exist"],
                },
            },
        )

    try:
        causes = await fault_service.get_causes(db, fault_id)
        data = [FaultResponse(**c.to_dict()) for c in causes]
        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} causes",
        )
    except Exception as e:
        logger.error(f"Error getting fault causes: {e}")
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


@router.get("/faults/{fault_id}/effects")
async def get_fault_effects(fault_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting effects for fault {fault_id}")

    fault = await fault_service.get_fault(db, fault_id)
    if not fault:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Fault not found",
                    "errors": [f"Fault {fault_id} does not exist"],
                },
            },
        )

    try:
        effects = await fault_service.get_effects(db, fault_id)
        data = [FaultResponse(**e.to_dict()) for e in effects]
        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} effects",
        )
    except Exception as e:
        logger.error(f"Error getting fault effects: {e}")
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
