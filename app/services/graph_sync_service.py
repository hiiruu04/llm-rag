import asyncio
import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select, text

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.neo4j import get_neo4j_driver
from app.models.asset import Asset
from app.models.fault import Fault, fault_cause_effect
from app.models.graph_sync_log import GraphSyncLog
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.sensor import Sensor
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
                    wait = 2 ** attempt
                    logger.warning(
                        f"Batch failed (attempt {attempt + 1}), "
                        f"retrying in {wait}s: {e}"
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

            # Relationships
            counts["parent_edges"] = await self._sync_parent_edges(driver)
            counts["sensor_edges"] = await self._sync_sensor_edges(driver)
            counts["fault_edges"] = await self._sync_fault_edges(driver)
            counts["maintenance_edges"] = await self._sync_maintenance_edges(driver)
            counts["cause_effect_edges"] = await self._sync_cause_effect_edges(driver)
            counts["fault_maintenance_edges"] = await self._sync_fault_maintenance_edges(driver)

            # Sensor summaries
            counts["sensor_summaries"] = await self._sync_sensor_summaries(driver)

            total_records = sum(counts.values())

            # Write SyncMetadata
            async with driver.session(database=settings.neo4j_database) as session:
                await session.run(
                    "MERGE (s:SyncMetadata) "
                    "SET s.last_full_sync = datetime(), "
                    "s.last_incremental_sync = datetime(), "
                    "s.total_assets = $ta, s.total_sensors = $ts, "
                    "s.total_faults = $tf, s.total_schedules = $tms, "
                    "s.sync_in_progress = false, s.lock_acquired_at = null",
                    ta=counts["assets"],
                    ts=counts["sensors"],
                    tf=counts["faults"],
                    tms=counts["maintenance"],
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

            # Delete nodes that were removed from PostgreSQL
            counts["deleted"] = await self._sync_deletions(driver)

            # Recompute sensor summaries for modified sensors
            counts["sensor_summaries"] = await self._sync_sensor_summaries(driver, since=last_sync)

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
            "id": "pg_id", "name": "name", "description": "description",
            "asset_type": "asset_type", "status": "status", "location": "location",
            "created_at": "created_at", "updated_at": "updated_at",
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
            "id": "pg_id", "name": "name", "sensor_type": "sensor_type",
            "unit": "unit", "status": "status", "created_at": "created_at",
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
            "id": "pg_id", "code": "code", "name": "name",
            "description": "description", "severity": "severity",
            "status": "status", "detected_at": "detected_at",
            "resolved_at": "resolved_at", "created_at": "created_at",
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
            "id": "pg_id", "title": "title", "description": "description",
            "maintenance_type": "maintenance_type", "status": "status",
            "priority": "priority", "scheduled_date": "scheduled_date",
            "completed_date": "completed_date", "assigned_to": "assigned_to",
            "recurrence": "recurrence",
            "estimated_duration_hours": "estimated_duration_hours",
            "notes": "notes", "created_at": "created_at", "updated_at": "updated_at",
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
        batch = [
            {"causing_id": str(r[0]), "affected_id": str(r[1])}
            for r in rows
        ]
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
        batch = [
            {"maintenance_id": str(r.id), "fault_id": str(r.fault_id)}
            for r in rows
        ]
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_sensor_summaries(self, driver, since=None) -> int:
        """Compute aggregated sensor summaries from PostgreSQL and write to Neo4j."""
        # First, clear old summaries (for full sync or modified sensors)
        async with driver.session(database=settings.neo4j_database) as neo_session:
            if not since:
                await neo_session.run("MATCH (s:SensorSummary) DETACH DELETE s")

        # Compute summaries via SQL
        summary_sql = """
        WITH windows AS (
            SELECT
                s.id AS sensor_id,
                s.asset_id,
                '1h' AS window,
                date_trunc('hour', sd.timestamp) AS window_start,
                date_trunc('hour', sd.timestamp)
                    + interval '1 hour' AS window_end
            FROM sensors s
            JOIN sensor_data sd ON sd.sensor_id = s.id
            WHERE sd.timestamp >= now() - interval '24 hours'
            GROUP BY s.id, s.asset_id,
                date_trunc('hour', sd.timestamp)

            UNION ALL

            SELECT
                s.id AS sensor_id,
                s.asset_id,
                '6h' AS window,
                date_trunc('day', sd.timestamp)
                    + interval '6 hours'
                    * floor(extract(hour from sd.timestamp) / 6)
                    AS window_start,
                date_trunc('day', sd.timestamp)
                    + interval '6 hours'
                    * (floor(extract(hour from sd.timestamp) / 6) + 1)
                    AS window_end
            FROM sensors s
            JOIN sensor_data sd ON sd.sensor_id = s.id
            WHERE sd.timestamp >= now() - interval '7 days'
            GROUP BY s.id, s.asset_id,
                date_trunc('day', sd.timestamp),
                floor(extract(hour from sd.timestamp) / 6)

            UNION ALL

            SELECT
                s.id AS sensor_id,
                s.asset_id,
                '24h' AS window,
                date_trunc('day', sd.timestamp) AS window_start,
                date_trunc('day', sd.timestamp) + interval '1 day' AS window_end
            FROM sensors s
            JOIN sensor_data sd ON sd.sensor_id = s.id
            WHERE sd.timestamp >= now() - interval '30 days'
            GROUP BY s.id, s.asset_id, date_trunc('day', sd.timestamp)
        )
        SELECT
            w.sensor_id,
            w.window,
            w.window_start,
            w.window_end,
            avg(sd.value) AS avg_value,
            min(sd.value) AS min_value,
            max(sd.value) AS max_value,
            COALESCE(stddev(sd.value), 0) AS stddev,
            count(sd.value) AS sample_count,
            CASE WHEN EXISTS (
                SELECT 1 FROM sensor_data sd2
                WHERE sd2.sensor_id = w.sensor_id
                AND sd2.value > avg(sd.value) + 3 * COALESCE(stddev(sd.value), 0)
                OR sd2.value < avg(sd.value) - 3 * COALESCE(stddev(sd.value), 0)
            ) THEN true ELSE false END AS anomaly_flag
        FROM windows w
        JOIN sensor_data sd ON sd.sensor_id = w.sensor_id
            AND sd.timestamp >= w.window_start AND sd.timestamp < w.window_end
        GROUP BY w.sensor_id, w.window, w.window_start, w.window_end
        ORDER BY w.sensor_id, w.window, w.window_start
        """

        async with async_session_factory() as pg_session:
            result = await pg_session.execute(text(summary_sql))
            rows = result.fetchall()

        if not rows:
            return 0

        batch = []
        for r in rows:
            batch.append({
                "sensor_pg_id": str(r[0]),
                "window": r[1],
                "window_start": r[2].isoformat() if r[2] else None,
                "window_end": r[3].isoformat() if r[3] else None,
                "avg_value": float(r[4]) if r[4] else 0.0,
                "min_value": float(r[5]) if r[5] else 0.0,
                "max_value": float(r[6]) if r[6] else 0.0,
                "stddev": float(r[7]) if r[7] else 0.0,
                "sample_count": int(r[8]) if r[8] else 0,
                "anomaly_flag": bool(r[9]) if r[9] else False,
            })

        cypher = (
            "UNWIND $batch AS row "
            "MATCH (s:Sensor {pg_id: row.sensor_pg_id}) "
            "MERGE (sum:SensorSummary {"
            "sensor_pg_id: row.sensor_pg_id, window: row.window, "
            "window_start: row.window_start}) "
            "SET sum.window_end = row.window_end, "
            "sum.avg_value = row.avg_value, sum.min_value = row.min_value, "
            "sum.max_value = row.max_value, sum.stddev = row.stddev, "
            "sum.sample_count = row.sample_count, "
            "sum.anomaly_flag = row.anomaly_flag "
            "MERGE (s)-[:HAS_SUMMARY]->(sum)"
        )
        return await self._write_raw_batches(driver, batch, cypher)

    async def _sync_deletions(self, driver) -> int:
        """Remove Neo4j nodes that no longer exist in PostgreSQL."""
        deleted = 0
        for model_class, label in [
            (Asset, "Asset"), (Sensor, "Sensor"),
            (Fault, "Fault"), (MaintenanceSchedule, "MaintenanceSchedule"),
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
                "s.total_schedules AS tms"
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
        }


_graph_sync_service: GraphSyncService | None = None


def get_graph_sync_service() -> GraphSyncService:
    global _graph_sync_service
    if _graph_sync_service is None:
        _graph_sync_service = GraphSyncService()
    return _graph_sync_service
