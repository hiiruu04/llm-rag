from sqlalchemy import select

from app.core.database import async_session_factory
from app.mcp.server import mcp_server
from app.models.asset import Asset
from app.models.fault import Fault


@mcp_server.resource("cmms://faults/active")
async def active_faults() -> str:
    """All active (non-resolved) faults."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Fault)
            .where(Fault.status.in_(["open", "investigating"]))
            .order_by(Fault.severity, Fault.detected_at.desc())
        )
        faults = result.scalars().all()

        fault_data = []
        for f in faults:
            asset = await session.get(Asset, f.asset_id)
            fault_data.append((f, asset.name if asset else "Unknown"))

    if not fault_data:
        return "No active faults."

    lines = [f"Active faults ({len(fault_data)}):"]
    for f, asset_name in fault_data:
        lines.append(
            f"- [{f.code}] {f.name} on {asset_name} "
            f"(severity: {f.severity}, status: {f.status}, detected: {f.detected_at})"
        )
    return "\n".join(lines)
