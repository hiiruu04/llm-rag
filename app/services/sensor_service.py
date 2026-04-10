from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import SensorCreate, SensorUpdate
from app.models.sensor import Sensor


async def create_sensor(db: AsyncSession, asset_id: UUID, data: SensorCreate) -> Sensor:
    sensor = Sensor(
        asset_id=asset_id,
        name=data.name,
        sensor_type=data.sensor_type,
        unit=data.unit,
        status=data.status,
    )
    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)
    return sensor


async def get_sensor(db: AsyncSession, sensor_id: UUID) -> Optional[Sensor]:
    result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    return result.scalar_one_or_none()


async def list_sensors(
    db: AsyncSession, asset_id: UUID, page: int = 1, per_page: int = 10
) -> tuple[list[Sensor], int]:
    count_result = await db.execute(
        select(func.count(Sensor.id)).where(Sensor.asset_id == asset_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Sensor)
        .where(Sensor.asset_id == asset_id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    sensors = list(result.scalars().all())
    return sensors, total


async def update_sensor(db: AsyncSession, sensor: Sensor, data: SensorUpdate) -> Sensor:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sensor, field, value)
    await db.commit()
    await db.refresh(sensor)
    return sensor


async def delete_sensor(db: AsyncSession, sensor: Sensor) -> None:
    await db.delete(sensor)
    await db.commit()
