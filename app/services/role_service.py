from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.schemas import RoleCreate, RoleUpdate


async def create_role(db: AsyncSession, data: RoleCreate) -> Role:
    role = Role(**data.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def get_role(db: AsyncSession, role_id: UUID) -> Optional[Role]:
    result = await db.execute(select(Role).where(Role.id == role_id))
    return result.scalar_one_or_none()


async def list_roles(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    name: Optional[str] = None,
) -> tuple[list[Role], int]:
    query = select(Role)
    count_query = select(func.count(Role.id))

    if name:
        query = query.where(Role.name.ilike(f"%{name}%"))
        count_query = count_query.where(Role.name.ilike(f"%{name}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    roles = list(result.scalars().all())
    return roles, total


async def update_role(db: AsyncSession, role: Role, data: RoleUpdate) -> Role:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(db: AsyncSession, role: Role) -> None:
    await db.delete(role)
    await db.commit()
