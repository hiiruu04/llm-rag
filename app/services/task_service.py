from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.schemas import TaskCreate, TaskUpdate
from app.models.task import Task


async def create_task(db: AsyncSession, data: TaskCreate) -> Task:
    from app.models.graph_associations import task_worker
    from app.models.worker import Worker

    schedule = await db.get(MaintenanceSchedule, data.maintenance_schedule_id)
    if not schedule:
        raise ValueError(f"MaintenanceSchedule {data.maintenance_schedule_id} does not exist")

    create_data = data.model_dump(exclude={"worker_ids"})
    task = Task(**create_data)
    db.add(task)
    await db.flush()

    if data.worker_ids:
        for worker_id in data.worker_ids:
            worker = await db.get(Worker, worker_id)
            if worker:
                existing = await db.execute(
                    task_worker.select().where(
                        task_worker.c.task_id == task.id,
                        task_worker.c.worker_id == worker_id,
                    )
                )
                if not existing.first():
                    await db.execute(
                        task_worker.insert().values(task_id=task.id, worker_id=worker_id)
                    )
        if data.worker_ids:
            task.status = "assigned"

    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: UUID) -> Optional[Task]:
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Task).options(selectinload(Task.workers)).where(Task.id == task_id)
    )
    return result.scalar_one_or_none()


async def list_tasks(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    maintenance_schedule_id: Optional[str] = None,
) -> tuple[list[Task], int]:
    from sqlalchemy.orm import selectinload

    query = select(Task).options(selectinload(Task.workers))
    count_query = select(func.count(Task.id))

    if status:
        query = query.where(Task.status == status)
        count_query = count_query.where(Task.status == status)
    if task_type:
        query = query.where(Task.task_type == task_type)
        count_query = count_query.where(Task.task_type == task_type)
    if maintenance_schedule_id:
        query = query.where(Task.maintenance_schedule_id == UUID(maintenance_schedule_id))
        count_query = count_query.where(
            Task.maintenance_schedule_id == UUID(maintenance_schedule_id)
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    tasks = list(result.scalars().all())
    return tasks, total


async def update_task(db: AsyncSession, task: Task, data: TaskUpdate) -> Task:
    from app.models.graph_associations import task_worker
    from app.models.worker import Worker

    update_data = data.model_dump(exclude_unset=True, exclude={"worker_ids"})
    for field, value in update_data.items():
        setattr(task, field, value)

    if data.worker_ids is not None:
        await db.execute(task_worker.delete().where(task_worker.c.task_id == task.id))
        for worker_id in data.worker_ids:
            worker = await db.get(Worker, worker_id)
            if worker:
                await db.execute(task_worker.insert().values(task_id=task.id, worker_id=worker_id))

    await db.commit()
    await db.refresh(task, attribute_names=["workers"])
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.commit()
