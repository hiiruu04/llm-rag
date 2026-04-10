from loguru import logger

from app.core.neo4j import get_neo4j_driver

CONSTRAINTS = [
    "CREATE CONSTRAINT asset_pg_id IF NOT EXISTS FOR (a:Asset) REQUIRE a.pg_id IS UNIQUE",
    "CREATE CONSTRAINT sensor_pg_id IF NOT EXISTS FOR (s:Sensor) REQUIRE s.pg_id IS UNIQUE",
    "CREATE CONSTRAINT fault_pg_id IF NOT EXISTS FOR (f:Fault) REQUIRE f.pg_id IS UNIQUE",
    (
        "CREATE CONSTRAINT maintenance_pg_id IF NOT EXISTS "
        "FOR (m:MaintenanceSchedule) REQUIRE m.pg_id IS UNIQUE"
    ),
]

INDEXES = [
    "CREATE INDEX asset_status IF NOT EXISTS FOR (a:Asset) ON (a.status)",
    "CREATE INDEX asset_type IF NOT EXISTS FOR (a:Asset) ON (a.asset_type)",
    "CREATE INDEX fault_severity IF NOT EXISTS FOR (f:Fault) ON (f.severity)",
    "CREATE INDEX fault_status IF NOT EXISTS FOR (f:Fault) ON (f.status)",
    (
        "CREATE INDEX maintenance_status IF NOT EXISTS "
        "FOR (m:MaintenanceSchedule) ON (m.status)"
    ),
    (
        "CREATE INDEX maintenance_scheduled IF NOT EXISTS "
        "FOR (m:MaintenanceSchedule) ON (m.scheduled_date)"
    ),
]

FULLTEXT_INDEXES = [
    (
        "CREATE FULLTEXT INDEX asset_name_search IF NOT EXISTS "
        "FOR (a:Asset) ON EACH [a.name, a.description]"
    ),
    (
        "CREATE FULLTEXT INDEX fault_name_search IF NOT EXISTS "
        "FOR (f:Fault) ON EACH [f.name, f.description]"
    ),
]


async def setup_neo4j_schema() -> None:
    driver = await get_neo4j_driver()

    async with driver.session() as session:
        for stmt in CONSTRAINTS:
            await session.run(stmt)
        logger.info("Neo4j constraints created")

        for stmt in INDEXES:
            await session.run(stmt)
        logger.info("Neo4j indexes created")

        for stmt in FULLTEXT_INDEXES:
            await session.run(stmt)
        logger.info("Neo4j fulltext indexes created")

    logger.info("Neo4j schema initialization complete")
