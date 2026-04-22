import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.graph_associations import task_competence, task_material
from app.models.schemas import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services import task_service
from sqlalchemy.orm import selectinload
from sqlalchemy import select

router = APIRouter(prefix="/api/v1", tags=["tasks"])


class TaskCompetenceAdd(BaseModel):
    competence_id: UUID
    level_id: Optional[UUID] = None


class TaskMaterialAdd(BaseModel):
    material_id: UUID
    quantity_required: Optional[float] = None


@router.post("/tasks", status_code=201)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating task: {data.name}")

    try:
        task = await task_service.create_task(db, data)
        return SuccessResponse.create(
            data=TaskResponse(**task.to_dict()),
            status_code=201,
            details="Task created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
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


@router.get("/tasks")
async def list_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    maintenance_schedule_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing tasks (page={page}, per_page={per_page})")

    try:
        tasks, total = await task_service.list_tasks(
            db,
            page=page,
            per_page=per_page,
            status=status,
            task_type=task_type,
            maintenance_schedule_id=maintenance_schedule_id,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [TaskResponse(**t.to_dict()) for t in tasks]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} tasks",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
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


@router.get("/tasks/{task_id}")
async def get_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting task {task_id}")

    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Task not found",
                    "errors": [f"Task {task_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=TaskResponse(**task.to_dict()),
        status_code=200,
        details="Task retrieved",
    )


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating task {task_id}")

    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Task not found",
                    "errors": [f"Task {task_id} does not exist"],
                },
            },
        )

    try:
        updated = await task_service.update_task(db, task, data)
        return SuccessResponse.create(
            data=TaskResponse(**updated.to_dict()),
            status_code=200,
            details="Task updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating task: {e}")
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


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting task {task_id}")

    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Task not found",
                    "errors": [f"Task {task_id} does not exist"],
                },
            },
        )

    try:
        await task_service.delete_task(db, task)
        return SuccessResponse.create(
            data={"id": str(task_id)},
            status_code=200,
            details="Task deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
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


@router.post("/tasks/{task_id}/competences", status_code=201)
async def add_task_competence(
    task_id: UUID,
    body: TaskCompetenceAdd,
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Task not found",
                    "errors": [f"Task {task_id} does not exist"],
                },
            },
        )

    try:
        await db.execute(
            task_competence.insert().values(
                task_id=task_id,
                competence_id=body.competence_id,
                level_id=body.level_id,
            )
        )
        await db.commit()
        return SuccessResponse.create(
            data={
                "task_id": str(task_id),
                "competence_id": str(body.competence_id),
            },
            status_code=201,
            details="Competence added to task",
        )
    except Exception as e:
        logger.error(f"Error adding competence to task: {e}")
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


@router.post("/tasks/{task_id}/materials", status_code=201)
async def add_task_material(
    task_id: UUID,
    body: TaskMaterialAdd,
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Task not found",
                    "errors": [f"Task {task_id} does not exist"],
                },
            },
        )

    try:
        await db.execute(
            task_material.insert().values(
                task_id=task_id,
                material_id=body.material_id,
                quantity_required=body.quantity_required,
            )
        )
        await db.commit()
        return SuccessResponse.create(
            data={
                "task_id": str(task_id),
                "material_id": str(body.material_id),
            },
            status_code=201,
            details="Material added to task",
        )
    except Exception as e:
        logger.error(f"Error adding material to task: {e}")
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
