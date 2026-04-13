from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.down_event import DownEvent
from app.models.schemas import DownEventCreate, DownEventUpdate


async def create_down_event(db: AsyncSession, data: DownEventCreate) -> DownEvent:
    down_event = DownEvent(**data.model_dump())
    db.add(down_event)
    await db.commit()
    await db.refresh(down_event)
    return down_event


async def get_down_event(db: AsyncSession, down_event_id: UUID) -> Optional[DownEvent]:
    result = await db.execute(select(DownEvent).where(DownEvent.id == down_event_id))
    return result.scalar_one_or_none()


async def list_down_events(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    asset_id: Optional[str] = None,
) -> tuple[list[DownEvent], int]:
    query = select(DownEvent)
    count_query = select(func.count(DownEvent.id))

    if severity:
        query = query.where(DownEvent.severity == severity)
        count_query = count_query.where(DownEvent.severity == severity)
    if status:
        query = query.where(DownEvent.status == status)
        count_query = count_query.where(DownEvent.status == status)
    if asset_id:
        query = query.where(DownEvent.asset_id == UUID(asset_id))
        count_query = count_query.where(DownEvent.asset_id == UUID(asset_id))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    down_events = list(result.scalars().all())
    return down_events, total


async def update_down_event(
    db: AsyncSession, down_event: DownEvent, data: DownEventUpdate
) -> DownEvent:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(down_event, field, value)
    await db.commit()
    await db.refresh(down_event)
    return down_event


async def delete_down_event(db: AsyncSession, down_event: DownEvent) -> None:
    await db.delete(down_event)
    await db.commit()
