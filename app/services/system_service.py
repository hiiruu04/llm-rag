from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import SystemCreate, SystemUpdate
from app.models.system import System


async def create_system(db: AsyncSession, data: SystemCreate) -> System:
    system = System(**data.model_dump())
    db.add(system)
    await db.commit()
    await db.refresh(system)
    return system


async def get_system(db: AsyncSession, system_id: UUID) -> Optional[System]:
    result = await db.execute(select(System).where(System.id == system_id))
    return result.scalar_one_or_none()


async def list_systems(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    name: Optional[str] = None,
) -> tuple[list[System], int]:
    query = select(System)
    count_query = select(func.count(System.id))

    if name:
        query = query.where(System.name.ilike(f"%{name}%"))
        count_query = count_query.where(System.name.ilike(f"%{name}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    systems = list(result.scalars().all())
    return systems, total


async def update_system(db: AsyncSession, system: System, data: SystemUpdate) -> System:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(system, field, value)
    await db.commit()
    await db.refresh(system)
    return system


async def delete_system(db: AsyncSession, system: System) -> None:
    await db.delete(system)
    await db.commit()
