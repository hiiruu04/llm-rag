from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.schemas import AssetCreate, AssetUpdate


async def create_asset(db: AsyncSession, data: AssetCreate) -> Asset:
    asset = Asset(
        name=data.name,
        description=data.description,
        asset_type=data.asset_type,
        parent_id=data.parent_id,
        status=data.status,
        location=data.location,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def get_asset(db: AsyncSession, asset_id: UUID) -> Optional[Asset]:
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    return result.scalar_one_or_none()


async def list_assets(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    asset_type: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> tuple[list[Asset], int]:
    query = select(Asset)
    count_query = select(func.count(Asset.id))

    if status:
        query = query.where(Asset.status == status)
        count_query = count_query.where(Asset.status == status)
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
        count_query = count_query.where(Asset.asset_type == asset_type)
    if parent_id is not None:
        if parent_id == "null":
            query = query.where(Asset.parent_id.is_(None))
            count_query = count_query.where(Asset.parent_id.is_(None))
        else:
            query = query.where(Asset.parent_id == UUID(parent_id))
            count_query = count_query.where(Asset.parent_id == UUID(parent_id))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    assets = list(result.scalars().all())
    return assets, total


async def update_asset(db: AsyncSession, asset: Asset, data: AssetUpdate) -> Asset:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    await db.commit()
    await db.refresh(asset)
    return asset


async def delete_asset(db: AsyncSession, asset: Asset) -> None:
    await db.delete(asset)
    await db.commit()


async def get_children(
    db: AsyncSession, asset_id: UUID, page: int = 1, per_page: int = 10
) -> tuple[list[Asset], int]:
    count_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.parent_id == asset_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Asset)
        .where(Asset.parent_id == asset_id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    children = list(result.scalars().all())
    return children, total


async def get_asset_tree(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Asset).order_by(Asset.name))
    all_assets = list(result.scalars().all())

    asset_map = {}
    for asset in all_assets:
        asset_map[str(asset.id)] = {
            "id": str(asset.id),
            "name": asset.name,
            "asset_type": asset.asset_type,
            "status": asset.status,
            "children": [],
        }

    roots = []
    for asset in all_assets:
        node = asset_map[str(asset.id)]
        if asset.parent_id and str(asset.parent_id) in asset_map:
            asset_map[str(asset.parent_id)]["children"].append(node)
        else:
            roots.append(node)

    return roots


async def check_circular_parent(db: AsyncSession, asset_id: UUID, new_parent_id: UUID) -> bool:
    """Return True if setting new_parent_id would create a circular reference."""
    current_id = new_parent_id
    visited = set()
    while current_id is not None:
        if current_id == asset_id or current_id in visited:
            return True
        visited.add(current_id)
        result = await db.execute(select(Asset.parent_id).where(Asset.id == current_id))
        parent = result.scalar_one_or_none()
        if parent is None:
            break
        current_id = parent
    return False
