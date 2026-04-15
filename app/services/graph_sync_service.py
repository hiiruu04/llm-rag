import asyncio
import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.neo4j import get_neo4j_driver
from app.models.action import Action
from app.models.aggregate import Aggregate
from app.models.asset import Asset
from app.models.cause import Cause
from app.models.competence import Competence
from app.models.down_event import DownEvent
from app.models.fault import Fault, fault_cause_effect
from app.models.graph_associations import (
    action_competence,
    asset_location,
    asset_system,
    asset_worker_assignment,
    cause_role,
    down_event_cause,
    order_asset,
    role_task,
    system_aggregate,
    task_competence,
    task_material,
    worker_competence,
    worker_shift,
)
from app.models.graph_sync_log import GraphSyncLog
from app.models.level import Level
from app.models.location import Location
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.material import Material
from app.models.order import Order
from app.models.role import Role
from app.models.sensor import Sensor
from app.models.shift import Shift
from app.models.system import System
from app.models.task import Task
from app.models.worker import Worker
from app.utils.neo4j_setup import setup_neo4j_schema

BATCH_SIZE = 500
MAX_RETRIES = 3
SYNC_LOCK_TIMEOUT_MINUTES = 10


def _row_to_neo4j_dict(row, columns: dict[str, str]) -> dict:
    result = {}
    for attr, neo_key in columns.items():
        val = getattr(row, attr, None)
        if isinstance(val, uuid.UUID):
            val = str(val)
        elif isinstance(val, datetime):
            val = val.isoformat() if val else None
        result[neo_key] = val
    return result


class GraphSyncService:
    async def _create_sync_log(self, sync_type: str) -> uuid.UUID:
        async with async_session_factory() as session:
            sync_log = GraphSyncLog(
                sync_type=sync_type,
                status="started",
                records_processed=0,
            )
            session.add(sync_log)
            await session.commit()
            await session.refresh(sync_log)
            return sync_log.id

    async def _update_sync_log(
        self,
        log_id: uuid.UUID,
        status: str,
        records: int = 0,
        error: str = None,
        meta: dict = None,
    ):
        async with async_session_factory() as session:
            sync_log = await session.get(GraphSyncLog, log_id)
            if sync_log:
                sync_log.status = status
                sync_log.records_processed = records
                sync_log.completed_at = datetime.now(timezone.utc)
                if error:
                    sync_log.error_message = error
                if meta:
                    sync_log.metadata_ = meta
                await session.commit()

    async def _acquire_sync_lock(self) -> bool:
        driver = await get_neo4j_driver()
        async with driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                "MERGE (s:SyncMetadata) "
                "ON CREATE SET s.sync_in_progress = false "
                "RETURN s.sync_in_progress AS sip, s.lock_acquired_at AS lat"
            )
            record = await result.single()

            if record and record["sip"]:
                lat = record["lat"]
                if lat:
                    from datetime import timedelta

                    lock_age = datetime.now(timezone.utc) - datetime.fromisoformat(str(lat))
                    if lock_age > timedelta(minutes=SYNC_LOCK_TIMEOUT_MINUTES):
                        logger.warning("Stale sync lock detected, clearing it")
                    else:
                        return False

            await session.run(
                "MATCH (s:SyncMetadata) "
                "SET s.sync_in_progress = true, s.lock_acquired_at = datetime()"
            )
            return True

    async def _release_sync_lock(self):
        driver = await get_neo4j_driver()
        async with driver.session(database=settings.neo4j_database) as session:
            await session.run(
                "MATCH (s:SyncMetadata) SET s.sync_in_progress = false, s.lock_acquired_at = null"
            )

    async def _run_batch_with_retry(self, session, cypher: str, batch: list[dict]):
        for attempt in range(MAX_RETRIES):
            try:
                await session.run(cypher, batch=batch)
                return
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait = 2**attempt
                    logger.warning(
                        f"Batch failed (attempt {attempt + 1}), retrying in {wait}s: {e}"
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

    async def full_sync(self) -> dict:
        log_id = await self._create_sync_log("full")

        if not await self._acquire_sync_lock():
            await self._update_sync_log(log_id, "failed", error="Sync already in progress")
            return {"status": "failed", "error": "Sync already in progress"}

        try:
            driver = await get_neo4j_driver()

            # Wipe Neo4j and recreate schema
            async with driver.session(database=settings.neo4j_database) as session:
                await session.run("MATCH (n) DETACH DELETE n")

            await setup_neo4j_schema()

            total_records = 0
            counts = {}

            # Load in dependency order
            counts["assets"] = await self._sync_assets(driver)
            counts["sensors"] = await self._sync_sensors(driver)
            counts["faults"] = await self._sync_faults(driver)
            counts["maintenance"] = await self._sync_maintenance(driver)
            counts["levels"] = await self._sync_levels(driver)
            counts["competences"] = await self._sync_competences(driver)
            counts["roles"] = await self._sync_roles(driver)
            counts["shifts"] = await self._sync_shifts(driver)
            counts["locations"] = await self._sync_locations(driver)
            counts["aggregates"] = await self._sync_aggregates(driver)
            counts["systems"] = await self._sync_systems(driver)
            counts["workers"] = await self._sync_workers(driver)
            counts["tasks"] = await self._sync_tasks(driver)
            counts["actions"] = await self._sync_actions(driver)
            counts["causes"] = await self._sync_causes(driver)
            counts["materials"] = await self._sync_materials(driver)
            counts["down_events"] = await self._sync_down_events(driver)
            counts["orders"] = await self._sync_orders(driver)

            # Relationships
            counts["parent_edges"] = await self._sync_parent_edges(driver)
            counts["sensor_edges"] = await self._sync_sensor_edges(driver)
            counts["fault_edges"] = await self._sync_fault_edges(driver)
            counts["maintenance_edges"] = await self._sync_maintenance_edges(driver)
            counts["cause_effect_edges"] = await self._sync_cause_effect_edges(driver)
            counts["fault_maintenance_edges"] = await self._sync_fault_maintenance_edges(driver)
            counts["assigned_to_edges"] = await self._sync_assigned_to_edges(driver)
            counts["worker_competence_edges"] = await self._sync_worker_competence_edges(driver)
            counts["worker_shift_edges"] = await self._sync_worker_shift_edges(driver)
            counts["task_competence_edges"] = await self._sync_task_competence_edges(driver)
            counts["task_material_edges"] = await self._sync_task_material_edges(driver)
            counts["cause_role_edges"] = await self._sync_cause_role_edges(driver)
            counts["role_task_edges"] = await self._sync_role_task_edges(driver)
            counts["action_competence_edges"] = await self._sync_action_competence_edges(driver)
            counts["asset_system_edges"] = await self._sync_asset_system_edges(driver)
            counts["system_aggregate_edges"] = await self._sync_system_aggregate_edges(driver)
            counts["down_event_cause_edges"] = await self._sync_down_event_cause_edges(driver)
            counts["order_asset_edges"] = await self._sync_order_asset_edges(driver)
            counts["asset_location_edges"] = await self._sync_asset_location_edges(driver)

            total_records = sum(counts.values())

            # Write SyncMetadata
            async with driver.session(database=settings.neo4j_database) as session:
                await session.run(
                    "MERGE (s:SyncMetadata) "
                    "SET s.last_full_sync = datetime(), "
                    "s.last_incremental_sync = datetime(), "
                    "s.total_assets = $ta, s.total_sensors = $ts, "
                    "s.total_faults = $tf, s.total_schedules = $tms, "
                    "s.total_workers = $tw, s.total_roles = $tr, "
                    "s.total_competences = $tc, s.total_levels = $tlv, "
                    "s.total_tasks = $tt, s.total_causes = $tca, "
                    "s.total_down_events = $tde, s.total_orders = $to2, "
                    "s.total_locations = $tlo, s.total_systems = $tsy, "
                    "s.total_aggregates = $tag, "
                    "s.sync_in_progress = false, s.lock_acquired_at = null",
                    ta=counts["assets"],
                    ts=counts["sensors"],
                    tf=counts["faults"],
                    tms=counts["maintenance"],
                    tw=counts["workers"],
                    tr=counts["roles"],
                    tc=counts["competences"],
                    tlv=counts["levels"],
                    tt=counts["tasks"],
                    tca=counts["causes"],
                    tde=counts["down_events"],
                    to2=counts["orders"],
                    tlo=counts["locations"],
                    tsy=counts["systems"],
                    tag=counts["aggregates"],
                )

            await self._update_sync_log(log_id, "completed", total_records, meta=counts)
            logger.info(f"Full sync completed: {counts}")
            return {"status": "completed", "records_processed": total_records, "counts": counts}

        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            await self._release_sync_lock()
            await self._update_sync_log(log_id, "failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    async def incremental_sync(self) -> dict:
        log_id = await self._create_sync_log("incremental")

        if not await self._acquire_sync_lock():
            await self._update_sync_log(log_id, "failed", error="Sync already in progress")
            return {"status": "failed", "error": "Sync already in progress"}

        try:
            driver = await get_neo4j_driver()

            # Get last sync timestamp
            async with driver.session(database=settings.neo4j_database) as session:
                result = await session.run(
                    "MATCH (s:SyncMetadata) RETURN s.last_incremental_sync AS lis"
                )
                record = await result.single()
                last_sync = record["lis"] if record and record["lis"] else None

            if not last_sync:
                logger.info("No previous sync found, falling back to full sync")
                await self._release_sync_lock()
                return await self.full_sync()

            total_records = 0
            counts = {}

            # Upsert modified records
            counts["assets"] = await self._sync_assets(driver, since=last_sync)
            counts["sensors"] = await self._sync_sensors(driver, since=last_sync)
            counts["faults"] = await self._sync_faults(driver, since=last_sync)
            counts["maintenance"] = await self._sync_maintenance(driver, since=last_sync)
            counts["levels"] = await self._sync_levels(driver, since=last_sync)
            counts["competences"] = await self._sync_competences(driver, since=last_sync)
            counts["roles"] = await self._sync_roles(driver, since=last_sync)
            counts["shifts"] = await self._sync_shifts(driver, since=last_sync)
            counts["locations"] = await self._sync_locations(driver, since=last_sync)
            counts["aggregates"] = await self._sync_aggregates(driver, since=last_sync)
            counts["systems"] = await self._sync_systems(driver, since=last_sync)
            counts["workers"] = await self._sync_workers(driver, since=last_sync)
            counts["tasks"] = await self._sync_tasks(driver, since=last_sync)
            counts["actions"] = await self._sync_actions(driver, since=last_sync)
            counts["causes"] = await self._sync_causes(driver, since=last_sync)
            counts["materials"] = await self._sync_materials(driver, since=last_sync)
            counts["down_events"] = await self._sync_down_events(driver, since=last_sync)
            counts["orders"] = await self._sync_orders(driver, since=last_sync)

            # Refresh edges for modified records
            counts["parent_edges"] = await self._sync_parent_edges(driver, since=last_sync)
            counts["sensor_edges"] = await self._sync_sensor_edges(driver, since=last_sync)
            counts["fault_edges"] = await self._sync_fault_edges(driver, since=last_sync)
            counts["maintenance_edges"] = await self._sync_maintenance_edges(
                driver, since=last_sync
            )
            counts["cause_effect_edges"] = await self._sync_cause_effect_edges(driver)
            counts["fault_maintenance_edges"] = await self._sync_fault_maintenance_edges(
                driver, since=last_sync
            )
            counts["assigned_to_edges"] = await self._sync_assigned_to_edges(driver)
            counts["worker_competence_edges"] = await self._sync_worker_competence_edges(driver)
            counts["worker_shift_edges"] = await self._sync_worker_shift_edges(driver)
            counts["task_competence_edges"] = await self._sync_task_competence_edges(driver)
            counts["task_material_edges"] = await self._sync_task_material_edges(driver)
            counts["cause_role_edges"] = await self._sync_cause_role_edges(driver)
            counts["role_task_edges"] = await self._sync_role_task_edges(driver)
            counts["action_competence_edges"] = await self._sync_action_competence_edges(driver)
            counts["asset_system_edges"] = await self._sync_asset_system_edges(driver)
            counts["system_aggregate_edges"] = await self._sync_system_aggregate_edges(driver)
            counts["down_event_cause_edges"] = await self._sync_down_event_cause_edges(driver)
            counts["order_asset_edges"] = await self._sync_order_asset_edges(driver)
            counts["asset_location_edges"] = await self._sync_asset_location_edges(driver)

            # Delete nodes that were removed from PostgreSQL
            counts["deleted"] = await self._sync_deletions(driver)

            total_records = sum(counts.values())

            # Update SyncMetadata
            async with driver.session(database=settings.neo4j_database) as session:
                await session.run(
                    "MATCH (s:SyncMetadata) "
                    "SET s.last_incremental_sync = datetime(), s.sync_in_progress = false, "
                    "s.lock_acquired_at = null"
                )

            await self._update_sync_log(log_id, "completed", total_records, meta=counts)
            logger.info(f"Incremental sync completed: {counts}")
            return {"status": "completed", "records_processed": total_records, "counts": counts}

        except Exception as e:
            logger.error(f"Incremental sync failed: {e}")
            await self._release_sync_lock()
            await self._update_sync_log(log_id, "failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    async def _fetch_pg_rows(self, model_class, since=None):
        async with async_session_factory() as session:
            stmt = select(model_class).order_by(model_class.created_at)
            if since:
                stmt = stmt.where(model_class.updated_at > since)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def _sync_assets(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Asset, since)
        if not rows:
            return 0

        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "asset_type": "asset_type",
            "status": "status",
            "location": "location",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (a:Asset {pg_id: row.pg_id}) "
            "SET a.name = row.name, a.description = row.description, "
            "a.asset_type = row.asset_type, a.status = row.status, "
            "a.location = row.location, a.created_at = row.created_at, "
            "a.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_sensors(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Sensor, since)
        if not rows:
            return 0

        columns = {
            "id": "pg_id",
            "name": "name",
            "sensor_type": "sensor_type",
            "unit": "unit",
            "status": "status",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (s:Sensor {pg_id: row.pg_id}) "
            "SET s.name = row.name, s.sensor_type = row.sensor_type, "
            "s.unit = row.unit, s.status = row.status, "
            "s.created_at = row.created_at, s.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_faults(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Fault, since)
        if not rows:
            return 0

        columns = {
            "id": "pg_id",
            "code": "code",
            "name": "name",
            "description": "description",
            "severity": "severity",
            "status": "status",
            "detected_at": "detected_at",
            "resolved_at": "resolved_at",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (f:Fault {pg_id: row.pg_id}) "
            "SET f.code = row.code, f.name = row.name, "
            "f.description = row.description, f.severity = row.severity, "
            "f.status = row.status, f.detected_at = row.detected_at, "
            "f.resolved_at = row.resolved_at, f.created_at = row.created_at, "
            "f.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_maintenance(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(MaintenanceSchedule, since)
        if not rows:
            return 0

        columns = {
            "id": "pg_id",
            "title": "title",
            "description": "description",
            "maintenance_type": "maintenance_type",
            "status": "status",
            "priority": "priority",
            "scheduled_date": "scheduled_date",
            "completed_date": "completed_date",
            "assigned_to": "assigned_to",
            "recurrence": "recurrence",
            "estimated_duration_hours": "estimated_duration_hours",
            "notes": "notes",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (m:MaintenanceSchedule {pg_id: row.pg_id}) "
            "SET m.title = row.title, m.description = row.description, "
            "m.maintenance_type = row.maintenance_type, m.status = row.status, "
            "m.priority = row.priority, m.scheduled_date = row.scheduled_date, "
            "m.completed_date = row.completed_date, m.assigned_to = row.assigned_to, "
            "m.recurrence = row.recurrence, "
            "m.estimated_duration_hours = row.estimated_duration_hours, "
            "m.notes = row.notes, m.created_at = row.created_at, "
            "m.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_levels(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Level, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "rank": "rank",
            "description": "description",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (l:Level {pg_id: row.pg_id}) "
            "SET l.name = row.name, l.rank = row.rank, "
            "l.description = row.description, l.created_at = row.created_at, "
            "l.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_competences(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Competence, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "category": "category",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (c:Competence {pg_id: row.pg_id}) "
            "SET c.name = row.name, c.description = row.description, "
            "c.category = row.category, c.created_at = row.created_at, "
            "c.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_roles(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Role, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (r:Role {pg_id: row.pg_id}) "
            "SET r.name = row.name, r.description = row.description, "
            "r.created_at = row.created_at, r.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_shifts(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Shift, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "start_time": "start_time",
            "end_time": "end_time",
            "description": "description",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (s:Shift {pg_id: row.pg_id}) "
            "SET s.name = row.name, s.start_time = row.start_time, "
            "s.end_time = row.end_time, s.description = row.description, "
            "s.created_at = row.created_at, s.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_locations(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Location, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "location_type": "location_type",
            "parent_id": "parent_id",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (l:Location {pg_id: row.pg_id}) "
            "SET l.name = row.name, l.description = row.description, "
            "l.location_type = row.location_type, l.parent_id = row.parent_id, "
            "l.created_at = row.created_at, l.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_aggregates(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Aggregate, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (a:Aggregate {pg_id: row.pg_id}) "
            "SET a.name = row.name, a.description = row.description, "
            "a.created_at = row.created_at, a.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_systems(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(System, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (s:System {pg_id: row.pg_id}) "
            "SET s.name = row.name, s.description = row.description, "
            "s.created_at = row.created_at, s.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_workers(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Worker, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "employee_id": "employee_id",
            "email": "email",
            "phone": "phone",
            "status": "status",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (w:Worker {pg_id: row.pg_id}) "
            "SET w.name = row.name, w.employee_id = row.employee_id, "
            "w.email = row.email, w.phone = row.phone, w.status = row.status, "
            "w.created_at = row.created_at, w.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_tasks(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Task, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "task_type": "task_type",
            "status": "status",
            "estimated_duration_hours": "estimated_duration_hours",
            "doc_link": "doc_link",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (t:Task {pg_id: row.pg_id}) "
            "SET t.name = row.name, t.description = row.description, "
            "t.task_type = row.task_type, t.status = row.status, "
            "t.estimated_duration_hours = row.estimated_duration_hours, "
            "t.doc_link = row.doc_link, t.created_at = row.created_at, "
            "t.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_actions(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Action, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "action_type": "action_type",
            "sequence_order": "sequence_order",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (a:Action {pg_id: row.pg_id}) "
            "SET a.name = row.name, a.description = row.description, "
            "a.action_type = row.action_type, a.sequence_order = row.sequence_order, "
            "a.created_at = row.created_at, a.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_causes(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Cause, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "description": "description",
            "category": "category",
            "severity": "severity",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (c:Cause {pg_id: row.pg_id}) "
            "SET c.name = row.name, c.description = row.description, "
            "c.category = row.category, c.severity = row.severity, "
            "c.created_at = row.created_at, c.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_materials(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Material, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "name": "name",
            "part_number": "part_number",
            "description": "description",
            "quantity_in_stock": "quantity_in_stock",
            "unit": "unit",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (m:Material {pg_id: row.pg_id}) "
            "SET m.name = row.name, m.part_number = row.part_number, "
            "m.description = row.description, m.quantity_in_stock = row.quantity_in_stock, "
            "m.unit = row.unit, m.created_at = row.created_at, "
            "m.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_down_events(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(DownEvent, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "asset_id": "asset_id",
            "started_at": "started_at",
            "ended_at": "ended_at",
            "downtime_minutes": "downtime_minutes",
            "description": "description",
            "severity": "severity",
            "status": "status",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (d:DownEvent {pg_id: row.pg_id}) "
            "SET d.asset_id = row.asset_id, d.started_at = row.started_at, "
            "d.ended_at = row.ended_at, d.downtime_minutes = row.downtime_minutes, "
            "d.description = row.description, d.severity = row.severity, "
            "d.status = row.status, d.created_at = row.created_at, "
            "d.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_orders(self, driver, since=None) -> int:
        rows = await self._fetch_pg_rows(Order, since)
        if not rows:
            return 0
        columns = {
            "id": "pg_id",
            "order_number": "order_number",
            "title": "title",
            "description": "description",
            "order_type": "order_type",
            "status": "status",
            "priority": "priority",
            "requested_date": "requested_date",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        cypher = (
            "UNWIND $batch AS row "
            "MERGE (o:Order {pg_id: row.pg_id}) "
            "SET o.order_number = row.order_number, o.title = row.title, "
            "o.description = row.description, o.order_type = row.order_type, "
            "o.status = row.status, o.priority = row.priority, "
            "o.requested_date = row.requested_date, o.created_at = row.created_at, "
            "o.updated_at = row.updated_at"
        )
        return await self._write_batches(driver, rows, columns, cypher)

    async def _sync_parent_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            stmt = select(Asset).where(Asset.parent_id.isnot(None))
            if since:
                stmt = stmt.where(Asset.updated_at > since)
            result = await session.execute(stmt)
            rows = result.scalars().all()

        if not rows:
            return 0

        cypher = (
            "UNWIND $batch AS row "
            "MATCH (child:Asset {pg_id: row.child_id}) "
            "MATCH (parent:Asset {pg_id: row.parent_id}) "
            "MERGE (child)-[:HAS_PARENT]->(parent)"
        )
        batch = [{"child_id": str(r.id), "parent_id": str(r.parent_id)} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_sensor_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            stmt = select(Sensor)
            if since:
                stmt = stmt.where(Sensor.updated_at > since)
            result = await session.execute(stmt)
            rows = result.scalars().all()

        if not rows:
            return 0

        cypher = (
            "UNWIND $batch AS row "
            "MATCH (a:Asset {pg_id: row.asset_id}) "
            "MATCH (s:Sensor {pg_id: row.sensor_id}) "
            "MERGE (a)-[:HAS_SENSOR]->(s)"
        )
        batch = [{"asset_id": str(r.asset_id), "sensor_id": str(r.id)} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_fault_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            stmt = select(Fault)
            if since:
                stmt = stmt.where(Fault.updated_at > since)
            result = await session.execute(stmt)
            rows = result.scalars().all()

        if not rows:
            return 0

        cypher = (
            "UNWIND $batch AS row "
            "MATCH (a:Asset {pg_id: row.asset_id}) "
            "MATCH (f:Fault {pg_id: row.fault_id}) "
            "MERGE (a)-[:HAS_FAULT]->(f)"
        )
        batch = [{"asset_id": str(r.asset_id), "fault_id": str(r.id)} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_maintenance_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            stmt = select(MaintenanceSchedule)
            if since:
                stmt = stmt.where(MaintenanceSchedule.updated_at > since)
            result = await session.execute(stmt)
            rows = result.scalars().all()

        if not rows:
            return 0

        cypher = (
            "UNWIND $batch AS row "
            "MATCH (a:Asset {pg_id: row.asset_id}) "
            "MATCH (m:MaintenanceSchedule {pg_id: row.maintenance_id}) "
            "MERGE (a)-[:HAS_MAINTENANCE]->(m)"
        )
        batch = [{"asset_id": str(r.asset_id), "maintenance_id": str(r.id)} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_cause_effect_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(fault_cause_effect))
            rows = result.fetchall()

        if not rows:
            return 0

        cypher = (
            "UNWIND $batch AS row "
            "MATCH (causing:Fault {pg_id: row.causing_id}) "
            "MATCH (affected:Fault {pg_id: row.affected_id}) "
            "MERGE (causing)-[:CAUSES]->(affected)"
        )
        batch = [{"causing_id": str(r[0]), "affected_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_fault_maintenance_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            stmt = select(MaintenanceSchedule).where(MaintenanceSchedule.fault_id.isnot(None))
            if since:
                stmt = stmt.where(MaintenanceSchedule.updated_at > since)
            result = await session.execute(stmt)
            rows = result.scalars().all()

        if not rows:
            return 0

        cypher = (
            "UNWIND $batch AS row "
            "MATCH (m:MaintenanceSchedule {pg_id: row.maintenance_id}) "
            "MATCH (f:Fault {pg_id: row.fault_id}) "
            "MERGE (m)-[:ADDRESSES_FAULT]->(f)"
        )
        batch = [{"maintenance_id": str(r.id), "fault_id": str(r.fault_id)} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_assigned_to_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(asset_worker_assignment))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (a:Asset {pg_id: row.asset_id}) "
            "MATCH (w:Worker {pg_id: row.worker_id}) "
            "MERGE (a)-[:assigned_to]->(w)"
        )
        batch = [{"asset_id": str(r[0]), "worker_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_worker_competence_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(worker_competence))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (w:Worker {pg_id: row.worker_id}) "
            "MATCH (c:Competence {pg_id: row.competence_id}) "
            "MERGE (w)-[:has]->(c)"
        )
        batch = [{"worker_id": str(r[0]), "competence_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_worker_shift_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(worker_shift))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (w:Worker {pg_id: row.worker_id}) "
            "MATCH (s:Shift {pg_id: row.shift_id}) "
            "MERGE (w)-[:works_in]->(s)"
        )
        batch = [{"worker_id": str(r[0]), "shift_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_task_competence_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(task_competence))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (t:Task {pg_id: row.task_id}) "
            "MATCH (c:Competence {pg_id: row.competence_id}) "
            "MERGE (t)-[:requires]->(c)"
        )
        batch = [{"task_id": str(r[0]), "competence_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_task_material_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(task_material))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (m:Material {pg_id: row.material_id}) "
            "MATCH (t:Task {pg_id: row.task_id}) "
            "MERGE (m)-[:planned_in]->(t)"
        )
        batch = [{"task_id": str(r[0]), "material_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_cause_role_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(cause_role))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (c:Cause {pg_id: row.cause_id}) "
            "MATCH (r:Role {pg_id: row.role_id}) "
            "MERGE (c)-[:requires]->(r)"
        )
        batch = [{"cause_id": str(r[0]), "role_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_role_task_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(role_task))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (r:Role {pg_id: row.role_id}) "
            "MATCH (t:Task {pg_id: row.task_id}) "
            "MERGE (r)-[:enables]->(t)"
        )
        batch = [{"role_id": str(r[0]), "task_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_action_competence_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(action_competence))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (a:Action {pg_id: row.action_id}) "
            "MATCH (c:Competence {pg_id: row.competence_id}) "
            "MERGE (a)-[:requires]->(c)"
        )
        batch = [{"action_id": str(r[0]), "competence_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_asset_system_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(asset_system))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (a:Asset {pg_id: row.asset_id}) "
            "MATCH (s:System {pg_id: row.system_id}) "
            "MERGE (a)-[:consists_of]->(s)"
        )
        batch = [{"asset_id": str(r[0]), "system_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_system_aggregate_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(system_aggregate))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (s:System {pg_id: row.system_id}) "
            "MATCH (a:Aggregate {pg_id: row.aggregate_id}) "
            "MERGE (s)-[:part_of]->(a)"
        )
        batch = [{"system_id": str(r[0]), "aggregate_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_down_event_cause_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(down_event_cause))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (d:DownEvent {pg_id: row.down_event_id}) "
            "MATCH (c:Cause {pg_id: row.cause_id}) "
            "MERGE (d)-[:has]->(c)"
        )
        batch = [{"down_event_id": str(r[0]), "cause_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_order_asset_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(order_asset))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (o:Order {pg_id: row.order_id}) "
            "MATCH (a:Asset {pg_id: row.asset_id}) "
            "MERGE (o)-[:booked_on]->(a)"
        )
        batch = [{"order_id": str(r[0]), "asset_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_asset_location_edges(self, driver, since=None) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(asset_location))
            rows = result.fetchall()
        if not rows:
            return 0
        cypher = (
            "UNWIND $batch AS row "
            "MATCH (a:Asset {pg_id: row.asset_id}) "
            "MATCH (l:Location {pg_id: row.location_id}) "
            "MERGE (a)-[:is_at]->(l)"
        )
        batch = [{"asset_id": str(r[0]), "location_id": str(r[1])} for r in rows]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_deletions(self, driver) -> int:
        """Remove Neo4j nodes that no longer exist in PostgreSQL."""
        deleted = 0
        for model_class, label in [
            (Asset, "Asset"),
            (Sensor, "Sensor"),
            (Fault, "Fault"),
            (MaintenanceSchedule, "MaintenanceSchedule"),
            (Worker, "Worker"),
            (Role, "Role"),
            (Competence, "Competence"),
            (Level, "Level"),
            (Task, "Task"),
            (Action, "Action"),
            (Cause, "Cause"),
            (Material, "Material"),
            (Shift, "Shift"),
            (DownEvent, "DownEvent"),
            (Order, "Order"),
            (Location, "Location"),
            (System, "System"),
            (Aggregate, "Aggregate"),
        ]:
            async with async_session_factory() as pg_session:
                result = await pg_session.execute(select(model_class.id))
                pg_ids = {str(r[0]) for r in result.fetchall()}

            async with driver.session(database=settings.neo4j_database) as neo_session:
                result = await neo_session.run(f"MATCH (n:{label}) RETURN n.pg_id AS pg_id")
                records = await result.data()
                neo_ids = {r["pg_id"] for r in records}
                to_delete = neo_ids - pg_ids

                if to_delete:
                    cypher = (
                        f"UNWIND $batch AS pg_id "
                        f"MATCH (n:{label} {{pg_id: pg_id}}) DETACH DELETE n"
                    )
                    await neo_session.run(cypher, batch=list(to_delete))
                    deleted += len(to_delete)

        return deleted

    async def _write_batches(self, driver, rows, columns: dict, cypher: str) -> int:
        count = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = [_row_to_neo4j_dict(r, columns) for r in rows[i : i + BATCH_SIZE]]
            async with driver.session(database=settings.neo4j_database) as session:
                await self._run_batch_with_retry(session, cypher, batch)
            count += len(batch)
        return count

    async def _write_raw_batches(self, driver, batch: list[dict], cypher: str) -> int:
        count = 0
        for i in range(0, len(batch), BATCH_SIZE):
            chunk = batch[i : i + BATCH_SIZE]
            async with driver.session(database=settings.neo4j_database) as session:
                await self._run_batch_with_retry(session, cypher, chunk)
            count += len(chunk)
        return count

    async def get_sync_status(self) -> dict:
        driver = await get_neo4j_driver()
        async with driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                "MATCH (s:SyncMetadata) "
                "RETURN s.last_full_sync AS lfs, s.last_incremental_sync AS lis, "
                "s.sync_in_progress AS sip, s.total_assets AS ta, "
                "s.total_sensors AS ts, s.total_faults AS tf, "
                "s.total_schedules AS tms, "
                "s.total_workers AS tw, s.total_roles AS tr, "
                "s.total_competences AS tc, s.total_levels AS tlv, "
                "s.total_tasks AS tt, s.total_causes AS tca, "
                "s.total_down_events AS tde, s.total_orders AS to2, "
                "s.total_locations AS tlo, s.total_systems AS tsy, "
                "s.total_aggregates AS tag"
            )
            record = await result.single()

        if not record:
            return {
                "synced": False,
                "sync_in_progress": False,
            }

        return {
            "synced": True,
            "last_full_sync": str(record["lfs"]) if record["lfs"] else None,
            "last_incremental_sync": str(record["lis"]) if record["lis"] else None,
            "sync_in_progress": record["sip"],
            "total_assets": record["ta"],
            "total_sensors": record["ts"],
            "total_faults": record["tf"],
            "total_schedules": record["tms"],
            "total_workers": record["tw"],
            "total_roles": record["tr"],
            "total_competences": record["tc"],
            "total_levels": record["tlv"],
            "total_tasks": record["tt"],
            "total_causes": record["tca"],
            "total_down_events": record["tde"],
            "total_orders": record["to2"],
            "total_locations": record["tlo"],
            "total_systems": record["tsy"],
            "total_aggregates": record["tag"],
        }


_graph_sync_service: GraphSyncService | None = None


def get_graph_sync_service() -> GraphSyncService:
    global _graph_sync_service
    if _graph_sync_service is None:
        _graph_sync_service = GraphSyncService()
    return _graph_sync_service
