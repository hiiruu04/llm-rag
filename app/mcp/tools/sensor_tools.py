from typing import Optional

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.neo4j import get_neo4j_driver
from app.mcp.server import mcp_server
from app.models.sensor_data import SensorData


@mcp_server.tool()
async def get_sensor_status(
    asset_id: Optional[str] = None,
    sensor_id: Optional[str] = None,
) -> str:
    """Get sensor info and latest readings from the database.

    Args:
        asset_id: Filter by asset UUID
        sensor_id: Specific sensor UUID
    """
    driver = await get_neo4j_driver()

    # Build graph query for sensor + asset context
    conditions = []
    params: dict = {}

    if sensor_id:
        conditions.append("s.pg_id = $sensor_id")
        params["sensor_id"] = sensor_id
    elif asset_id:
        conditions.append("a.pg_id = $asset_id")
        params["asset_id"] = asset_id

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    cypher = (
        f"MATCH (a:Asset)-[:HAS_SENSOR]->(s:Sensor) "
        f"{where} "
        f"RETURN a.name AS asset, s.pg_id AS sensor_pg_id, "
        f"s.name AS sensor, s.sensor_type AS type, "
        f"s.unit AS unit, s.status AS status "
        f"ORDER BY a.name, s.name"
    )

    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(cypher, **params)
        records = await result.data()

    if not records:
        return "No sensors found for the given criteria."

    # Fetch latest reading per sensor from PostgreSQL
    sensor_pg_ids = [r["sensor_pg_id"] for r in records if r.get("sensor_pg_id")]
    latest_readings: dict = {}

    if sensor_pg_ids:
        import uuid

        pg_ids = [uuid.UUID(sid) for sid in sensor_pg_ids]
        async with async_session_factory() as pg_session:
            subq = (
                select(
                    SensorData.sensor_id,
                    func.max(SensorData.timestamp).label("latest_ts"),
                )
                .where(SensorData.sensor_id.in_(pg_ids))
                .group_by(SensorData.sensor_id)
                .subquery()
            )
            stmt = select(SensorData).join(
                subq,
                (SensorData.sensor_id == subq.c.sensor_id)
                & (SensorData.timestamp == subq.c.latest_ts),
            )
            result = await pg_session.execute(stmt)
            for sd in result.scalars().all():
                latest_readings[str(sd.sensor_id)] = {
                    "value": sd.value,
                    "timestamp": sd.timestamp.isoformat(),
                }

    lines = [f"Sensors ({len(records)} found):"]
    for r in records:
        reading = latest_readings.get(r["sensor_pg_id"])
        reading_str = (
            f", latest: {reading['value']} at {reading['timestamp']}"
            if reading
            else ", no readings"
        )
        lines.append(
            f"- {r['asset']} / {r['sensor']} "
            f"({r['type']}, {r.get('unit', 'N/A')}, status: {r['status']})"
            f"{reading_str}"
        )

    return "\n".join(lines)
