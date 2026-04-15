from app.core.config import settings
from app.core.neo4j import get_neo4j_driver
from app.mcp.server import mcp_server


@mcp_server.resource("cmms://sensors/anomalies")
async def sensor_anomalies() -> str:
    """Sensors with active faults on their parent assets."""
    driver = await get_neo4j_driver()

    cypher = (
        "MATCH (a:Asset)-[:HAS_SENSOR]->(s:Sensor) "
        "MATCH (a)-[:HAS_FAULT]->(f:Fault) "
        "WHERE f.status IN ['open', 'in_progress'] "
        "RETURN DISTINCT s.name AS sensor, s.sensor_type AS type, "
        "s.unit AS unit, a.name AS asset, collect(f.name) AS faults "
        "ORDER BY a.name, s.name"
    )

    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(cypher)
        records = await result.data()

    if not records:
        return "No sensors with active faults detected."

    lines = [f"Sensors on assets with active faults ({len(records)} sensors):"]
    for r in records:
        lines.append(
            f"- {r['sensor']} ({r['type']}, {r.get('unit', 'N/A')}) "
            f"on {r['asset']}, faults: {', '.join(r['faults'])}"
        )
    return "\n".join(lines)
