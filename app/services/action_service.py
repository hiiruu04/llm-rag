from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.models.schemas import ActionCreate, ActionUpdate


async def create_action(db: AsyncSession, data: ActionCreate) -> Action:
    action = Action(**data.model_dump())
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return action


async def get_action(db: AsyncSession, action_id: UUID) -> Optional[Action]:
    result = await db.execute(select(Action).where(Action.id == action_id))
    return result.scalar_one_or_none()


async def list_actions(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    action_type: Optional[str] = None,
) -> tuple[list[Action], int]:
    query = select(Action)
    count_query = select(func.count(Action.id))

    if action_type:
        query = query.where(Action.action_type == action_type)
        count_query = count_query.where(Action.action_type == action_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    actions = list(result.scalars().all())
    return actions, total


async def update_action(db: AsyncSession, action: Action, data: ActionUpdate) -> Action:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(action, field, value)
    await db.commit()
    await db.refresh(action)
    return action


async def delete_action(db: AsyncSession, action: Action) -> None:
    await db.delete(action)
    await db.commit()
