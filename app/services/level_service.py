from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.level import Level
from app.models.schemas import LevelCreate, LevelUpdate


async def create_level(db: AsyncSession, data: LevelCreate) -> Level:
    level = Level(**data.model_dump())
    db.add(level)
    await db.commit()
    await db.refresh(level)
    return level


async def get_level(db: AsyncSession, level_id: UUID) -> Optional[Level]:
    result = await db.execute(select(Level).where(Level.id == level_id))
    return result.scalar_one_or_none()


async def list_levels(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    name: Optional[str] = None,
) -> tuple[list[Level], int]:
    query = select(Level)
    count_query = select(func.count(Level.id))

    if name:
        query = query.where(Level.name.ilike(f"%{name}%"))
        count_query = count_query.where(Level.name.ilike(f"%{name}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    levels = list(result.scalars().all())
    return levels, total


async def update_level(db: AsyncSession, level: Level, data: LevelUpdate) -> Level:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(level, field, value)
    await db.commit()
    await db.refresh(level)
    return level


async def delete_level(db: AsyncSession, level: Level) -> None:
    await db.delete(level)
    await db.commit()
