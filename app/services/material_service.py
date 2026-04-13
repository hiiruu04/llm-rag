from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material
from app.models.schemas import MaterialCreate, MaterialUpdate


async def create_material(db: AsyncSession, data: MaterialCreate) -> Material:
    material = Material(**data.model_dump())
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return material


async def get_material(db: AsyncSession, material_id: UUID) -> Optional[Material]:
    result = await db.execute(select(Material).where(Material.id == material_id))
    return result.scalar_one_or_none()


async def list_materials(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    part_number: Optional[str] = None,
) -> tuple[list[Material], int]:
    query = select(Material)
    count_query = select(func.count(Material.id))

    if part_number:
        query = query.where(Material.part_number.ilike(f"%{part_number}%"))
        count_query = count_query.where(Material.part_number.ilike(f"%{part_number}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    materials = list(result.scalars().all())
    return materials, total


async def update_material(
    db: AsyncSession, material: Material, data: MaterialUpdate
) -> Material:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    await db.commit()
    await db.refresh(material)
    return material


async def delete_material(db: AsyncSession, material: Material) -> None:
    await db.delete(material)
    await db.commit()
