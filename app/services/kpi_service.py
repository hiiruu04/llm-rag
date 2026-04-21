from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.models.down_event import DownEvent


async def compute_mttr(
    asset_id: UUID | None = None,
    asset_name: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    async with async_session_factory() as db:
        query = select(
            func.count(DownEvent.id).label("count"),
            func.avg(DownEvent.downtime_minutes).label("mean_minutes"),
            func.min(DownEvent.downtime_minutes).label("min_minutes"),
            func.max(DownEvent.downtime_minutes).label("max_minutes"),
            func.sum(DownEvent.downtime_minutes).label("total_minutes"),
        ).where(DownEvent.ended_at.isnot(None))

        if asset_id:
            query = query.where(DownEvent.asset_id == asset_id)
        if start_date:
            query = query.where(DownEvent.started_at >= start_date)
        if end_date:
            query = query.where(DownEvent.started_at <= end_date)

        result = await db.execute(query)
        row = result.one()

        if row.count == 0:
            return {
                "count": 0,
                "mean_minutes": None,
                "min_minutes": None,
                "max_minutes": None,
                "total_minutes": 0,
            }

        if asset_name:
            from app.models.asset import Asset

            asset_query = select(Asset).where(Asset.name.ilike(f"%{asset_name}%"))
            asset_result = await db.execute(asset_query)
            assets = list(asset_result.scalars().all())
            if not assets:
                return {
                    "count": 0,
                    "mean_minutes": None,
                    "min_minutes": None,
                    "max_minutes": None,
                    "total_minutes": 0,
                    "asset_name": asset_name,
                }
            asset_ids = [a.id for a in assets]
            detail_query = select(
                func.count(DownEvent.id).label("count"),
                func.avg(DownEvent.downtime_minutes).label("mean_minutes"),
                func.min(DownEvent.downtime_minutes).label("min_minutes"),
                func.max(DownEvent.downtime_minutes).label("max_minutes"),
                func.sum(DownEvent.downtime_minutes).label("total_minutes"),
            ).where(
                DownEvent.ended_at.isnot(None),
                DownEvent.asset_id.in_(asset_ids),
            )
            if start_date:
                detail_query = detail_query.where(DownEvent.started_at >= start_date)
            if end_date:
                detail_query = detail_query.where(DownEvent.started_at <= end_date)
            detail_result = await db.execute(detail_query)
            row = detail_result.one()

        return {
            "count": row.count,
            "mean_minutes": round(row.mean_minutes, 2) if row.mean_minutes else None,
            "min_minutes": row.min_minutes,
            "max_minutes": row.max_minutes,
            "total_minutes": row.total_minutes or 0,
        }


async def compute_mtbf(
    asset_id: UUID | None = None,
    asset_name: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    async with async_session_factory() as db:
        query = select(
            func.count(DownEvent.id).label("count"),
            func.avg(DownEvent.downtime_minutes).label("avg_downtime"),
        ).where(DownEvent.ended_at.isnot(None))

        if asset_id:
            query = query.where(DownEvent.asset_id == asset_id)
        if start_date:
            query = query.where(DownEvent.started_at >= start_date)
        if end_date:
            query = query.where(DownEvent.started_at <= end_date)

        result = await db.execute(query)
        row = result.one()

        count = row.count or 0
        if count == 0:
            return {"count": 0, "mean_minutes": None}

        total_period_minutes = 0.0
        actual_start = start_date
        actual_end = end_date or datetime.now(timezone.utc)

        if not actual_start:
            earliest_query = select(func.min(DownEvent.started_at)).where(
                DownEvent.ended_at.isnot(None)
            )
            if asset_id:
                earliest_query = earliest_query.where(DownEvent.asset_id == asset_id)
            earliest_result = await db.execute(earliest_query)
            earliest = earliest_result.scalar()
            if earliest:
                actual_start = earliest
            else:
                actual_start = actual_end - timedelta(days=90)

        if actual_start and actual_end:
            total_period_minutes = (actual_end - actual_start).total_seconds() / 60

        if count <= 0 or total_period_minutes <= 0:
            return {"count": count, "mean_minutes": None}

        total_downtime = row.avg_downtime * count if row.avg_downtime else 0
        uptime = total_period_minutes - total_downtime
        mtbf = uptime / count if count > 0 else None

        return {
            "count": count,
            "mean_minutes": round(mtbf, 2) if mtbf else None,
            "period_start": str(actual_start) if actual_start else None,
            "period_end": str(actual_end),
            "total_period_minutes": round(total_period_minutes, 2),
            "total_downtime_minutes": round(total_downtime, 2) if total_downtime else 0,
        }


async def compute_availability(
    asset_id: UUID | None = None,
    asset_name: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    end_dt = end_date or datetime.now(timezone.utc)
    start_dt = start_date or (end_dt - timedelta(days=90))
    total_minutes = (end_dt - start_dt).total_seconds() / 60

    async with async_session_factory() as db:
        query = select(func.sum(DownEvent.downtime_minutes)).where(
            DownEvent.started_at >= start_dt,
            DownEvent.started_at <= end_dt,
        )

        if asset_id:
            query = query.where(DownEvent.asset_id == asset_id)

        if asset_name:
            from app.models.asset import Asset

            asset_query = select(Asset).where(Asset.name.ilike(f"%{asset_name}%"))
            asset_result = await db.execute(asset_query)
            assets = list(asset_result.scalars().all())
            if assets:
                asset_ids = [a.id for a in assets]
                query = query.where(DownEvent.asset_id.in_(asset_ids))

        result = await db.execute(query)
        total_downtime = result.scalar() or 0

    uptime = total_minutes - total_downtime
    availability_pct = (uptime / total_minutes * 100) if total_minutes > 0 else 0

    return {
        "percentage": round(availability_pct, 2),
        "uptime_minutes": round(uptime, 2),
        "downtime_minutes": round(total_downtime, 2),
        "total_period_minutes": round(total_minutes, 2),
        "period_start": str(start_dt),
        "period_end": str(end_dt),
    }


async def compute_kpi_summary(asset_name: str | None = None) -> dict:
    from app.models.asset import Asset

    async with async_session_factory() as db:
        asset_id = None
        if asset_name:
            asset_result = await db.execute(
                select(Asset).where(Asset.name.ilike(f"%{asset_name}%"))
            )
            asset = asset_result.scalar_one_or_none()
            if asset:
                asset_id = asset.id

    mttr = await compute_mttr(asset_id=asset_id, asset_name=asset_name)
    mtbf = await compute_mtbf(asset_id=asset_id, asset_name=asset_name)
    availability = await compute_availability(asset_id=asset_id, asset_name=asset_name)

    summary = {}
    if mttr.get("count", 0) > 0:
        summary["mttr"] = mttr
    if mtbf.get("count", 0) > 0:
        summary["mtbf"] = mtbf
    summary["availability"] = availability

    return summary
