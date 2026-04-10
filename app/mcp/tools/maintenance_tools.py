from typing import Optional

from sqlalchemy import select

from app.core.database import async_session_factory
from app.mcp.server import mcp_server
from app.models.asset import Asset
from app.models.maintenance_schedule import MaintenanceSchedule


@mcp_server.tool()
async def get_maintenance_schedule(
    asset_id: Optional[str] = None,
    status: Optional[str] = None,
    maintenance_type: Optional[str] = None,
    priority: Optional[str] = None,
) -> str:
    """Filter and retrieve maintenance schedules.

    Args:
        asset_id: Filter by asset UUID
        status: Filter by status (scheduled, in_progress, completed, cancelled, overdue)
        maintenance_type: Filter by type (preventive, corrective, predictive)
        priority: Filter by priority (low, medium, high, critical)
    """
    from uuid import UUID

    stmt = select(MaintenanceSchedule)
    if asset_id:
        try:
            stmt = stmt.where(MaintenanceSchedule.asset_id == UUID(asset_id))
        except ValueError:
            return f"Invalid asset ID: {asset_id}"
    if status:
        stmt = stmt.where(MaintenanceSchedule.status == status)
    if maintenance_type:
        stmt = stmt.where(MaintenanceSchedule.maintenance_type == maintenance_type)
    if priority:
        stmt = stmt.where(MaintenanceSchedule.priority == priority)

    async with async_session_factory() as session:
        result = await session.execute(
            stmt.order_by(MaintenanceSchedule.scheduled_date).limit(50)
        )
        schedules = result.scalars().all()

        sched_data = []
        for m in schedules:
            asset = await session.get(Asset, m.asset_id)
            sched_data.append((m, asset.name if asset else "Unknown"))

    if not sched_data:
        return "No maintenance schedules found matching the criteria."

    lines = [f"Found {len(sched_data)} maintenance schedules:"]
    for m, asset_name in sched_data:
        lines.append(
            f"- {m.title} on {asset_name}\n"
            f"  type: {m.maintenance_type}, status: {m.status}, priority: {m.priority}\n"
            f"  scheduled: {m.scheduled_date}, assigned: {m.assigned_to or 'Unassigned'}\n"
            f"  recurrence: {m.recurrence}, duration: {m.estimated_duration_hours or 'N/A'}h"
        )

    return "\n".join(lines)
