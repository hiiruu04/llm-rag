from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.level import Level
from app.models.schemas import LevelCreate, LevelUpdate


async def create_level(db: AsyncSession, data: LevelCreate) -> Level:
    level = Level(**data.model_dump())
    db.add(level)
    await db.commit()
    result = await db.execute(
        select(Level).where(Level.id == level.id).options(selectinload(Level.role))
    )
    return result.scalar_one()


async def get_level(db: AsyncSession, level_id: UUID) -> Optional[Level]:
    result = await db.execute(
        select(Level)
        .where(Level.id == level_id)
        .options(selectinload(Level.role), selectinload(Level.competences))
    )
    return result.scalar_one_or_none()


async def list_levels(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    name: Optional[str] = None,
    role_id: Optional[UUID] = None,
) -> tuple[list[Level], int]:
    query = select(Level).options(selectinload(Level.role))
    count_query = select(func.count(Level.id))

    if name:
        query = query.where(Level.name.ilike(f"%{name}%"))
        count_query = count_query.where(Level.name.ilike(f"%{name}%"))

    if role_id:
        query = query.where(Level.role_id == role_id)
        count_query = count_query.where(Level.role_id == role_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Level.role_id, Level.rank).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    levels = list(result.scalars().all())
    return levels, total


async def update_level(db: AsyncSession, level: Level, data: LevelUpdate) -> Level:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(level, field, value)
    await db.commit()
    result = await db.execute(
        select(Level).where(Level.id == level.id).options(selectinload(Level.role))
    )
    return result.scalar_one()


async def delete_level(db: AsyncSession, level: Level) -> None:
    await db.delete(level)
    await db.commit()
