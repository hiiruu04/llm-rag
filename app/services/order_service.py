from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.schemas import OrderCreate, OrderUpdate


async def create_order(db: AsyncSession, data: OrderCreate) -> Order:
    order = Order(**data.model_dump())
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def get_order(db: AsyncSession, order_id: UUID) -> Optional[Order]:
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    priority: Optional[str] = None,
) -> tuple[list[Order], int]:
    query = select(Order)
    count_query = select(func.count(Order.id))

    if status:
        query = query.where(Order.status == status)
        count_query = count_query.where(Order.status == status)
    if order_type:
        query = query.where(Order.order_type == order_type)
        count_query = count_query.where(Order.order_type == order_type)
    if priority:
        query = query.where(Order.priority == priority)
        count_query = count_query.where(Order.priority == priority)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    orders = list(result.scalars().all())
    return orders, total


async def update_order(db: AsyncSession, order: Order, data: OrderUpdate) -> Order:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    await db.commit()
    await db.refresh(order)
    return order


async def delete_order(db: AsyncSession, order: Order) -> None:
    await db.delete(order)
    await db.commit()
