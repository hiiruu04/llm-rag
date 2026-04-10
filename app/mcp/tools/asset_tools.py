from typing import Optional

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.neo4j import get_neo4j_driver
from app.mcp.server import mcp_server
from app.models.asset import Asset
from app.models.fault import Fault
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.sensor import Sensor


@mcp_server.tool()
async def query_assets(
    search: Optional[str] = None,
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 20,
) -> str:
    """Search and filter assets in the CMMS system.

    Args:
        search: Text to search in asset name/description
        asset_type: Filter by asset type (e.g., "machine", "line", "plant")
        status: Filter by status (active, inactive, maintenance, decommissioned)
        location: Filter by location
        limit: Maximum results to return (default 20)
    """
    async with async_session_factory() as session:
        stmt = select(Asset)
        if search:
            stmt = stmt.where(Asset.name.ilike(f"%{search}%"))
        if asset_type:
            stmt = stmt.where(Asset.asset_type == asset_type)
        if status:
            stmt = stmt.where(Asset.status == status)
        if location:
            stmt = stmt.where(Asset.location.ilike(f"%{location}%"))
        stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        assets = result.scalars().all()

    if not assets:
        return "No assets found matching the criteria."

    lines = [f"Found {len(assets)} assets:"]
    for a in assets:
        lines.append(
            f"- {a.name} (ID: {a.id}, type: {a.asset_type}, status: {a.status}, "
            f"location: {a.location or 'N/A'})"
        )
    return "\n".join(lines)


@mcp_server.tool()
async def get_asset_details(
    asset_id: str,
    include_children: bool = True,
    include_sensors: bool = True,
    include_faults: bool = True,
    include_maintenance: bool = True,
) -> str:
    """Get full details for a specific asset including related entities.

    Args:
        asset_id: UUID of the asset
        include_children: Include child assets
        include_sensors: Include associated sensors
        include_faults: Include associated faults
        include_maintenance: Include maintenance schedules
    """
    from uuid import UUID

    try:
        uid = UUID(asset_id)
    except ValueError:
        return f"Invalid asset ID: {asset_id}"

    async with async_session_factory() as session:
        asset = await session.get(Asset, uid)
        if not asset:
            return f"Asset {asset_id} not found."

        lines = [
            f"Asset: {asset.name}",
            f"  ID: {asset.id}",
            f"  Type: {asset.asset_type}",
            f"  Status: {asset.status}",
            f"  Location: {asset.location or 'N/A'}",
            f"  Description: {asset.description or 'N/A'}",
        ]

        if include_children:
            result = await session.execute(
                select(Asset).where(Asset.parent_id == uid)
            )
            children = result.scalars().all()
            if children:
                lines.append(f"  Children ({len(children)}):")
                for c in children:
                    lines.append(f"    - {c.name} ({c.status})")

        if include_sensors:
            result = await session.execute(
                select(Sensor).where(Sensor.asset_id == uid)
            )
            sensors = result.scalars().all()
            if sensors:
                lines.append(f"  Sensors ({len(sensors)}):")
                for s in sensors:
                    lines.append(f"    - {s.name} ({s.sensor_type}, {s.status})")

        if include_faults:
            result = await session.execute(
                select(Fault).where(Fault.asset_id == uid)
            )
            faults = result.scalars().all()
            if faults:
                lines.append(f"  Faults ({len(faults)}):")
                for f in faults:
                    lines.append(
                        f"    - [{f.code}] {f.name} (severity: {f.severity}, status: {f.status})"
                    )

        if include_maintenance:
            result = await session.execute(
                select(MaintenanceSchedule).where(MaintenanceSchedule.asset_id == uid)
            )
            schedules = result.scalars().all()
            if schedules:
                lines.append(f"  Maintenance ({len(schedules)}):")
                for m in schedules:
                    lines.append(
                        f"    - {m.title} (type: {m.maintenance_type}, status: {m.status}, "
                        f"scheduled: {m.scheduled_date})"
                    )

    return "\n".join(lines)


@mcp_server.tool()
async def get_asset_tree(
    root_asset_id: Optional[str] = None,
    max_depth: int = 3,
) -> str:
    """Get the hierarchical asset tree from the knowledge graph.

    Args:
        root_asset_id: Optional UUID of root asset. If omitted, returns all root assets.
        max_depth: Maximum depth of the tree (default 3)
    """
    driver = await get_neo4j_driver()

    if root_asset_id:
        cypher = (
            "MATCH (root:Asset {pg_id: $pg_id}) "
            "MATCH (root)<-[:HAS_PARENT*0..]-(descendant:Asset) "
            "RETURN root.pg_id AS id, root.name AS name, root.asset_type AS type, "
            "root.status AS status, root.location AS location, "
            "length((root)<-[:HAS_PARENT*]-()) AS depth "
            "ORDER BY depth"
        )
        params = {"pg_id": root_asset_id}
    else:
        cypher = (
            "MATCH (root:Asset) "
            "WHERE NOT (root)-[:HAS_PARENT]->(:Asset) "
            "MATCH (root)<-[:HAS_PARENT*0..]-(descendant:Asset) "
            "RETURN DISTINCT descendant.pg_id AS id, descendant.name AS name, "
            "descendant.asset_type AS type, descendant.status AS status, "
            "descendant.location AS location, "
            "length((descendant)<-[:HAS_PARENT*]-()) AS depth "
            "ORDER BY depth"
        )
        params = {}

    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(cypher, **params)
        records = await result.data()

    if not records:
        return "No assets found in the knowledge graph."

    lines = ["Asset Tree:"]
    for r in records:
        depth = r.get("depth", 0)
        if depth > max_depth:
            continue
        indent = "  " * depth
        lines.append(
            f"{indent}- {r['name']} (type: {r['type']}, status: {r['status']}, "
            f"location: {r.get('location') or 'N/A'})"
        )
    return "\n".join(lines)
