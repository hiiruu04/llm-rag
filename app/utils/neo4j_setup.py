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
    "CREATE CONSTRAINT worker_pg_id IF NOT EXISTS FOR (w:Worker) REQUIRE w.pg_id IS UNIQUE",
    "CREATE CONSTRAINT role_pg_id IF NOT EXISTS FOR (r:Role) REQUIRE r.pg_id IS UNIQUE",
    (
        "CREATE CONSTRAINT competence_pg_id IF NOT EXISTS "
        "FOR (c:Competence) REQUIRE c.pg_id IS UNIQUE"
    ),
    "CREATE CONSTRAINT level_pg_id IF NOT EXISTS FOR (l:Level) REQUIRE l.pg_id IS UNIQUE",
    "CREATE CONSTRAINT task_pg_id IF NOT EXISTS FOR (t:Task) REQUIRE t.pg_id IS UNIQUE",
    "CREATE CONSTRAINT cause_pg_id IF NOT EXISTS FOR (c:Cause) REQUIRE c.pg_id IS UNIQUE",
    "CREATE CONSTRAINT material_pg_id IF NOT EXISTS FOR (m:Material) REQUIRE m.pg_id IS UNIQUE",
    "CREATE CONSTRAINT shift_pg_id IF NOT EXISTS FOR (s:Shift) REQUIRE s.pg_id IS UNIQUE",
    "CREATE CONSTRAINT down_event_pg_id IF NOT EXISTS FOR (d:DownEvent) REQUIRE d.pg_id IS UNIQUE",
    "CREATE CONSTRAINT order_pg_id IF NOT EXISTS FOR (o:Order) REQUIRE o.pg_id IS UNIQUE",
    "CREATE CONSTRAINT location_pg_id IF NOT EXISTS FOR (l:Location) REQUIRE l.pg_id IS UNIQUE",
    "CREATE CONSTRAINT system_pg_id IF NOT EXISTS FOR (s:System) REQUIRE s.pg_id IS UNIQUE",
    "CREATE CONSTRAINT aggregate_pg_id IF NOT EXISTS FOR (a:Aggregate) REQUIRE a.pg_id IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX asset_status IF NOT EXISTS FOR (a:Asset) ON (a.status)",
    "CREATE INDEX asset_type IF NOT EXISTS FOR (a:Asset) ON (a.asset_type)",
    "CREATE INDEX fault_severity IF NOT EXISTS FOR (f:Fault) ON (f.severity)",
    "CREATE INDEX fault_status IF NOT EXISTS FOR (f:Fault) ON (f.status)",
    ("CREATE INDEX maintenance_status IF NOT EXISTS FOR (m:MaintenanceSchedule) ON (m.status)"),
    (
        "CREATE INDEX maintenance_scheduled IF NOT EXISTS "
        "FOR (m:MaintenanceSchedule) ON (m.scheduled_date)"
    ),
    "CREATE INDEX worker_status IF NOT EXISTS FOR (w:Worker) ON (w.status)",
    "CREATE INDEX worker_employee_id IF NOT EXISTS FOR (w:Worker) ON (w.employee_id)",
    "CREATE INDEX worker_level_id IF NOT EXISTS FOR (w:Worker) ON (w.level_id)",
    "CREATE INDEX competence_category IF NOT EXISTS FOR (c:Competence) ON (c.category)",
    "CREATE INDEX task_status IF NOT EXISTS FOR (t:Task) ON (t.status)",
    "CREATE INDEX task_type IF NOT EXISTS FOR (t:Task) ON (t.task_type)",
    "CREATE INDEX task_schedule_id IF NOT EXISTS FOR (t:Task) ON (t.maintenance_schedule_id)",
    "CREATE INDEX task_shift_id IF NOT EXISTS FOR (t:Task) ON (t.shift_id)",
    "CREATE INDEX cause_category IF NOT EXISTS FOR (c:Cause) ON (c.category)",
    "CREATE INDEX cause_severity IF NOT EXISTS FOR (c:Cause) ON (c.severity)",
    "CREATE INDEX down_event_severity IF NOT EXISTS FOR (d:DownEvent) ON (d.severity)",
    "CREATE INDEX down_event_status IF NOT EXISTS FOR (d:DownEvent) ON (d.status)",
    "CREATE INDEX down_event_asset IF NOT EXISTS FOR (d:DownEvent) ON (d.asset_id)",
    "CREATE INDEX down_event_fault_id IF NOT EXISTS FOR (d:DownEvent) ON (d.fault_id)",
    "CREATE INDEX down_event_maintenance IF NOT EXISTS FOR (d:DownEvent) ON (d.maintenance_schedule_id)",
    "CREATE INDEX order_status IF NOT EXISTS FOR (o:Order) ON (o.status)",
    "CREATE INDEX order_type IF NOT EXISTS FOR (o:Order) ON (o.order_type)",
    "CREATE INDEX order_priority IF NOT EXISTS FOR (o:Order) ON (o.priority)",
    "CREATE INDEX order_maintenance_schedule IF NOT EXISTS FOR (o:Order) ON (o.maintenance_schedule_id)",
    "CREATE INDEX material_part_number IF NOT EXISTS FOR (m:Material) ON (m.part_number)",
    "CREATE INDEX material_order_id IF NOT EXISTS FOR (m:Material) ON (m.order_id)",
    "CREATE INDEX location_type IF NOT EXISTS FOR (l:Location) ON (l.location_type)",
    "CREATE INDEX location_parent IF NOT EXISTS FOR (l:Location) ON (l.parent_id)",
    "CREATE INDEX level_rank IF NOT EXISTS FOR (l:Level) ON (l.rank)",
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
    ("CREATE FULLTEXT INDEX worker_name_search IF NOT EXISTS FOR (w:Worker) ON EACH [w.name]"),
    (
        "CREATE FULLTEXT INDEX task_name_search IF NOT EXISTS "
        "FOR (t:Task) ON EACH [t.name, t.description]"
    ),
    (
        "CREATE FULLTEXT INDEX cause_name_search IF NOT EXISTS "
        "FOR (c:Cause) ON EACH [c.name, c.description]"
    ),
    (
        "CREATE FULLTEXT INDEX order_title_search IF NOT EXISTS "
        "FOR (o:Order) ON EACH [o.title, o.description]"
    ),
    (
        "CREATE FULLTEXT INDEX location_name_search IF NOT EXISTS "
        "FOR (l:Location) ON EACH [l.name, l.description]"
    ),
    (
        "CREATE FULLTEXT INDEX sensor_name_search IF NOT EXISTS "
        "FOR (s:Sensor) ON EACH [s.name]"
    ),
    (
        "CREATE FULLTEXT INDEX material_name_search IF NOT EXISTS "
        "FOR (m:Material) ON EACH [m.name, m.description]"
    ),
    # GraphRAG indexes
    (
        "CREATE FULLTEXT INDEX doc_entity_name_search IF NOT EXISTS "
        "FOR (d:DocEntity) ON EACH [d.name, d.description]"
    ),
]

# Additional constraints and indexes for GraphRAG DocumentChunk and DocEntity nodes
GRAPHRAG_CONSTRAINTS = [
    (
        "CREATE CONSTRAINT document_chunk_id IF NOT EXISTS "
        "FOR (c:DocumentChunk) REQUIRE c.chunk_id IS UNIQUE"
    ),
    (
        "CREATE CONSTRAINT doc_entity_id IF NOT EXISTS "
        "FOR (e:DocEntity) REQUIRE e.entity_id IS UNIQUE"
    ),
]

GRAPHRAG_INDEXES = [
    "CREATE INDEX document_chunk_doc_id IF NOT EXISTS FOR (c:DocumentChunk) ON (c.document_id)",
    "CREATE INDEX doc_entity_type IF NOT EXISTS FOR (e:DocEntity) ON (e.entity_type)",
    "CREATE INDEX doc_entity_source IF NOT EXISTS FOR (e:DocEntity) ON (e.source_document_id)",
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

        for stmt in GRAPHRAG_CONSTRAINTS:
            await session.run(stmt)
        logger.info("Neo4j GraphRAG constraints created")

        for stmt in GRAPHRAG_INDEXES:
            await session.run(stmt)
        logger.info("Neo4j GraphRAG indexes created")

    logger.info("Neo4j schema initialization complete")
