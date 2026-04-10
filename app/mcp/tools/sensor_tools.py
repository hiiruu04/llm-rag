from typing import Optional

from app.core.config import settings
from app.core.neo4j import get_neo4j_driver
from app.mcp.server import mcp_server


@mcp_server.tool()
async def get_sensor_status(
    asset_id: Optional[str] = None,
    sensor_id: Optional[str] = None,
    window: str = "1h",
    include_latest_reading: bool = True,
) -> str:
    """Get sensor readings and aggregated summaries.

    Args:
        asset_id: Filter by asset UUID
        sensor_id: Specific sensor UUID
        window: Aggregation window (1h, 6h, 24h, 7d, 30d)
        include_latest_reading: Include the most recent reading
    """
    driver = await get_neo4j_driver()

    conditions = ["sum.window = $window"]
    params = {"window": window}

    if sensor_id:
        conditions.append("s.pg_id = $sensor_id")
        params["sensor_id"] = sensor_id
    elif asset_id:
        conditions.append("a.pg_id = $asset_id")
        params["asset_id"] = asset_id

    where = " AND ".join(conditions)

    cypher = (
        f"MATCH (a:Asset)-[:HAS_SENSOR]->(s:Sensor)"
        f"-[:HAS_SUMMARY]->(sum:SensorSummary) "
        f"WHERE {where} "
        f"RETURN a.name AS asset, s.name AS sensor, "
        f"s.sensor_type AS type, s.unit AS unit, "
        f"sum.window, sum.avg_value, sum.min_value, "
        f"sum.max_value, sum.stddev, sum.sample_count, "
        f"sum.anomaly_flag "
        f"ORDER BY a.name, s.name"
    )

    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(cypher, **params)
        records = await result.data()

    if not records:
        return "No sensor summaries found for the given criteria."

    lines = [f"Sensor summaries (window: {window}):"]
    for r in records:
        anomaly = " [ANOMALY]" if r.get("anomaly_flag") else ""
        lines.append(
            f"- {r['asset']} / {r['sensor']} ({r['type']}, {r.get('unit', 'N/A')}){anomaly}\n"
            f"  avg: {r['avg_value']:.2f}, min: {r['min_value']:.2f}, "
            f"max: {r['max_value']:.2f}, stddev: {r['stddev']:.2f}, "
            f"samples: {r['sample_count']}"
        )

    return "\n".join(lines)
