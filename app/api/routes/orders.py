import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
)
from app.services import order_service

router = APIRouter(prefix="/api/v1", tags=["orders"])


@router.post("/orders", status_code=201)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating order: {data.order_number}")

    try:
        order = await order_service.create_order(db, data)
        return SuccessResponse.create(
            data=OrderResponse(**order.to_dict()),
            status_code=201,
            details="Order created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.get("/orders")
async def list_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing orders (page={page}, per_page={per_page})")

    try:
        orders, total = await order_service.list_orders(
            db,
            page=page,
            per_page=per_page,
            status=status,
            order_type=order_type,
            priority=priority,
        )
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [OrderResponse(**o.to_dict()) for o in orders]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} orders",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing orders: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.get("/orders/{order_id}")
async def get_order(order_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting order {order_id}")

    order = await order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Order not found",
                    "errors": [f"Order {order_id} does not exist"],
                },
            },
        )

    return SuccessResponse.create(
        data=OrderResponse(**order.to_dict()),
        status_code=200,
        details="Order retrieved",
    )


@router.put("/orders/{order_id}")
async def update_order(
    order_id: UUID,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating order {order_id}")

    order = await order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Order not found",
                    "errors": [f"Order {order_id} does not exist"],
                },
            },
        )

    try:
        updated = await order_service.update_order(db, order, data)
        return SuccessResponse.create(
            data=OrderResponse(**updated.to_dict()),
            status_code=200,
            details="Order updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.delete("/orders/{order_id}")
async def delete_order(order_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting order {order_id}")

    order = await order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Order not found",
                    "errors": [f"Order {order_id} does not exist"],
                },
            },
        )

    try:
        await order_service.delete_order(db, order)
        return SuccessResponse.create(
            data={"id": str(order_id)},
            status_code=200,
            details="Order deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting order: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )
