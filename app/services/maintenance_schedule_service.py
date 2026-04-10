from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.schemas import MaintenanceScheduleCreate, MaintenanceScheduleUpdate

RECURRENCE_DELTAS: dict[str, timedelta] = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
    "quarterly": timedelta(days=90),
    "yearly": timedelta(days=365),
}


async def create_schedule(
    db: AsyncSession, asset_id: UUID, data: MaintenanceScheduleCreate
) -> MaintenanceSchedule:
    schedule = MaintenanceSchedule(
        asset_id=asset_id,
        fault_id=data.fault_id,
        title=data.title,
        description=data.description,
        maintenance_type=data.maintenance_type,
        priority=data.priority,
        scheduled_date=data.scheduled_date,
        assigned_to=data.assigned_to,
        recurrence=data.recurrence,
        estimated_duration_hours=data.estimated_duration_hours,
        notes=data.notes,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def get_schedule(db: AsyncSession, schedule_id: UUID) -> Optional[MaintenanceSchedule]:
    result = await db.execute(
        select(MaintenanceSchedule).where(MaintenanceSchedule.id == schedule_id)
    )
    return schedule if (schedule := result.scalar_one_or_none()) else None


async def list_schedules(
    db: AsyncSession,
    asset_id: Optional[UUID] = None,
    status: Optional[str] = None,
    maintenance_type: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[MaintenanceSchedule], int]:
    conditions = []
    if asset_id is not None:
        conditions.append(MaintenanceSchedule.asset_id == asset_id)
    if status is not None:
        conditions.append(MaintenanceSchedule.status == status)
    if maintenance_type is not None:
        conditions.append(MaintenanceSchedule.maintenance_type == maintenance_type)
    if priority is not None:
        conditions.append(MaintenanceSchedule.priority == priority)

    count_query = select(func.count(MaintenanceSchedule.id))
    data_query = select(MaintenanceSchedule).order_by(MaintenanceSchedule.scheduled_date)

    for condition in conditions:
        count_query = count_query.where(condition)
        data_query = data_query.where(condition)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    result = await db.execute(
        data_query.offset((page - 1) * per_page).limit(per_page)
    )
    schedules = list(result.scalars().all())
    return schedules, total


async def update_schedule(
    db: AsyncSession, schedule: MaintenanceSchedule, data: MaintenanceScheduleUpdate
) -> MaintenanceSchedule:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def delete_schedule(db: AsyncSession, schedule: MaintenanceSchedule) -> None:
    await db.delete(schedule)
    await db.commit()


async def mark_completed(
    db: AsyncSession, schedule: MaintenanceSchedule
) -> MaintenanceSchedule:
    schedule.status = "completed"
    schedule.completed_date = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def detect_and_mark_overdue(db: AsyncSession) -> list[MaintenanceSchedule]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(MaintenanceSchedule)
        .where(
            MaintenanceSchedule.status.in_(["scheduled", "in_progress"]),
            MaintenanceSchedule.scheduled_date < now,
        )
        .values(status="overdue")
        .returning(MaintenanceSchedule)
    )
    await db.commit()
    rows = result.fetchall()
    return [row[0] for row in rows]


async def get_overdue_schedules(
    db: AsyncSession, page: int = 1, per_page: int = 10
) -> tuple[list[MaintenanceSchedule], int]:
    count_result = await db.execute(
        select(func.count(MaintenanceSchedule.id)).where(
            MaintenanceSchedule.status == "overdue"
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(MaintenanceSchedule)
        .where(MaintenanceSchedule.status == "overdue")
        .order_by(MaintenanceSchedule.scheduled_date)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    schedules = list(result.scalars().all())
    return schedules, total


async def generate_next_recurrence(
    db: AsyncSession, schedule: MaintenanceSchedule
) -> Optional[MaintenanceSchedule]:
    if schedule.recurrence == "none":
        return None

    delta = RECURRENCE_DELTAS.get(schedule.recurrence)
    if delta is None:
        return None

    next_date = schedule.scheduled_date + delta
    next_schedule = MaintenanceSchedule(
        asset_id=schedule.asset_id,
        fault_id=schedule.fault_id,
        title=schedule.title,
        description=schedule.description,
        maintenance_type=schedule.maintenance_type,
        priority=schedule.priority,
        scheduled_date=next_date,
        assigned_to=schedule.assigned_to,
        recurrence=schedule.recurrence,
        estimated_duration_hours=schedule.estimated_duration_hours,
        notes=schedule.notes,
    )
    db.add(next_schedule)
    await db.commit()
    await db.refresh(next_schedule)
    return next_schedule
