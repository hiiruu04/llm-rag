from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import ShiftCreate, ShiftUpdate
from app.models.shift import Shift


async def create_shift(db: AsyncSession, data: ShiftCreate) -> Shift:
    shift = Shift(**data.model_dump())
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    return shift


async def get_shift(db: AsyncSession, shift_id: UUID) -> Optional[Shift]:
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    return result.scalar_one_or_none()


async def list_shifts(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    name: Optional[str] = None,
) -> tuple[list[Shift], int]:
    query = select(Shift)
    count_query = select(func.count(Shift.id))

    if name:
        query = query.where(Shift.name.ilike(f"%{name}%"))
        count_query = count_query.where(Shift.name.ilike(f"%{name}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    shifts = list(result.scalars().all())
    return shifts, total


async def update_shift(db: AsyncSession, shift: Shift, data: ShiftUpdate) -> Shift:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shift, field, value)
    await db.commit()
    await db.refresh(shift)
    return shift


async def delete_shift(db: AsyncSession, shift: Shift) -> None:
    await db.delete(shift)
    await db.commit()
