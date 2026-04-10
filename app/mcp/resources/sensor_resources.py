from app.core.config import settings
from app.core.neo4j import get_neo4j_driver
from app.mcp.server import mcp_server


@mcp_server.resource("cmms://sensors/anomalies")
async def sensor_anomalies() -> str:
    """Sensor summaries flagged as anomalous (last 24h)."""
    driver = await get_neo4j_driver()

    cypher = (
        "MATCH (s:Sensor)-[:HAS_SUMMARY]->(sum:SensorSummary) "
        "WHERE sum.anomaly_flag = true "
        "AND sum.window IN ['1h', '6h', '24h'] "
        "RETURN s.name AS sensor, s.sensor_type AS type, s.unit AS unit, "
        "sum.window, sum.avg_value, sum.min_value, sum.max_value, "
        "sum.stddev, sum.sample_count "
        "ORDER BY s.name, sum.window"
    )

    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(cypher)
        records = await result.data()

    if not records:
        return "No anomalous sensor readings detected."

    lines = [f"Anomalous sensors ({len(records)} readings):"]
    for r in records:
        lines.append(
            f"- {r['sensor']} ({r['type']}, {r.get('unit', 'N/A')}) window={r['window']}\n"
            f"  avg: {r['avg_value']:.2f}, min: {r['min_value']:.2f}, "
            f"max: {r['max_value']:.2f}, stddev: {r['stddev']:.2f}, "
            f"samples: {r['sample_count']}"
        )
    return "\n".join(lines)
