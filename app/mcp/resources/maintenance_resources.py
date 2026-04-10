from sqlalchemy import select

from app.core.database import async_session_factory
from app.mcp.server import mcp_server
from app.models.asset import Asset
from app.models.maintenance_schedule import MaintenanceSchedule


@mcp_server.resource("cmms://maintenance/overdue")
async def overdue_maintenance() -> str:
    """All overdue maintenance schedules."""
    from datetime import datetime, timezone

    async with async_session_factory() as session:
        result = await session.execute(
            select(MaintenanceSchedule)
            .where(
                MaintenanceSchedule.status == "scheduled",
                MaintenanceSchedule.scheduled_date < datetime.now(timezone.utc),
            )
            .order_by(MaintenanceSchedule.scheduled_date)
        )
        schedules = result.scalars().all()

        sched_data = []
        for m in schedules:
            asset = await session.get(Asset, m.asset_id)
            sched_data.append((m, asset.name if asset else "Unknown"))

    if not sched_data:
        return "No overdue maintenance."

    lines = [f"Overdue maintenance ({len(sched_data)}):"]
    for m, asset_name in sched_data:
        lines.append(
            f"- {m.title} on {asset_name} "
            f"(type: {m.maintenance_type}, priority: {m.priority}, "
            f"was scheduled: {m.scheduled_date}, assigned: {m.assigned_to or 'Unassigned'})"
        )
    return "\n".join(lines)
