# Model Improvements & Knowledge Graph Stitching

## Overview

Two structural changes to the domain model and knowledge graph:

1. **Fault -> DownEvent relationship**: Add `HAS_OCCURRED` relationship from Fault to DownEvent
2. **Delete Action model**: Merge Action into MaintenanceSchedule

---

## Change 1: Fault -[HAS_OCCURRED]-> DownEvent

### Rationale

DownEvents previously only linked to Asset and Cause. In the CMMS domain, faults cause down events -- the graph should express `(Fault)-[:HAS_OCCURRED]->(DownEvent)` so queries can traverse from a fault to its resulting downtime.

### What changed

- **DownEvent model** (`app/models/down_event.py`): Added `fault_id` FK column pointing to `faults.id` (nullable, SET NULL on delete) and a `fault` relationship.
- **Fault model** (`app/models/fault.py`): Added `down_events` back-reference.
- **Schemas** (`app/models/schemas.py`): Added `fault_id` to `DownEventCreate`, `DownEventUpdate`, and `DownEventResponse`.
- **Seed data** (`scripts/seed_db.py`): Linked specific down events to faults (e.g., "Boiler emergency shutdown" -> fault B-TL-001, "Turbine vibration trip" -> fault T-BV-001, "Boiler low water level trip" -> fault B-LW-001).
- **Graph sync** (`app/services/graph_sync_service.py`): `fault_id` included in DownEvent node properties; new `_sync_fault_down_event_edges()` method creates `(Fault)-[:HAS_OCCURRED]->(DownEvent)` relationships.
- **Cypher generator** (`app/services/cypher_generator.py`): Added `(Fault)-[:HAS_OCCURRED]->(DownEvent)` relationship and `fault_id` property to GRAPH_SCHEMA.
- **Cypher templates** (`app/services/cypher_templates.py`): `down_event_analysis` now traverses from Fault to DownEvent, returning `fault_code` and `fault_name`.
- **Neo4j setup** (`app/utils/neo4j_setup.py`): Added index on `DownEvent.fault_id`.
- **Graph resources** (`app/mcp/resources/graph_resources.py`): Added HAS_OCCURRED relationship and `fault_id` property to schema description.

### New graph traversal

```cypher
MATCH (f:Fault)-[:HAS_OCCURRED]->(de:DownEvent)
RETURN f.code, f.name, de.started_at, de.downtime_minutes
```

---

## Change 2: Delete Action, Merge into MaintenanceSchedule

### Rationale

Action and MaintenanceSchedule represent the same domain concept -- a maintenance action/task. Action had `name`, `description`, `action_type`, `sequence_order` fields and a relationship to Competence. MaintenanceSchedule already has richer fields. We absorb Action's unique fields into MaintenanceSchedule and delete Action entirely.

### What changed

- **MaintenanceSchedule model** (`app/models/maintenance_schedule.py`): Added `action_type` (String(100), default "standard") and `sequence_order` (Integer, default 0) columns.
- **Association table** (`app/models/graph_associations.py`): Renamed `action_competence` to `maintenance_competence` with FK to `maintenance_schedules.id`.
- **Deleted files**:
  - `app/models/action.py`
  - `app/services/action_service.py`
  - `app/api/routes/actions.py`
- **Schemas** (`app/models/schemas.py`): Removed `ActionCreate`, `ActionUpdate`, `ActionResponse`. Added `action_type` and `sequence_order` to MaintenanceSchedule schemas.
- **Models init** (`app/models/__init__.py`): Removed `Action` and `action_competence`, added `maintenance_competence`.
- **Main app** (`app/main.py`): Removed actions router.
- **Seed data** (`scripts/seed_db.py`): Removed `seed_actions()`. Updated `seed_associations()` to link MaintenanceSchedule -> Competence via `maintenance_competence` table.
- **Graph sync** (`app/services/graph_sync_service.py`): Removed `_sync_actions()`, renamed `_sync_action_competence_edges()` to `_sync_maintenance_competence_edges()` using `(MaintenanceSchedule)-[:REQUIRES_COMPETENCE]->(Competence)`, added `action_type` and `sequence_order` to MaintenanceSchedule sync, removed Action from deletions sync.
- **Cypher generator** (`app/services/cypher_generator.py`): Removed Action node, replaced `(Action)-[:requires]->(Competence)` with `(MaintenanceSchedule)-[:REQUIRES_COMPETENCE]->(Competence)`.
- **Neo4j setup** (`app/utils/neo4j_setup.py`): Removed `action_pg_id` constraint.
- **Graph resources** (`app/mcp/resources/graph_resources.py`): Removed Action node, updated relationship to MaintenanceSchedule.
- **Alembic env** (`alembic/env.py`): Updated imports.

### New graph traversal

```cypher
MATCH (m:MaintenanceSchedule)-[:REQUIRES_COMPETENCE]->(c:Competence)
RETURN m.title, c.name
```

---

## Updated Graph Schema Summary

### Node labels
Asset, Sensor, Fault, MaintenanceSchedule, Worker, Role, Competence, Level, Task, Cause, Material, Shift, DownEvent, Order, Location, System, Aggregate

### Key relationships (new/changed)
- `(Fault)-[:HAS_OCCURRED]->(DownEvent)` -- NEW
- `(MaintenanceSchedule)-[:REQUIRES_COMPETENCE]->(Competence)` -- RENAMED from Action
