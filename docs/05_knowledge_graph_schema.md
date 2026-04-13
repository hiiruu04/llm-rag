# Knowledge Graph Schema Design Document

## Overview

This document describes the knowledge graph schema for the LLM-RAG CMMS (Computerized Maintenance Management System). The schema models an industrial power plant environment with 15 entity node types connected by 14 relationship types (implemented as 13 many-to-many junction tables plus the existing fault cause-effect link). It enables rich queries across equipment, workforce, competencies, tasks, downtime events, and maintenance operations.

**Important terminology note:** In this system, `Asset` is the model name used to represent equipment. There is no separate `Equipment` model. Throughout the PostgreSQL schema and codebase, the `assets` table and `Asset` SQLAlchemy model serve the role that a domain expert would call "equipment."

---

## Graph Schema

### Node Types (15)

| Node | PostgreSQL Table | SQLAlchemy Model | Key Properties |
|------|-----------------|------------------|----------------|
| Asset (Equipment) | `assets` | `Asset` | id (UUID), name, description, asset_type, parent_id, location, status, created_at, updated_at |
| Worker | `workers` | `Worker` | id (UUID), name, employee_id, email, phone, status, created_at, updated_at |
| Role | `roles` | `Role` | id (UUID), name, description, created_at, updated_at |
| Competence | `competences` | `Competence` | id (UUID), name, description, category, created_at, updated_at |
| Level | `levels` | `Level` | id (UUID), name, rank, description, created_at, updated_at |
| Task | `tasks` | `Task` | id (UUID), name, description, task_type, status, estimated_duration_hours, doc_link, created_at, updated_at |
| Action | `actions` | `Action` | id (UUID), name, description, action_type, sequence_order, created_at, updated_at |
| Cause | `causes` | `Cause` | id (UUID), name, description, category, severity, created_at, updated_at |
| Material | `materials` | `Material` | id (UUID), name, part_number, description, quantity_in_stock, unit, created_at, updated_at |
| Shift | `shifts` | `Shift` | id (UUID), name, start_time, end_time, description, created_at, updated_at |
| DownEvent | `down_events` | `DownEvent` | id (UUID), asset_id (FK), started_at, ended_at, downtime_minutes, description, severity, status, created_at, updated_at |
| Order | `orders` | `Order` | id (UUID), order_number, title, description, order_type, status, priority, requested_date, created_at, updated_at |
| Location | `locations` | `Location` | id (UUID), name, description, location_type, parent_id (self-referential FK), created_at, updated_at |
| System | `systems` | `System` | id (UUID), name, description, created_at, updated_at |
| Aggregate | `aggregates` | `Aggregate` | id (UUID), name, description, created_at, updated_at |

### Pre-existing Node Types (from prior migrations)

| Node | PostgreSQL Table | SQLAlchemy Model | Key Properties |
|------|-----------------|------------------|----------------|
| Sensor | `sensors` | `Sensor` | id (UUID), asset_id (FK), name, sensor_type, unit, status |
| SensorData | `sensor_data` | `SensorData` | id (serial), sensor_id (FK), timestamp, value |
| Fault | `faults` | `Fault` | id (UUID), asset_id (FK), code, name, description, severity, status, detected_at, resolved_at |
| MaintenanceSchedule | `maintenance_schedules` | `MaintenanceSchedule` | id (UUID), asset_id (FK), fault_id (FK), title, description, maintenance_type, status, priority, scheduled_date, completed_date, assigned_to, recurrence, estimated_duration_hours, notes |

### Node Type Enumerations

| Node | Field | Allowed Values |
|------|-------|---------------|
| Asset | asset_type | `facility`, `boiler`, `pump`, `chamber`, `turbine`, `generator`, `cooling_system`, etc. |
| Asset | status | `active`, `inactive`, `maintenance`, `decommissioned` |
| Worker | status | `active`, `inactive`, `on_leave` |
| Task | task_type | `general`, `inspection`, `repair`, `installation`, `calibration` |
| Task | status | `pending`, `in_progress`, `completed`, `cancelled` |
| Action | action_type | `safety`, `preparation`, `inspection`, `repair`, `verification`, `documentation` |
| Cause | category | `mechanical`, `chemical`, `thermal`, `operational`, `electrical` |
| Cause | severity | `low`, `medium`, `high`, `critical` |
| DownEvent | severity | `low`, `medium`, `high`, `critical` |
| DownEvent | status | `active`, `resolved` |
| Order | order_type | `maintenance`, `repair`, `inspection`, `installation` |
| Order | status | `open`, `in_progress`, `completed`, `cancelled` |
| Order | priority | `low`, `medium`, `high`, `critical` |
| Location | location_type | `plant`, `building`, `room`, etc. |

---

## Relationship Types

### New Relationships (13 junction tables)

| Junction Table | From Entity | To Entity | Relationship | Extra Columns | Semantic Meaning |
|---|---|---|---|---|---|
| `asset_worker_assignment` | Asset | Worker | many-to-many | -- | Worker is assigned to operate/maintain the asset |
| `worker_competence` | Worker | Competence | many-to-many | `level_id` (FK to levels) | Worker possesses a competence at a given proficiency level |
| `worker_shift` | Worker | Shift | many-to-many | -- | Worker is assigned to a shift schedule |
| `task_competence` | Task | Competence | many-to-many | `level_id` (FK to levels) | Task requires a competence (optionally at a minimum level) |
| `task_material` | Task | Material | many-to-many | `quantity_required` | Task requires a material/spare part in a given quantity |
| `cause_role` | Cause | Role | many-to-many | -- | Resolving a cause requires a specific role |
| `role_task` | Role | Task | many-to-many | -- | Having a role enables performing certain tasks |
| `action_competence` | Action | Competence | many-to-many | -- | Performing an action requires a specific competence |
| `asset_system` | Asset | System | many-to-many | -- | Asset is part of or composed of engineering systems |
| `system_aggregate` | System | Aggregate | many-to-many | -- | System belongs to an aggregate functional group |
| `asset_location` | Asset | Location | many-to-many | -- | Asset is physically located at a location |
| `down_event_cause` | DownEvent | Cause | many-to-many | -- | Downtime event was caused by one or more root causes |
| `order_asset` | Order | Asset | many-to-many | -- | Work order is booked against one or more assets |

### Pre-existing Relationships

| Junction Table | From Entity | To Entity | Extra Columns | Semantic Meaning |
|---|---|---|---|---|
| `fault_cause_effect` | Fault (causing) | Fault (affected) | `link_type` | One fault causes or contributes to another |

### Foreign Key Relationships (one-to-many)

| Parent | Child | FK Column | Description |
|--------|-------|-----------|-------------|
| Asset | Asset | `parent_id` | Hierarchical asset tree (self-referential) |
| Asset | Sensor | `asset_id` | Sensors attached to an asset |
| Asset | Fault | `asset_id` | Faults detected on an asset |
| Asset | MaintenanceSchedule | `asset_id` | Maintenance scheduled for an asset |
| Asset | DownEvent | `asset_id` | Downtime events for an asset |
| Sensor | SensorData | `sensor_id` | Time-series readings from a sensor |
| Fault | MaintenanceSchedule | `fault_id` | Maintenance triggered by a fault |
| Location | Location | `parent_id` | Hierarchical location tree (self-referential, e.g., plant > building > room) |

---

## Entity-Relationship Diagram (Textual)

```
Aggregate
   ^  (system_aggregate)
   |
System
   ^  (asset_system)
   |
Asset (Equipment) ---- (asset_location) ---- Location (tree)
   |                                           ^
   +-- (asset_worker_assignment) -- Worker     |
   |                                 |  |
   |                          (worker_shift) Shift
   |                                 |
   |                          (worker_competence) -- Competence -- Level
   |                                                        ^
   +-- (order_asset) -- Order                  (task_competence)
   |                      |                                |
   |                      |                     (action_competence)
   |                      |                                |
   +-- DownEvent -- (down_event_cause) -- Cause -- (cause_role) -- Role
   |                                                          |
   +-- Fault -- (fault_cause_effect) -- Fault        (role_task)
   |                                                          |
   +-- Sensor --> SensorData                       Task -- (task_material) -- Material
   |
   +-- MaintenanceSchedule (-> Fault)
```

---

## Key Graph Traversal Paths

### 1. Workforce Competency Path

```
Asset -[asset_worker_assignment]-> Worker -[worker_competence]-> Competence -[worker_competence.level_id]-> Level
Worker -[worker_shift]-> Shift
```

**Query example:** "What competences does the operator assigned to the Feed Water Pump have, and at what level? What shift are they on?"

### 2. Task Requirements Path

```
Task -[task_competence]-> Competence
Task -[task_material]-> Material
Role -[role_task]-> Task
Action -[action_competence]-> Competence
```

**Query example:** "What competences and materials does the Bearing Replacement task require? Which actions need which competences?"

### 3. Downtime Analysis Path

```
DownEvent -[down_event_cause]-> Cause -[cause_role]-> Role -[role_task]-> Task
DownEvent --> Asset (FK)
```

**Query example:** "What caused the last turbine downtime event, who is qualified to diagnose it, and what tasks should be performed?"

### 4. Equipment Hierarchy Path

```
Asset -[asset_system]-> System -[system_aggregate]-> Aggregate
Asset -[asset_location]-> Location (tree: plant > building > room)
Asset -[parent_id]-> Asset (hierarchy: facility > boiler > pump)
```

**Query example:** "Show me the full system decomposition, aggregate grouping, and physical location of Boiler Unit 01."

### 5. Work Order Tracking Path

```
Order -[order_asset]-> Asset -[asset_worker_assignment]-> Worker
Order -[order_asset]-> Asset --> DownEvent (FK)
```

**Query example:** "Show all open work orders for assets assigned to the morning shift workers."

### 6. Fault Propagation Path

```
Fault -[fault_cause_effect]-> Fault --> Asset (FK) -[asset_system]-> System
```

**Query example:** "Which faults caused the low water level warning, and what systems are affected?"

---

## PostgreSQL Schema Details

### Core Entity Tables (15 new + 5 existing)

New tables (created in migration `004_knowledge_graph_schema`):
- `levels`, `competences`, `roles`, `shifts`, `locations`, `aggregates`, `systems`
- `workers`, `tasks`, `actions`, `causes`, `materials`
- `down_events`, `orders`

Pre-existing tables:
- `assets`, `sensors`, `sensor_data`, `faults`, `maintenance_schedules`

### Junction Tables (13 new + 1 existing)

New junction tables (created in migration `004_knowledge_graph_schema`):
- `asset_worker_assignment` -- Asset <-> Worker
- `worker_competence` -- Worker <-> Competence (with `level_id`)
- `worker_shift` -- Worker <-> Shift
- `task_competence` -- Task <-> Competence (with `level_id`)
- `task_material` -- Task <-> Material (with `quantity_required`)
- `cause_role` -- Cause <-> Role
- `role_task` -- Role <-> Task
- `action_competence` -- Action <-> Competence
- `asset_system` -- Asset <-> System
- `system_aggregate` -- System <-> Aggregate
- `asset_location` -- Asset <-> Location
- `down_event_cause` -- DownEvent <-> Cause
- `order_asset` -- Order <-> Asset

Pre-existing junction table:
- `fault_cause_effect` -- Fault <-> Fault (with `link_type`)

### All Junction Table Schemas

#### `asset_worker_assignment`

| Column | Type | Constraints |
|--------|------|-------------|
| asset_id | UUID | FK -> assets.id, NOT NULL |
| worker_id | UUID | FK -> workers.id, NOT NULL |
| **Unique** | | (asset_id, worker_id) |

#### `worker_competence`

| Column | Type | Constraints |
|--------|------|-------------|
| worker_id | UUID | FK -> workers.id, NOT NULL |
| competence_id | UUID | FK -> competences.id, NOT NULL |
| level_id | UUID | FK -> levels.id, SET NULL on delete |
| **Unique** | | (worker_id, competence_id) |

#### `worker_shift`

| Column | Type | Constraints |
|--------|------|-------------|
| worker_id | UUID | FK -> workers.id, NOT NULL |
| shift_id | UUID | FK -> shifts.id, NOT NULL |
| **Unique** | | (worker_id, shift_id) |

#### `task_competence`

| Column | Type | Constraints |
|--------|------|-------------|
| task_id | UUID | FK -> tasks.id, NOT NULL |
| competence_id | UUID | FK -> competences.id, NOT NULL |
| level_id | UUID | FK -> levels.id, SET NULL on delete |
| **Unique** | | (task_id, competence_id) |

#### `task_material`

| Column | Type | Constraints |
|--------|------|-------------|
| task_id | UUID | FK -> tasks.id, NOT NULL |
| material_id | UUID | FK -> materials.id, NOT NULL |
| quantity_required | Float | nullable |
| **Unique** | | (task_id, material_id) |

#### `cause_role`

| Column | Type | Constraints |
|--------|------|-------------|
| cause_id | UUID | FK -> causes.id, NOT NULL |
| role_id | UUID | FK -> roles.id, NOT NULL |
| **Unique** | | (cause_id, role_id) |

#### `role_task`

| Column | Type | Constraints |
|--------|------|-------------|
| role_id | UUID | FK -> roles.id, NOT NULL |
| task_id | UUID | FK -> tasks.id, NOT NULL |
| **Unique** | | (role_id, task_id) |

#### `action_competence`

| Column | Type | Constraints |
|--------|------|-------------|
| action_id | UUID | FK -> actions.id, NOT NULL |
| competence_id | UUID | FK -> competences.id, NOT NULL |
| **Unique** | | (action_id, competence_id) |

#### `asset_system`

| Column | Type | Constraints |
|--------|------|-------------|
| asset_id | UUID | FK -> assets.id, NOT NULL |
| system_id | UUID | FK -> systems.id, NOT NULL |
| **Unique** | | (asset_id, system_id) |

#### `system_aggregate`

| Column | Type | Constraints |
|--------|------|-------------|
| system_id | UUID | FK -> systems.id, NOT NULL |
| aggregate_id | UUID | FK -> aggregates.id, NOT NULL |
| **Unique** | | (system_id, aggregate_id) |

#### `asset_location`

| Column | Type | Constraints |
|--------|------|-------------|
| asset_id | UUID | FK -> assets.id, NOT NULL |
| location_id | UUID | FK -> locations.id, NOT NULL |
| **Unique** | | (asset_id, location_id) |

#### `down_event_cause`

| Column | Type | Constraints |
|--------|------|-------------|
| down_event_id | UUID | FK -> down_events.id, NOT NULL |
| cause_id | UUID | FK -> causes.id, NOT NULL |
| **Unique** | | (down_event_id, cause_id) |

#### `order_asset`

| Column | Type | Constraints |
|--------|------|-------------|
| order_id | UUID | FK -> orders.id, NOT NULL |
| asset_id | UUID | FK -> assets.id, NOT NULL |
| **Unique** | | (order_id, asset_id) |

#### `fault_cause_effect` (pre-existing)

| Column | Type | Constraints |
|--------|------|-------------|
| causing_fault_id | UUID | FK -> faults.id, NOT NULL |
| affected_fault_id | UUID | FK -> faults.id, NOT NULL |
| link_type | String | e.g., "causes", "contributes_to" |

---

## SQLAlchemy Model Files

All models are defined in `app/models/` and re-exported from `app/models/__init__.py`.

| File | Model(s) |
|------|----------|
| `app/models/asset.py` | `Asset` |
| `app/models/worker.py` | `Worker` |
| `app/models/role.py` | `Role` |
| `app/models/competence.py` | `Competence` |
| `app/models/level.py` | `Level` |
| `app/models/task.py` | `Task` |
| `app/models/action.py` | `Action` |
| `app/models/cause.py` | `Cause` |
| `app/models/material.py` | `Material` |
| `app/models/shift.py` | `Shift` |
| `app/models/down_event.py` | `DownEvent` |
| `app/models/order.py` | `Order` |
| `app/models/location.py` | `Location` |
| `app/models/system.py` | `System` |
| `app/models/aggregate.py` | `Aggregate` |
| `app/models/sensor.py` | `Sensor` |
| `app/models/sensor_data.py` | `SensorData` |
| `app/models/fault.py` | `Fault`, `fault_cause_effect` |
| `app/models/maintenance_schedule.py` | `MaintenanceSchedule` |
| `app/models/graph_associations.py` | All 13 new junction tables |
| `app/models/graph_sync_log.py` | `GraphSyncLog` |
| `app/models/schemas.py` | Pydantic request/response schemas for all entities |

---

## Alembic Migration

Migration file: `alembic/versions/004_knowledge_graph_schema.py`

- **Revision ID:** `004_kg`
- **Revises:** `003_graph_sync_log`
- Creates all 15 new entity tables and 13 new junction tables
- The `downgrade()` function drops all tables in reverse dependency order

---

## Seed Data

The seed script at `scripts/seed_db.py` populates the database with realistic power plant data.

### Seed Data Counts

| Entity | Count | Seed Function |
|--------|-------|---------------|
| Assets | 7 (hierarchical) | `seed_assets()` |
| Sensors | 18 | `seed_sensors()` |
| Faults | 5 | `seed_faults()` |
| Levels | 4 | `seed_levels()` |
| Competences | 10 | `seed_competences()` |
| Roles | 8 | `seed_roles()` |
| Shifts | 3 | `seed_shifts()` |
| Locations | 6 (hierarchical) | `seed_locations()` |
| Aggregates | 3 | `seed_aggregates()` |
| Systems | 7 | `seed_systems()` |
| Workers | 7 | `seed_workers()` |
| Tasks | 7 | `seed_tasks()` |
| Actions | 8 | `seed_actions()` |
| Causes | 8 | `seed_causes()` |
| Materials | 8 | `seed_materials()` |
| DownEvents | 5 | `seed_down_events()` |
| Orders | 6 | `seed_orders()` |
| SensorData | 432 (18 sensors x 24 hours) | `seed_sensor_data()` |
| MaintenanceSchedules | 10 | `seed_maintenance_schedules()` |
| Association links | ~60+ | `seed_associations()` |

### Seed Execution Order (dependency-aware)

1. `seed_assets()` -- no dependencies
2. `seed_sensors()` -- depends on assets
3. `seed_faults()` -- depends on assets
4. `seed_levels()` -- no dependencies
5. `seed_competences()` -- no dependencies
6. `seed_roles()` -- no dependencies
7. `seed_shifts()` -- no dependencies
8. `seed_locations()` -- no dependencies
9. `seed_aggregates()` -- no dependencies
10. `seed_systems()` -- no dependencies
11. `seed_workers()` -- depends on competences, levels, shifts
12. `seed_tasks()` -- no dependencies
13. `seed_actions()` -- no dependencies
14. `seed_causes()` -- no dependencies
15. `seed_materials()` -- no dependencies
16. `seed_down_events()` -- depends on assets, causes
17. `seed_orders()` -- depends on assets
18. `seed_sensor_data()` -- depends on sensors
19. `seed_maintenance_schedules()` -- depends on assets, faults
20. `seed_associations()` -- depends on all entities above

### Seed Data Sample: Workers and Competence Assignments

| Worker | Employee ID | Competences | Shift |
|--------|-------------|-------------|-------|
| John Smith | EMP-001 | Boiler Operation (Advanced), Safety Procedures (Expert) | Morning |
| Maria Garcia | EMP-002 | Electrical Systems (Advanced), PLC Programming (Intermediate) | Morning |
| Robert Chen | EMP-003 | Vibration Analysis (Expert), Turbine Operation (Advanced) | Afternoon |
| Sarah Johnson | EMP-004 | Pump Maintenance (Advanced), Welding (Intermediate) | Afternoon |
| Ahmed Hassan | EMP-005 | Thermal Imaging (Advanced), Electrical Systems (Intermediate) | Night |
| Lisa Wong | EMP-006 | Safety Procedures (Advanced) | -- |
| James Brown | EMP-007 | Pipe Fitting (Expert), Welding (Advanced) | Morning |

### Seed Data Sample: Location Hierarchy

```
Main Plant (plant)
  +-- Building A (building, "Boiler house")
  |     +-- Boiler Room A (room)
  +-- Building B (building, "Turbine hall")
        +-- Turbine Hall B (room)
        +-- Control Room (room)
```

### Seed Data Sample: Asset-System-Aggregate Relationships

```
Steam Generation Line (Aggregate)
  +-- Feed Water System --> Feed Water Pump, Boiler Unit 01
  +-- Combustion System --> Boiler Unit 01
  +-- Steam System --> Boiler Unit 01, Steam Turbine 01
Power Generation Unit (Aggregate)
  +-- Turbine System --> Steam Turbine 01
  +-- Generator System --> Generator
Cooling Circuit (Aggregate)
  +-- Cooling Water System --> Generator, Cooling System
```

---

## Cypher Query Examples (for Neo4j graph sync)

### Find qualified workers for a task

```cypher
MATCH (t:Task {name: 'Bearing Replacement'})-[:requires]->(c:Competence)
MATCH (w:Worker)-[:has]->(c)
MATCH (c)-[:typeOf]->(l:Level)
MATCH (w)-[:works_in]->(s:Shift)
RETURN w.name AS worker, c.name AS competence, l.name AS level, s.name AS shift
```

### Analyze downtime root causes and find responsible roles

```cypher
MATCH (e:Asset {name: 'Steam Turbine 01'})
MATCH (e)<-[:booked_on]-(d:DownEvent)-[:has]->(c:Cause)
MATCH (c)-[:requires]->(r:Role)
RETURN d.started_at, d.downtime_minutes, c.name AS cause, c.severity,
       collect(r.name) AS required_roles
ORDER BY d.started_at DESC
```

### Equipment hierarchy with location and system decomposition

```cypher
MATCH (e:Asset)-[:consists_of]->(s:System)-[:part_of]->(a:Aggregate)
MATCH (e)-[:is_at]->(l:Location)
RETURN e.name AS equipment, s.name AS system, a.name AS aggregate, l.name AS location
```

### Material planning for active tasks

```cypher
MATCH (m:Material)-[:planned_in]-(t:Task {status: 'in_progress'})
RETURN m.name AS material, m.part_number, m.quantity_in_stock AS in_stock,
       t.name AS task, t.status
ORDER BY m.quantity_in_stock ASC
```

### Find workers qualified to resolve a specific downtime cause

```cypher
MATCH (de:DownEvent)-[:has]->(c:Cause {name: 'Vibration Damage'})
MATCH (c)-[:requires]->(r:Role)-[:enables]->(t:Task)-[:requires]->(comp:Competence)
MATCH (w:Worker)-[:has]->(comp)
MATCH (w)-[:works_in]->(s:Shift)
RETURN DISTINCT w.name AS worker, r.name AS role, comp.name AS competence, s.name AS shift
```

---

## API Endpoints

### CRUD Endpoints (per entity)

Each entity has standard CRUD operations:
- `POST /api/v1/{resource}` -- Create
- `GET /api/v1/{resource}` -- List (with pagination and filters)
- `GET /api/v1/{resource}/{id}` -- Get by ID
- `PUT /api/v1/{resource}/{id}` -- Update
- `DELETE /api/v1/{resource}/{id}` -- Delete

Resource names: `assets`, `workers`, `roles`, `competences`, `levels`, `tasks`, `actions`, `causes`, `materials`, `shifts`, `down-events`, `orders`, `locations`, `systems`, `aggregates`, `sensors`, `faults`, `maintenance-schedules`

### Special Endpoints

- `GET /api/v1/assets/{id}/workers` -- Get workers assigned to an asset
- `GET /api/v1/assets/{id}/down-events` -- Get downtime events for an asset
- `GET /api/v1/workers/{id}/competences` -- Get worker competences with levels
- `GET /api/v1/locations/tree` -- Get hierarchical location tree
- `GET /api/v1/down-events/statistics` -- Get downtime statistics
- `POST /api/v1/tasks/{id}/competences` -- Add competence requirement to task
- `POST /api/v1/tasks/{id}/materials` -- Add material requirement to task

---

## Implementation Phases

1. **Phase 1:** SQLAlchemy models + Alembic migration (`004_knowledge_graph_schema`)
2. **Phase 2:** Neo4j schema (constraints, indexes)
3. **Phase 3:** Graph sync service (node + edge sync)
4. **Phase 4:** Cypher templates + entity extractor + cypher generator
5. **Phase 5:** CRUD services + API routes
6. **Phase 6:** MCP tools update
7. **Phase 7:** Seed data + documentation (this document)
