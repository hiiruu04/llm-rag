from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import WorkerCreate, WorkerUpdate
from app.models.worker import Worker


async def create_worker(db: AsyncSession, data: WorkerCreate) -> Worker:
    worker = Worker(**data.model_dump())
    db.add(worker)
    await db.commit()
    await db.refresh(worker)
    return worker


async def get_worker(db: AsyncSession, worker_id: UUID) -> Optional[Worker]:
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    return result.scalar_one_or_none()


async def list_workers(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    employee_id: Optional[str] = None,
) -> tuple[list[Worker], int]:
    query = select(Worker)
    count_query = select(func.count(Worker.id))

    if status:
        query = query.where(Worker.status == status)
        count_query = count_query.where(Worker.status == status)
    if employee_id:
        query = query.where(Worker.employee_id == employee_id)
        count_query = count_query.where(Worker.employee_id == employee_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    workers = list(result.scalars().all())
    return workers, total


async def update_worker(db: AsyncSession, worker: Worker, data: WorkerUpdate) -> Worker:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(worker, field, value)
    await db.commit()
    await db.refresh(worker)
    return worker


async def delete_worker(db: AsyncSession, worker: Worker) -> None:
    await db.delete(worker)
    await db.commit()
