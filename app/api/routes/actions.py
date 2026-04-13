import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    ActionCreate,
    ActionResponse,
    ActionUpdate,
)
from app.services import action_service

router = APIRouter(prefix="/api/v1", tags=["actions"])


@router.post("/actions", status_code=201)
async def create_action(
    data: ActionCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating action: {data.name}")

    try:
        action = await action_service.create_action(db, data)
        return SuccessResponse.create(
            data=ActionResponse(**action.to_dict()),
            status_code=201,
            details="Action created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating action: {e}")
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


@router.get("/actions")
async def list_actions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    action_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing actions (page={page}, per_page={per_page})")

    try:
        actions, total = await action_service.list_actions(
            db,
            page=page,
            per_page=per_page,
            action_type=action_type,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [ActionResponse(**a.to_dict()) for a in actions]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} actions",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing actions: {e}")
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


@router.get("/actions/{action_id}")
async def get_action(action_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting action {action_id}")

    action = await action_service.get_action(db, action_id)
    if not action:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Action not found",
                    "errors": [f"Action {action_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=ActionResponse(**action.to_dict()),
        status_code=200,
        details="Action retrieved",
    )


@router.put("/actions/{action_id}")
async def update_action(
    action_id: UUID,
    data: ActionUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating action {action_id}")

    action = await action_service.get_action(db, action_id)
    if not action:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Action not found",
                    "errors": [f"Action {action_id} does not exist"],
                },
            },
        )

    try:
        updated = await action_service.update_action(db, action, data)
        return SuccessResponse.create(
            data=ActionResponse(**updated.to_dict()),
            status_code=200,
            details="Action updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating action: {e}")
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


@router.delete("/actions/{action_id}")
async def delete_action(action_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting action {action_id}")

    action = await action_service.get_action(db, action_id)
    if not action:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Action not found",
                    "errors": [f"Action {action_id} does not exist"],
                },
            },
        )

    try:
        await action_service.delete_action(db, action)
        return SuccessResponse.create(
            data={"id": str(action_id)},
            status_code=200,
            details="Action deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting action: {e}")
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
