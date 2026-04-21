from uuid import UUID

from loguru import logger
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.down_event import DownEvent
from app.models.order import Order
from app.models.task import Task


async def close_action(
    action_id: UUID | str,
    outcome: str,
    notes: str | None = None,
) -> dict:
    async with async_session_factory() as db:
        action_uuid = UUID(action_id) if isinstance(action_id, str) else action_id

        task_result = await db.execute(select(Task).where(Task.id == action_uuid))
        task = task_result.scalar_one_or_none()

        if task:
            task.status = "completed"
            if notes:
                existing = task.description or ""
                task.description = (
                    f"{existing}\n\n[CLOSED] {outcome}" if existing else f"[CLOSED] {outcome}"
                )
            await db.commit()
            await db.refresh(task)
            logger.info(f"Closed task {action_id} with outcome: {outcome}")
            return {
                "type": "task",
                "id": str(task.id),
                "name": task.name,
                "status": task.status,
                "outcome": outcome,
            }

        order_result = await db.execute(select(Order).where(Order.id == action_uuid))
        order = order_result.scalar_one_or_none()

        if order:
            order.status = "completed"
            if notes:
                existing = order.description or ""
                order.description = (
                    f"{existing}\n\n[CLOSED] {outcome}" if existing else f"[CLOSED] {outcome}"
                )
            await db.commit()
            await db.refresh(order)
            logger.info(f"Closed order {action_id} with outcome: {outcome}")
            return {
                "type": "order",
                "id": str(order.id),
                "order_number": order.order_number,
                "title": order.title,
                "status": order.status,
                "outcome": outcome,
            }

        logger.warning(f"Action {action_id} not found as task or order")
        return {
            "type": "not_found",
            "id": str(action_id),
            "error": "No task or order found with that ID",
        }


async def log_event(
    asset_id: UUID | str,
    fault_id: UUID | str,
    description: str,
    severity: str = "medium",
    started_at: str | None = None,
) -> dict:
    async with async_session_factory() as db:
        asset_uuid = UUID(asset_id) if isinstance(asset_id, str) else asset_id
        fault_uuid = UUID(fault_id) if isinstance(fault_id, str) else fault_id

        from datetime import datetime, timezone

        started = datetime.now(timezone.utc)
        if started_at:
            try:
                started = datetime.fromisoformat(started_at).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        event = DownEvent(
            asset_id=asset_uuid,
            fault_id=fault_uuid,
            severity=severity,
            started_at=started,
            status="active",
            downtime_minutes=0,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        logger.info(f"Logged down event {event.id} for asset {asset_id}")
        return {
            "type": "down_event",
            "id": str(event.id),
            "asset_id": str(asset_uuid),
            "fault_id": str(fault_uuid),
            "severity": event.severity,
            "status": event.status,
            "started_at": str(event.started_at),
        }


async def record_outcome(
    task_id: UUID | str,
    result: str,
    notes: str | None = None,
) -> dict:
    async with async_session_factory() as db:
        task_uuid = UUID(task_id) if isinstance(task_id, str) else task_id

        task_result = await db.execute(select(Task).where(Task.id == task_uuid))
        task = task_result.scalar_one_or_none()

        if not task:
            logger.warning(f"Task {task_id} not found for outcome recording")
            return {
                "type": "not_found",
                "id": str(task_uuid),
                "error": "No task found with that ID",
            }

        task.status = "completed"
        outcome_text = f"[OUTCOME] {result}"
        if notes:
            outcome_text += f"\n[NOTES] {notes}"
        existing = task.description or ""
        task.description = f"{existing}\n\n{outcome_text}" if existing else outcome_text

        await db.commit()
        await db.refresh(task)

        logger.info(f"Recorded outcome for task {task_id}: {result}")
        return {
            "type": "task",
            "id": str(task.id),
            "name": task.name,
            "status": task.status,
            "result": result,
            "notes": notes,
        }
