from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.schemas import TaskCreate, TaskUpdate
from app.models.task import Task


async def create_task(db: AsyncSession, data: TaskCreate) -> Task:
    # Validate maintenance_schedule_id exists
    schedule = await db.get(MaintenanceSchedule, data.maintenance_schedule_id)
    if not schedule:
        raise ValueError(f"MaintenanceSchedule {data.maintenance_schedule_id} does not exist")

    task = Task(**data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: UUID) -> Optional[Task]:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def list_tasks(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    maintenance_schedule_id: Optional[str] = None,
) -> tuple[list[Task], int]:
    query = select(Task)
    count_query = select(func.count(Task.id))

    if status:
        query = query.where(Task.status == status)
        count_query = count_query.where(Task.status == status)
    if task_type:
        query = query.where(Task.task_type == task_type)
        count_query = count_query.where(Task.task_type == task_type)
    if maintenance_schedule_id:
        query = query.where(Task.maintenance_schedule_id == UUID(maintenance_schedule_id))
        count_query = count_query.where(Task.maintenance_schedule_id == UUID(maintenance_schedule_id))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    tasks = list(result.scalars().all())
    return tasks, total


async def update_task(db: AsyncSession, task: Task, data: TaskUpdate) -> Task:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.commit()
