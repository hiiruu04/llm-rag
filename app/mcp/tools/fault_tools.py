from typing import Optional

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.neo4j import get_neo4j_driver
from app.mcp.server import mcp_server
from app.models.asset import Asset
from app.models.fault import Fault


@mcp_server.tool()
async def search_faults(
    asset_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    code: Optional[str] = None,
    include_chain: bool = False,
) -> str:
    """Search and filter faults across assets.

    Args:
        asset_id: Filter by asset UUID
        severity: Filter by severity (low, medium, high, critical)
        status: Filter by status (open, investigating, resolved, closed)
        code: Filter by fault code
        include_chain: Include cause-effect chain from graph
    """
    from uuid import UUID

    stmt = select(Fault)
    if asset_id:
        try:
            stmt = stmt.where(Fault.asset_id == UUID(asset_id))
        except ValueError:
            return f"Invalid asset ID: {asset_id}"
    if severity:
        stmt = stmt.where(Fault.severity == severity)
    if status:
        stmt = stmt.where(Fault.status == status)
    if code:
        stmt = stmt.where(Fault.code.ilike(f"%{code}%"))

    async with async_session_factory() as session:
        result = await session.execute(stmt.order_by(Fault.detected_at.desc()).limit(50))
        faults = result.scalars().all()

        # Load asset names
        fault_data = []
        for f in faults:
            asset = await session.get(Asset, f.asset_id)
            fault_data.append((f, asset.name if asset else "Unknown"))

    if not fault_data:
        return "No faults found matching the criteria."

    lines = [f"Found {len(fault_data)} faults:"]
    for f, asset_name in fault_data:
        lines.append(
            f"- [{f.code}] {f.name} on {asset_name} "
            f"(severity: {f.severity}, status: {f.status}, detected: {f.detected_at})"
        )

    if include_chain:
        driver = await get_neo4j_driver()
        for f, _ in fault_data[:5]:  # Limit chain lookups
            async with driver.session(database=settings.neo4j_database) as neo_session:
                result = await neo_session.run(
                    "MATCH path = (f:Fault {pg_id: $pg_id})-[:CAUSES*1..5]->(downstream:Fault) "
                    "RETURN [node in nodes(path) | node.code + ': ' + node.name] AS chain",
                    pg_id=str(f.id),
                )
                chains = await result.data()
                if chains:
                    lines.append(f"  Causal chain from {f.code}:")
                    for chain in chains:
                        lines.append(f"    {' -> '.join(chain['chain'])}")

    return "\n".join(lines)


@mcp_server.tool()
async def get_fault_chain(
    fault_id: str,
    direction: str = "downstream",
    max_depth: int = 5,
) -> str:
    """Get the full cause-effect propagation chain for a fault.

    Args:
        fault_id: UUID of the fault
        direction: "upstream" (what caused it), "downstream" (what it causes), or "both"
        max_depth: Maximum chain depth (default 5)
    """
    driver = await get_neo4j_driver()

    if direction == "upstream":
        cypher = (
            "MATCH path = (upstream:Fault)"
            "-[:CAUSES*1..]->(target:Fault {pg_id: $pg_id}) "
            "RETURN [node in nodes(path) | "
            "node.code + ': ' + node.name + "
            "' (' + node.severity + ')'] AS chain"
        )
    elif direction == "downstream":
        cypher = (
            "MATCH path = (target:Fault {pg_id: $pg_id})"
            "-[:CAUSES*1..]->(downstream:Fault) "
            "RETURN [node in nodes(path) | "
            "node.code + ': ' + node.name + "
            "' (' + node.severity + ')'] AS chain"
        )
    else:
        cypher = (
            "MATCH (target:Fault {pg_id: $pg_id}) "
            "OPTIONAL MATCH upstream_path = "
            "(upstream:Fault)-[:CAUSES*1..]->(target) "
            "OPTIONAL MATCH downstream_path = "
            "(target)-[:CAUSES*1..]->(downstream:Fault) "
            "RETURN collect(DISTINCT [node in nodes(upstream_path) | "
            "node.code + ': ' + node.name + "
            "' (' + node.severity + ')']) AS upstream_chains, "
            "collect(DISTINCT [node in nodes(downstream_path) | "
            "node.code + ': ' + node.name + "
            "' (' + node.severity + ')']) AS downstream_chains"
        )

    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(cypher, pg_id=fault_id)
        records = await result.data()

    if not records:
        return f"No fault chain found for fault {fault_id}."

    lines = [f"Fault chain for {fault_id}:"]
    if direction in ("upstream", "downstream"):
        for record in records:
            chain = record.get("chain", [])
            if chain:
                lines.append(f"  {' -> '.join(chain)}")
    else:
        for record in records:
            for uc in record.get("upstream_chains", []):
                if uc:
                    lines.append(f"  Upstream: {' -> '.join(uc)}")
            for dc in record.get("downstream_chains", []):
                if dc:
                    lines.append(f"  Downstream: {' -> '.join(dc)}")

    return "\n".join(lines)
