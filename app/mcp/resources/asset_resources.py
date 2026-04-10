from sqlalchemy import select

from app.core.database import async_session_factory
from app.mcp.server import mcp_server
from app.models.asset import Asset
from app.models.fault import Fault
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.sensor import Sensor


@mcp_server.resource("cmms://assets/catalog")
async def asset_catalog() -> str:
    """All assets with basic info."""
    async with async_session_factory() as session:
        result = await session.execute(select(Asset).order_by(Asset.name))
        assets = result.scalars().all()

    if not assets:
        return "No assets in the catalog."

    lines = [f"Asset catalog ({len(assets)} assets):"]
    for a in assets:
        lines.append(
            f"- {a.name} (ID: {a.id}, type: {a.asset_type}, "
            f"status: {a.status}, location: {a.location or 'N/A'})"
        )
    return "\n".join(lines)


@mcp_server.resource("cmms://assets/{asset_id}/summary")
async def asset_summary(asset_id: str) -> str:
    """Asset summary: sensors, open faults, upcoming maintenance."""
    from uuid import UUID

    try:
        uid = UUID(asset_id)
    except ValueError:
        return f"Invalid asset ID: {asset_id}"

    async with async_session_factory() as session:
        asset = await session.get(Asset, uid)
        if not asset:
            return f"Asset {asset_id} not found."

        sensors = (await session.execute(
            select(Sensor).where(Sensor.asset_id == uid)
        )).scalars().all()

        open_faults = (await session.execute(
            select(Fault).where(
                Fault.asset_id == uid,
                Fault.status.in_(["open", "investigating"])
            )
        )).scalars().all()

        upcoming = (await session.execute(
            select(MaintenanceSchedule).where(
                MaintenanceSchedule.asset_id == uid,
                MaintenanceSchedule.status.in_(["scheduled", "in_progress"])
            )
        )).scalars().all()

    lines = [
        f"Asset: {asset.name} ({asset.asset_type}, {asset.status})",
        f"Sensors: {len(sensors)}",
        f"Open faults: {len(open_faults)}",
        f"Upcoming maintenance: {len(upcoming)}",
    ]

    if open_faults:
        lines.append("Open faults:")
        for f in open_faults:
            lines.append(f"  - [{f.code}] {f.name} (severity: {f.severity})")

    if upcoming:
        lines.append("Upcoming maintenance:")
        for m in upcoming:
            lines.append(f"  - {m.title} (scheduled: {m.scheduled_date})")

    return "\n".join(lines)
