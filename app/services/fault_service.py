from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fault import Fault, fault_cause_effect
from app.models.schemas import FaultCreate, FaultUpdate


async def create_fault(db: AsyncSession, asset_id: UUID, data: FaultCreate) -> Fault:
    fault = Fault(
        asset_id=asset_id,
        code=data.code,
        name=data.name,
        description=data.description,
        severity=data.severity,
        status=data.status,
        detected_at=data.detected_at,
        resolved_at=data.resolved_at,
    )
    db.add(fault)
    await db.commit()
    await db.refresh(fault)
    return fault


async def get_fault(db: AsyncSession, fault_id: UUID) -> Optional[Fault]:
    result = await db.execute(select(Fault).where(Fault.id == fault_id))
    return fault if (fault := result.scalar_one_or_none()) else None


async def list_faults(
    db: AsyncSession, asset_id: UUID, page: int = 1, per_page: int = 10
) -> tuple[list[Fault], int]:
    count_result = await db.execute(select(func.count(Fault.id)).where(Fault.asset_id == asset_id))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Fault)
        .where(Fault.asset_id == asset_id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    faults = list(result.scalars().all())
    return faults, total


async def list_all_faults(
    db: AsyncSession,
    asset_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[Fault], int]:
    conditions = []
    if asset_id is not None:
        conditions.append(Fault.asset_id == asset_id)
    if severity is not None:
        conditions.append(Fault.severity == severity)
    if status is not None:
        conditions.append(Fault.status == status)

    count_query = select(func.count(Fault.id))
    data_query = select(Fault).order_by(Fault.detected_at.desc())

    for condition in conditions:
        count_query = count_query.where(condition)
        data_query = data_query.where(condition)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    result = await db.execute(data_query.offset((page - 1) * per_page).limit(per_page))
    faults = list(result.scalars().all())
    return faults, total


async def update_fault(db: AsyncSession, fault: Fault, data: FaultUpdate) -> Fault:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fault, field, value)
    await db.commit()
    await db.refresh(fault)
    return fault


async def delete_fault(db: AsyncSession, fault: Fault) -> None:
    await db.delete(fault)
    await db.commit()


async def add_fault_link(
    db: AsyncSession,
    fault_id: UUID,
    linked_fault_id: UUID,
    link_type: str,
) -> None:
    await db.execute(
        fault_cause_effect.insert().values(
            causing_fault_id=linked_fault_id if link_type == "cause" else fault_id,
            affected_fault_id=fault_id if link_type == "cause" else linked_fault_id,
            link_type=link_type,
        )
    )
    await db.commit()


async def remove_fault_link(db: AsyncSession, fault_id: UUID, linked_id: UUID) -> None:
    await db.execute(
        fault_cause_effect.delete().where(
            and_(
                fault_cause_effect.c.causing_fault_id == linked_id,
                fault_cause_effect.c.affected_fault_id == fault_id,
            )
        )
    )
    # Also try the reverse direction
    await db.execute(
        fault_cause_effect.delete().where(
            and_(
                fault_cause_effect.c.causing_fault_id == fault_id,
                fault_cause_effect.c.affected_fault_id == linked_id,
            )
        )
    )
    await db.commit()


async def get_causes(db: AsyncSession, fault_id: UUID) -> list[Fault]:
    result = await db.execute(
        select(Fault)
        .join(fault_cause_effect, Fault.id == fault_cause_effect.c.causing_fault_id)
        .where(fault_cause_effect.c.affected_fault_id == fault_id)
    )
    return list(result.scalars().all())


async def get_effects(db: AsyncSession, fault_id: UUID) -> list[Fault]:
    result = await db.execute(
        select(Fault)
        .join(fault_cause_effect, Fault.id == fault_cause_effect.c.affected_fault_id)
        .where(fault_cause_effect.c.causing_fault_id == fault_id)
    )
    return list(result.scalars().all())
