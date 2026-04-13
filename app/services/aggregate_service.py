from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aggregate import Aggregate
from app.models.schemas import AggregateCreate, AggregateUpdate


async def create_aggregate(db: AsyncSession, data: AggregateCreate) -> Aggregate:
    aggregate = Aggregate(**data.model_dump())
    db.add(aggregate)
    await db.commit()
    await db.refresh(aggregate)
    return aggregate


async def get_aggregate(db: AsyncSession, aggregate_id: UUID) -> Optional[Aggregate]:
    result = await db.execute(select(Aggregate).where(Aggregate.id == aggregate_id))
    return result.scalar_one_or_none()


async def list_aggregates(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    name: Optional[str] = None,
) -> tuple[list[Aggregate], int]:
    query = select(Aggregate)
    count_query = select(func.count(Aggregate.id))

    if name:
        query = query.where(Aggregate.name.ilike(f"%{name}%"))
        count_query = count_query.where(Aggregate.name.ilike(f"%{name}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    aggregates = list(result.scalars().all())
    return aggregates, total


async def update_aggregate(
    db: AsyncSession, aggregate: Aggregate, data: AggregateUpdate
) -> Aggregate:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(aggregate, field, value)
    await db.commit()
    await db.refresh(aggregate)
    return aggregate


async def delete_aggregate(db: AsyncSession, aggregate: Aggregate) -> None:
    await db.delete(aggregate)
    await db.commit()
