from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import SensorDataCreate
from app.models.sensor_data import SensorData


async def create_reading(db: AsyncSession, sensor_id: UUID, data: SensorDataCreate) -> SensorData:
    reading = SensorData(
        sensor_id=sensor_id,
        timestamp=data.timestamp,
        value=data.value,
    )
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    return reading


async def create_readings_batch(
    db: AsyncSession, sensor_id: UUID, readings: list[SensorDataCreate]
) -> int:
    objects = [
        SensorData(
            sensor_id=sensor_id,
            timestamp=r.timestamp,
            value=r.value,
        )
        for r in readings
    ]
    db.add_all(objects)
    await db.commit()
    return len(objects)


async def list_readings(
    db: AsyncSession,
    sensor_id: UUID,
    page: int = 1,
    per_page: int = 50,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> tuple[list[SensorData], int]:
    query = select(SensorData).where(SensorData.sensor_id == sensor_id)
    count_query = select(func.count(SensorData.id)).where(SensorData.sensor_id == sensor_id)

    if start_time:
        query = query.where(SensorData.timestamp >= start_time)
        count_query = count_query.where(SensorData.timestamp >= start_time)
    if end_time:
        query = query.where(SensorData.timestamp <= end_time)
        count_query = count_query.where(SensorData.timestamp <= end_time)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(SensorData.timestamp.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    readings = list(result.scalars().all())
    return readings, total


async def get_latest_reading(db: AsyncSession, sensor_id: UUID) -> Optional[SensorData]:
    result = await db.execute(
        select(SensorData)
        .where(SensorData.sensor_id == sensor_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def delete_readings_in_range(
    db: AsyncSession,
    sensor_id: UUID,
    start_time: datetime,
    end_time: datetime,
) -> int:
    result = await db.execute(
        delete(SensorData)
        .where(SensorData.sensor_id == sensor_id)
        .where(SensorData.timestamp >= start_time)
        .where(SensorData.timestamp <= end_time)
        .returning(SensorData.id)
    )
    await db.commit()
    return len(result.all())
