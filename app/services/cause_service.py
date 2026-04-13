from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cause import Cause
from app.models.schemas import CauseCreate, CauseUpdate


async def create_cause(db: AsyncSession, data: CauseCreate) -> Cause:
    cause = Cause(**data.model_dump())
    db.add(cause)
    await db.commit()
    await db.refresh(cause)
    return cause


async def get_cause(db: AsyncSession, cause_id: UUID) -> Optional[Cause]:
    result = await db.execute(select(Cause).where(Cause.id == cause_id))
    return result.scalar_one_or_none()


async def list_causes(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    category: Optional[str] = None,
    severity: Optional[str] = None,
) -> tuple[list[Cause], int]:
    query = select(Cause)
    count_query = select(func.count(Cause.id))

    if category:
        query = query.where(Cause.category == category)
        count_query = count_query.where(Cause.category == category)
    if severity:
        query = query.where(Cause.severity == severity)
        count_query = count_query.where(Cause.severity == severity)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    causes = list(result.scalars().all())
    return causes, total


async def update_cause(db: AsyncSession, cause: Cause, data: CauseUpdate) -> Cause:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cause, field, value)
    await db.commit()
    await db.refresh(cause)
    return cause


async def delete_cause(db: AsyncSession, cause: Cause) -> None:
    await db.delete(cause)
    await db.commit()
