from typing import Optional

from loguru import logger
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.core.config import settings

_driver: Optional[AsyncDriver] = None


async def get_neo4j_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        logger.info(f"Neo4j driver created for {settings.neo4j_uri}")
    return _driver


async def close_neo4j_driver() -> None:
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


async def check_neo4j_connection() -> bool:
    try:
        driver = await get_neo4j_driver()
        async with driver.session(database=settings.neo4j_database) as session:
            result = await session.run("RETURN 1 AS check")
            await result.consume()
        return True
    except Exception as e:
        logger.error(f"Neo4j connection check failed: {e}")
        return False


async def get_neo4j_info() -> dict:
    try:
        driver = await get_neo4j_driver()
        async with driver.session(database=settings.neo4j_database) as session:
            counts = {}
            for label in ["Asset", "Sensor", "Fault", "MaintenanceSchedule", "SensorSummary"]:
                result = await session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
                record = await result.single()
                counts[f"total_{label.lower()}s"] = record["cnt"] if record else 0

            # Check sync metadata
            result = await session.run(
                "MATCH (s:SyncMetadata) RETURN s.last_full_sync AS lfs, "
                "s.last_incremental_sync AS lis, s.sync_in_progress AS sip"
            )
            record = await result.single()
            if record:
                lfs = record["lfs"]
                lis = record["lis"]
                counts["last_full_sync"] = str(lfs) if lfs is not None else None
                counts["last_incremental_sync"] = str(lis) if lis is not None else None
                counts["sync_in_progress"] = record["sip"]
            else:
                counts["last_full_sync"] = None
                counts["last_incremental_sync"] = None
                counts["sync_in_progress"] = False

        return {"connected": True, **counts}
    except Exception as e:
        logger.error(f"Neo4j info retrieval failed: {e}")
        return {"connected": False, "error": str(e)}
