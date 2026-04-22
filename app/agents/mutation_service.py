from uuid import UUID

from loguru import logger
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.asset import Asset
from app.models.down_event import DownEvent
from app.models.fault import Fault
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.order import Order
from app.models.task import Task
from app.models.worker import Worker


async def _trigger_graph_sync():
    try:
        from app.services.graph_sync_service import get_graph_sync_service

        sync_service = get_graph_sync_service()
        result = await sync_service.incremental_sync()
        logger.info(f"Auto graph sync triggered: {result.get('status', 'unknown')}")
    except Exception as e:
        logger.warning(f"Auto graph sync failed (non-fatal): {e}")


async def create_maintenance_plan(
    asset_id: UUID | str,
    title: str,
    maintenance_type: str = "preventive",
    description: str | None = None,
    priority: str = "medium",
    scheduled_date: str | None = None,
    recurrence: str = "none",
    estimated_duration_hours: float | None = None,
    notes: str | None = None,
) -> dict:
    from datetime import datetime, timezone

    async with async_session_factory() as db:
        asset_uuid = UUID(asset_id) if isinstance(asset_id, str) else asset_id

        asset_result = await db.execute(select(Asset).where(Asset.id == asset_uuid))
        asset = asset_result.scalar_one_or_none()
        if not asset:
            return {
                "type": "not_found",
                "id": str(asset_uuid),
                "error": "No asset found with that ID",
            }

        valid_types = {"preventive", "corrective", "predictive"}
        if maintenance_type not in valid_types:
            return {
                "type": "error",
                "error": (
                    f"Invalid maintenance_type '{maintenance_type}'. "
                    f"Valid: {', '.join(sorted(valid_types))}"
                ),
            }

        valid_priorities = {"low", "medium", "high", "critical"}
        if priority not in valid_priorities:
            return {
                "type": "error",
                "error": (
                    f"Invalid priority '{priority}'. Valid: {', '.join(sorted(valid_priorities))}"
                ),
            }

        valid_recurrences = {"none", "daily", "weekly", "monthly", "quarterly", "yearly"}
        if recurrence not in valid_recurrences:
            return {
                "type": "error",
                "error": (
                    f"Invalid recurrence '{recurrence}'. "
                    f"Valid: {', '.join(sorted(valid_recurrences))}"
                ),
            }

        parsed_date = datetime.now(timezone.utc)
        if scheduled_date:
            try:
                parsed_date = datetime.fromisoformat(scheduled_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return {
                    "type": "error",
                    "error": (
                        f"Invalid scheduled_date format: '{scheduled_date}'. Use ISO 8601 format."
                    ),
                }

        schedule = MaintenanceSchedule(
            asset_id=asset_uuid,
            title=title,
            description=description,
            maintenance_type=maintenance_type,
            priority=priority,
            scheduled_date=parsed_date,
            recurrence=recurrence,
            estimated_duration_hours=estimated_duration_hours,
            notes=notes,
        )
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)

        logger.info(f"Created maintenance plan '{title}' for asset {asset_id}")
        await _trigger_graph_sync()
        return {
            "type": "maintenance_plan",
            "id": str(schedule.id),
            "asset_id": str(asset_uuid),
            "title": schedule.title,
            "maintenance_type": schedule.maintenance_type,
            "priority": schedule.priority,
            "scheduled_date": str(schedule.scheduled_date),
            "recurrence": schedule.recurrence,
            "status": schedule.status,
        }


async def create_task(
    name: str,
    maintenance_schedule_id: UUID | str,
    task_type: str = "general",
    description: str | None = None,
    shift_id: UUID | str | None = None,
    worker_ids: list[str] | None = None,
    estimated_duration_hours: float | None = None,
    action_type: str = "standard",
    sequence_order: int = 0,
) -> dict:
    from app.models.graph_associations import task_worker

    async with async_session_factory() as db:
        schedule_uuid = (
            UUID(maintenance_schedule_id)
            if isinstance(maintenance_schedule_id, str)
            else maintenance_schedule_id
        )

        schedule_result = await db.execute(
            select(MaintenanceSchedule).where(MaintenanceSchedule.id == schedule_uuid)
        )
        schedule = schedule_result.scalar_one_or_none()
        if not schedule:
            return {
                "type": "not_found",
                "id": str(schedule_uuid),
                "error": "No maintenance schedule found with that ID",
            }

        valid_types = {"general", "inspection", "repair", "installation", "calibration"}
        if task_type not in valid_types:
            return {
                "type": "error",
                "error": (
                    f"Invalid task_type '{task_type}'. Valid: {', '.join(sorted(valid_types))}"
                ),
            }

        shift_uuid = None
        if shift_id:
            from app.models.shift import Shift

            shift_uuid = UUID(shift_id) if isinstance(shift_id, str) else shift_id
            shift_result = await db.execute(select(Shift).where(Shift.id == shift_uuid))
            shift = shift_result.scalar_one_or_none()
            if not shift:
                return {
                    "type": "not_found",
                    "id": str(shift_uuid),
                    "error": "No shift found with that ID",
                }

        task = Task(
            name=name,
            description=description,
            task_type=task_type,
            status="pending",
            maintenance_schedule_id=schedule_uuid,
            shift_id=shift_uuid,
            estimated_duration_hours=estimated_duration_hours,
            action_type=action_type,
            sequence_order=sequence_order,
        )
        db.add(task)
        await db.flush()

        assigned_worker_names = []
        if worker_ids:
            for wid in worker_ids:
                try:
                    worker_uuid = UUID(wid)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid worker UUID: {wid}")
                    continue

                worker_result = await db.execute(select(Worker).where(Worker.id == worker_uuid))
                worker = worker_result.scalar_one_or_none()
                if worker:
                    existing = await db.execute(
                        select(task_worker).where(
                            task_worker.c.task_id == task.id,
                            task_worker.c.worker_id == worker_uuid,
                        )
                    )
                    if not existing.first():
                        await db.execute(
                            task_worker.insert().values(task_id=task.id, worker_id=worker_uuid)
                        )
                        assigned_worker_names.append(worker.name)

            if assigned_worker_names:
                task.status = "assigned"

        await db.commit()
        await db.refresh(task)

        logger.info(f"Created task '{name}' under schedule {schedule_uuid}")
        await _trigger_graph_sync()
        return {
            "type": "task",
            "id": str(task.id),
            "name": task.name,
            "task_type": task.task_type,
            "status": task.status,
            "maintenance_schedule_id": str(schedule_uuid),
            "shift_id": str(shift_uuid) if shift_uuid else None,
            "assigned_workers": assigned_worker_names,
            "action_type": task.action_type,
            "sequence_order": task.sequence_order,
        }


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
            await _trigger_graph_sync()
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
            await _trigger_graph_sync()
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
        await _trigger_graph_sync()
        return {
            "type": "task",
            "id": str(task.id),
            "name": task.name,
            "status": task.status,
            "result": result,
            "notes": notes,
        }


# --- SchedulingAgent mutations ---


async def assign_task(
    task_id: UUID | str,
    worker_id: UUID | str,
) -> dict:
    from app.models.graph_associations import task_worker

    async with async_session_factory() as db:
        task_uuid = UUID(task_id) if isinstance(task_id, str) else task_id
        worker_uuid = UUID(worker_id) if isinstance(worker_id, str) else worker_id

        task_result = await db.execute(select(Task).where(Task.id == task_uuid))
        task = task_result.scalar_one_or_none()
        if not task:
            logger.warning(f"Task {task_id} not found for assignment")
            return {
                "type": "not_found",
                "id": str(task_uuid),
                "error": "No task found with that ID",
            }

        worker_result = await db.execute(select(Worker).where(Worker.id == worker_uuid))
        worker = worker_result.scalar_one_or_none()
        if not worker:
            logger.warning(f"Worker {worker_id} not found for assignment")
            return {
                "type": "not_found",
                "id": str(worker_uuid),
                "error": "No worker found with that ID",
            }

        existing = await db.execute(
            select(task_worker).where(
                task_worker.c.task_id == task_uuid,
                task_worker.c.worker_id == worker_uuid,
            )
        )
        if not existing.first():
            await db.execute(task_worker.insert().values(task_id=task_uuid, worker_id=worker_uuid))

        if task.status == "pending":
            task.status = "assigned"

        await db.commit()
        await db.refresh(task)

        logger.info(f"Assigned task {task_id} to worker {worker_id}")
        await _trigger_graph_sync()
        return {
            "type": "task_assignment",
            "task_id": str(task.id),
            "task_name": task.name,
            "worker_id": str(worker.id),
            "worker_name": worker.name,
            "status": task.status,
        }


async def update_task_status(
    task_id: UUID | str,
    status: str,
) -> dict:
    async with async_session_factory() as db:
        task_uuid = UUID(task_id) if isinstance(task_id, str) else task_id

        valid_statuses = {
            "pending",
            "assigned",
            "in_progress",
            "completed",
            "cancelled",
            "on_hold",
        }
        if status not in valid_statuses:
            return {
                "type": "error",
                "id": str(task_uuid),
                "error": f"Invalid status '{status}'. Valid: {', '.join(sorted(valid_statuses))}",
            }

        task_result = await db.execute(select(Task).where(Task.id == task_uuid))
        task = task_result.scalar_one_or_none()
        if not task:
            logger.warning(f"Task {task_id} not found for status update")
            return {
                "type": "not_found",
                "id": str(task_uuid),
                "error": "No task found with that ID",
            }

        old_status = task.status
        task.status = status

        await db.commit()
        await db.refresh(task)

        logger.info(f"Updated task {task_id} status: {old_status} -> {status}")
        await _trigger_graph_sync()
        return {
            "type": "task_status_update",
            "task_id": str(task.id),
            "task_name": task.name,
            "old_status": old_status,
            "new_status": task.status,
        }


async def reschedule_task(
    task_id: UUID | str,
    shift_id: UUID | str,
) -> dict:
    from app.models.shift import Shift

    async with async_session_factory() as db:
        task_uuid = UUID(task_id) if isinstance(task_id, str) else task_id
        shift_uuid = UUID(shift_id) if isinstance(shift_id, str) else shift_id

        task_result = await db.execute(select(Task).where(Task.id == task_uuid))
        task = task_result.scalar_one_or_none()
        if not task:
            logger.warning(f"Task {task_id} not found for rescheduling")
            return {
                "type": "not_found",
                "id": str(task_uuid),
                "error": "No task found with that ID",
            }

        shift_result = await db.execute(select(Shift).where(Shift.id == shift_uuid))
        shift = shift_result.scalar_one_or_none()
        if not shift:
            logger.warning(f"Shift {shift_id} not found for rescheduling")
            return {
                "type": "not_found",
                "id": str(shift_uuid),
                "error": "No shift found with that ID",
            }

        old_shift_id = str(task.shift_id) if task.shift_id else None
        task.shift_id = shift_uuid

        await db.commit()
        await db.refresh(task)

        logger.info(f"Rescheduled task {task_id} to shift {shift_id}")
        await _trigger_graph_sync()
        return {
            "type": "task_reschedule",
            "task_id": str(task.id),
            "task_name": task.name,
            "old_shift_id": old_shift_id,
            "new_shift_id": str(shift_uuid),
            "shift_name": shift.name,
        }


# --- AnalyzerAgent mutations ---


async def log_down_event(
    asset_id: UUID | str,
    fault_id: UUID | str,
    description: str = "",
    severity: str = "medium",
) -> dict:
    async with async_session_factory() as db:
        asset_uuid = UUID(asset_id) if isinstance(asset_id, str) else asset_id
        fault_uuid = UUID(fault_id) if isinstance(fault_id, str) else fault_id

        from datetime import datetime, timezone

        event = DownEvent(
            asset_id=asset_uuid,
            fault_id=fault_uuid,
            severity=severity,
            started_at=datetime.now(timezone.utc),
            status="active",
            downtime_minutes=0,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        logger.info(f"Logged down event {event.id} for asset {asset_id}")
        await _trigger_graph_sync()
        return {
            "type": "down_event",
            "id": str(event.id),
            "asset_id": str(asset_uuid),
            "fault_id": str(fault_uuid),
            "severity": event.severity,
            "status": event.status,
            "started_at": str(event.started_at),
        }


async def close_down_event(
    down_event_id: UUID | str,
    resolution: str,
) -> dict:
    async with async_session_factory() as db:
        event_uuid = UUID(down_event_id) if isinstance(down_event_id, str) else down_event_id

        event_result = await db.execute(select(DownEvent).where(DownEvent.id == event_uuid))
        event = event_result.scalar_one_or_none()

        if not event:
            logger.warning(f"Down event {down_event_id} not found")
            return {
                "type": "not_found",
                "id": str(event_uuid),
                "error": "No down event found with that ID",
            }

        from datetime import datetime, timezone

        event.status = "resolved"
        event.ended_at = datetime.now(timezone.utc)
        if event.started_at:
            delta = datetime.now(timezone.utc) - event.started_at
            event.downtime_minutes = int(delta.total_seconds() / 60)

        await db.commit()
        await db.refresh(event)

        logger.info(f"Closed down event {down_event_id} with resolution: {resolution}")
        await _trigger_graph_sync()
        return {
            "type": "down_event_close",
            "id": str(event.id),
            "status": event.status,
            "resolution": resolution,
            "downtime_minutes": event.downtime_minutes,
            "ended_at": str(event.ended_at) if event.ended_at else None,
        }


async def update_fault_severity(
    fault_id: UUID | str,
    severity: str,
) -> dict:
    async with async_session_factory() as db:
        fault_uuid = UUID(fault_id) if isinstance(fault_id, str) else fault_id

        valid_severities = {"low", "medium", "high", "critical"}
        if severity not in valid_severities:
            return {
                "type": "error",
                "id": str(fault_uuid),
                "error": (
                    f"Invalid severity '{severity}'. Valid: {', '.join(sorted(valid_severities))}"
                ),
            }

        fault_result = await db.execute(select(Fault).where(Fault.id == fault_uuid))
        fault = fault_result.scalar_one_or_none()

        if not fault:
            logger.warning(f"Fault {fault_id} not found for severity update")
            return {
                "type": "not_found",
                "id": str(fault_uuid),
                "error": "No fault found with that ID",
            }

        old_severity = fault.severity
        fault.severity = severity

        await db.commit()
        await db.refresh(fault)

        logger.info(f"Updated fault {fault_id} severity: {old_severity} -> {severity}")
        await _trigger_graph_sync()
        return {
            "type": "fault_severity_update",
            "fault_id": str(fault.id),
            "fault_code": fault.code,
            "fault_name": fault.name,
            "old_severity": old_severity,
            "new_severity": fault.severity,
        }


# --- Mutation dispatch helpers ---


SCHEDULER_MUTATIONS = {
    "create_maintenance_plan": create_maintenance_plan,
    "create_task": create_task,
    "assign_task": assign_task,
    "update_task_status": update_task_status,
    "reschedule_task": reschedule_task,
}

ANALYZER_MUTATIONS = {
    "log_down_event": log_down_event,
    "close_down_event": close_down_event,
    "update_fault_severity": update_fault_severity,
}


async def execute_scheduler_mutation(mutation: str) -> dict:
    parts = mutation.split(":", 2)
    action = parts[0]

    if action == "create_maintenance_plan" and len(parts) >= 3:
        return await create_maintenance_plan(parts[1], parts[2])
    elif action == "create_task" and len(parts) >= 3:
        return await create_task(parts[2], parts[1])
    elif action == "assign_task" and len(parts) >= 3:
        return await assign_task(parts[1], parts[2])
    elif action == "update_task_status" and len(parts) >= 3:
        return await update_task_status(parts[1], parts[2])
    elif action == "reschedule_task" and len(parts) >= 3:
        return await reschedule_task(parts[1], parts[2])
    else:
        return {"type": "error", "error": f"Unknown or malformed scheduling mutation: {mutation}"}


async def execute_analyzer_mutation(mutation: str) -> dict:
    parts = mutation.split(":", 2)
    action = parts[0]

    if action == "log_down_event" and len(parts) >= 3:
        desc_parts = parts[2].split(":", 1)
        description = desc_parts[1] if len(desc_parts) > 1 else desc_parts[0]
        fault_uuid = desc_parts[0] if len(desc_parts) > 1 else ""
        return await log_down_event(parts[1], fault_uuid, description)
    elif action == "close_down_event" and len(parts) >= 3:
        return await close_down_event(parts[1], parts[2])
    elif action == "update_fault_severity" and len(parts) >= 3:
        return await update_fault_severity(parts[1], parts[2])
    else:
        return {"type": "error", "error": f"Unknown or malformed analysis mutation: {mutation}"}
