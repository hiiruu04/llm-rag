import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.services import role_service

router = APIRouter(prefix="/api/v1", tags=["roles"])


@router.post("/roles", status_code=201)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating role: {data.name}")

    try:
        role = await role_service.create_role(db, data)
        return SuccessResponse.create(
            data=RoleResponse(**role.to_dict()),
            status_code=201,
            details="Role created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating role: {e}")
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


@router.get("/roles")
async def list_roles(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing roles (page={page}, per_page={per_page})")

    try:
        roles, total = await role_service.list_roles(
            db,
            page=page,
            per_page=per_page,
            name=name,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [RoleResponse(**r.to_dict()) for r in roles]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} roles",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
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


@router.get("/roles/{role_id}")
async def get_role(role_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting role {role_id}")

    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Role not found",
                    "errors": [f"Role {role_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=RoleResponse(**role.to_dict()),
        status_code=200,
        details="Role retrieved",
    )


@router.put("/roles/{role_id}")
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating role {role_id}")

    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Role not found",
                    "errors": [f"Role {role_id} does not exist"],
                },
            },
        )

    try:
        updated = await role_service.update_role(db, role, data)
        return SuccessResponse.create(
            data=RoleResponse(**updated.to_dict()),
            status_code=200,
            details="Role updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating role: {e}")
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


@router.delete("/roles/{role_id}")
async def delete_role(role_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting role {role_id}")

    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Role not found",
                    "errors": [f"Role {role_id} does not exist"],
                },
            },
        )

    try:
        await role_service.delete_role(db, role)
        return SuccessResponse.create(
            data={"id": str(role_id)},
            status_code=200,
            details="Role deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
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
