from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.schemas import LocationCreate, LocationUpdate


async def create_location(db: AsyncSession, data: LocationCreate) -> Location:
    location = Location(**data.model_dump())
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location


async def get_location(db: AsyncSession, location_id: UUID) -> Optional[Location]:
    result = await db.execute(select(Location).where(Location.id == location_id))
    return result.scalar_one_or_none()


async def list_locations(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    location_type: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> tuple[list[Location], int]:
    query = select(Location)
    count_query = select(func.count(Location.id))

    if location_type:
        query = query.where(Location.location_type == location_type)
        count_query = count_query.where(Location.location_type == location_type)
    if parent_id is not None:
        if parent_id == "null":
            query = query.where(Location.parent_id.is_(None))
            count_query = count_query.where(Location.parent_id.is_(None))
        else:
            query = query.where(Location.parent_id == UUID(parent_id))
            count_query = count_query.where(Location.parent_id == UUID(parent_id))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    locations = list(result.scalars().all())
    return locations, total


async def update_location(
    db: AsyncSession, location: Location, data: LocationUpdate
) -> Location:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    await db.commit()
    await db.refresh(location)
    return location


async def delete_location(db: AsyncSession, location: Location) -> None:
    await db.delete(location)
    await db.commit()


async def get_children(
    db: AsyncSession, location_id: UUID, page: int = 1, per_page: int = 10
) -> tuple[list[Location], int]:
    count_result = await db.execute(
        select(func.count(Location.id)).where(Location.parent_id == location_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Location)
        .where(Location.parent_id == location_id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    children = list(result.scalars().all())
    return children, total


async def get_location_tree(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Location).order_by(Location.name))
    all_locations = list(result.scalars().all())

    location_map = {}
    for location in all_locations:
        location_map[str(location.id)] = {
            "id": str(location.id),
            "name": location.name,
            "location_type": location.location_type,
            "description": location.description,
            "children": [],
        }

    roots = []
    for location in all_locations:
        node = location_map[str(location.id)]
        if location.parent_id and str(location.parent_id) in location_map:
            location_map[str(location.parent_id)]["children"].append(node)
        else:
            roots.append(node)

    return roots
