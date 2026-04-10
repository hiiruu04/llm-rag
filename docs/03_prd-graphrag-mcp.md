# PRD: GraphRAG + MCP Architecture for LLM-RAG CMMS

**Version**: 1.0 | **Date**: 2026-04-08 | **Status**: Draft

---

## 1. Executive Summary

Evolve the existing LLM-RAG CMMS application with three major capabilities:

1. **GraphRAG via Neo4j** — A knowledge graph mirroring the CMMS domain model (assets, sensors, faults, maintenance schedules), enabling structured relationship queries (fault propagation chains, asset hierarchies, maintenance impact analysis) that vector search cannot serve well.
2. **MCP Server** — Expose CMMS data and GraphRAG capabilities as MCP tools/resources so external LLM clients (Claude Desktop, Cursor, etc.) can directly query the system.
3. **MCP Client** — Connect to external MCP servers to enrich answers with external context (equipment docs, industry standards, parts inventory).

**Key decisions**:
- Hybrid RAG: keep vector-based (Qdrant) for unstructured documents, add GraphRAG (Neo4j) for structured CMMS data
- On-demand rebuild for PostgreSQL → Neo4j sync (admin-triggered full/incremental)
- OpenAI only (GPT-4o) for all LLM operations

---

## 2. Current Architecture (Baseline)

```
docker-compose: [app, qdrant, postgres]

User Query → POST /api/v1/query
  → RAGPipeline.query()
    → EmbeddingService (OpenAI text-embedding-3-small)
    → VectorStoreManager (Qdrant cosine search, top-K=5)
    → Context string built from retrieved chunks
    → LLMService (LlamaIndex OpenAI → GPT-4o)
  → Response: {answer, sources, model_used, tokens_used}

PostgreSQL models: Asset, Sensor, SensorData, Fault (M2M cause-effect), MaintenanceSchedule
No MCP integration exists.
```

---

## 3. Knowledge Graph Schema (Neo4j)

### 3.1 Node Labels and Properties

Each PostgreSQL row becomes a node with `pg_id` (UUID string) as the cross-reference key.

**`:Asset`**
```
pg_id: String (UNIQUE), name, description, asset_type, status, location, created_at, updated_at
```

**`:Sensor`**
```
pg_id: String (UNIQUE), name, sensor_type, unit, status, created_at, updated_at
```

**`:SensorSummary`** (aggregated from `sensor_data` — NOT individual readings)
```
sensor_pg_id: String, window: String ("1h"|"6h"|"24h"|"7d"|"30d"),
window_start: DateTime, window_end: DateTime,
avg_value: Float, min_value: Float, max_value: Float, stddev: Float,
sample_count: Integer, anomaly_flag: Boolean
```

**`:Fault`**
```
pg_id: String (UNIQUE), code, name, description, severity, status,
detected_at, resolved_at, created_at, updated_at
```

**`:MaintenanceSchedule`**
```
pg_id: String (UNIQUE), title, description, maintenance_type, status, priority,
scheduled_date, completed_date, assigned_to, recurrence, estimated_duration_hours, notes,
created_at, updated_at
```

**`:SyncMetadata`** (singleton node tracking sync state)
```
last_full_sync: DateTime, last_incremental_sync: DateTime,
total_assets: Integer, total_sensors: Integer, total_faults: Integer, total_schedules: Integer,
sync_in_progress: Boolean
```

### 3.2 Relationships

| From | Type | To | Notes |
|------|------|----|-------|
| `Asset` | `HAS_PARENT` | `Asset` | Child → Parent (mirrors `parent_id` FK) |
| `Asset` | `HAS_SENSOR` | `Sensor` | |
| `Sensor` | `HAS_SUMMARY` | `SensorSummary` | |
| `Asset` | `HAS_FAULT` | `Fault` | |
| `Fault` | `CAUSES` | `Fault` | Directed: causing → affected (from `fault_cause_effect` table) |
| `Asset` | `HAS_MAINTENANCE` | `MaintenanceSchedule` | |
| `MaintenanceSchedule` | `ADDRESSES_FAULT` | `Fault` | Nullable (when `fault_id` is set) |

### 3.3 Constraints and Indexes

```cypher
-- Uniqueness (also creates index)
CREATE CONSTRAINT asset_pg_id IF NOT EXISTS FOR (a:Asset) REQUIRE a.pg_id IS UNIQUE;
CREATE CONSTRAINT sensor_pg_id IF NOT EXISTS FOR (s:Sensor) REQUIRE s.pg_id IS UNIQUE;
CREATE CONSTRAINT fault_pg_id IF NOT EXISTS FOR (f:Fault) REQUIRE f.pg_id IS UNIQUE;
CREATE CONSTRAINT maintenance_pg_id IF NOT EXISTS FOR (m:MaintenanceSchedule) REQUIRE m.pg_id IS UNIQUE;

-- Property indexes
CREATE INDEX asset_status IF NOT EXISTS FOR (a:Asset) ON (a.status);
CREATE INDEX asset_type IF NOT EXISTS FOR (a:Asset) ON (a.asset_type);
CREATE INDEX fault_severity IF NOT EXISTS FOR (f:Fault) ON (f.severity);
CREATE INDEX fault_status IF NOT EXISTS FOR (f:Fault) ON (f.status);
CREATE INDEX maintenance_status IF NOT EXISTS FOR (m:MaintenanceSchedule) ON (m.status);
CREATE INDEX maintenance_scheduled IF NOT EXISTS FOR (m:MaintenanceSchedule) ON (m.scheduled_date);

-- Fulltext for name search
CREATE FULLTEXT INDEX asset_name_search IF NOT EXISTS FOR (a:Asset) ON EACH [a.name, a.description];
CREATE FULLTEXT INDEX fault_name_search IF NOT EXISTS FOR (f:Fault) ON EACH [f.name, f.description];
```

### 3.4 Sensor Data Strategy

Individual sensor readings (potentially millions/day) are NOT synced as nodes. Instead, aggregate summaries are computed during sync using PostgreSQL window functions:

| Window | Covered Range | Aggregation |
|--------|--------------|-------------|
| `1h` | Last 24 hours | `date_trunc('hour', timestamp)` |
| `6h` | Last 7 days | 6-hour buckets |
| `24h` | Last 30 days | Daily |
| `7d` | Last 90 days | Weekly |
| `30d` | Everything older | Monthly |

Each summary: `{avg_value, min_value, max_value, stddev, sample_count, anomaly_flag}`.

### 3.5 Key Graph Query Patterns

```cypher
-- Asset subtree (all descendants)
MATCH (root:Asset {pg_id: $asset_id})<-[:HAS_PARENT*0..]-(descendant:Asset)
RETURN descendant

-- Fault propagation chain
MATCH path = (root:Fault {pg_id: $fault_id})-[:CAUSES*1..5]->(downstream:Fault)
RETURN path

-- Asset health dashboard
MATCH (asset:Asset {status: 'active'})
OPTIONAL MATCH (asset)-[:HAS_FAULT]->(f:Fault) WHERE f.status IN ['open','investigating']
OPTIONAL MATCH (asset)-[:HAS_MAINTENANCE]->(m:MaintenanceSchedule) WHERE m.status = 'overdue'
RETURN asset.name, count(DISTINCT f) AS open_faults, count(DISTINCT m) AS overdue_count

-- Maintenance impact analysis (what's affected if we take down an asset?)
MATCH (target:Asset {pg_id: $asset_id})<-[:HAS_PARENT*0..]-(descendant:Asset)
OPTIONAL MATCH (descendant)-[:HAS_FAULT]->(fault:Fault) WHERE fault.status IN ['open','investigating']
RETURN target, collect(DISTINCT descendant) AS affected, collect(DISTINCT fault) AS active_faults
```

---

## 4. PostgreSQL → Neo4j Sync Pipeline

### 4.1 Full Rebuild

1. `MATCH (n) DETACH DELETE n` — wipe Neo4j
2. Re-create constraints and indexes
3. Load data in dependency order using batched `UNWIND` (500 rows/batch):
   - Assets → Sensors → Faults → MaintenanceSchedules
   - Then: `HAS_PARENT` edges, `CAUSES` edges, `ADDRESSES_FAULT` edges
   - Finally: SensorSummary aggregates (computed via SQL, written to Neo4j)
4. Write `SyncMetadata` node with counts and timestamps

```cypher
-- Batch asset creation example
UNWIND $batch AS row
MERGE (a:Asset {pg_id: row.pg_id})
SET a.name = row.name, a.description = row.description,
    a.asset_type = row.asset_type, a.status = row.status,
    a.location = row.location
```

### 4.2 Incremental Rebuild

1. Read `last_incremental_sync` from `SyncMetadata` node
2. Query PostgreSQL for records with `updated_at > last_sync` — `MERGE` (upsert) into Neo4j
3. Detect deletions: IDs in Neo4j but absent from PostgreSQL → `DETACH DELETE`
4. Recompute sensor summaries only for modified/new sensors
5. Update `SyncMetadata`

### 4.3 Sync Admin API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/admin/graph/sync/full` | Trigger full rebuild (background task) |
| `POST` | `/api/v1/admin/graph/sync/incremental` | Trigger incremental sync |
| `GET` | `/api/v1/admin/graph/sync/status` | Sync state, node counts, in-progress flag |
| `GET` | `/api/v1/graph/info` | Neo4j connectivity, node counts |

### 4.4 Sync Log (PostgreSQL)

New `graph_sync_log` table tracks each sync operation:

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `sync_type` | String(20) | `"full"` or `"incremental"` |
| `status` | String(20) | `"started"`, `"completed"`, `"failed"` |
| `started_at` | DateTime(tz) | |
| `completed_at` | DateTime(tz) | nullable |
| `records_processed` | Integer | |
| `error_message` | Text | nullable |
| `metadata` | JSONB | nullable, stores counts per entity type |

### 4.5 Safety

- All Neo4j writes use `MERGE` (idempotent)
- Batch transactions (500 records each), retry up to 3x with backoff
- `sync_in_progress` flag prevents concurrent syncs; 10-min timeout clears stale locks
- LLM-generated Cypher: whitelist-only clauses (`MATCH`, `RETURN`, `WHERE`, `WITH`, `OPTIONAL MATCH`, `ORDER BY`, `LIMIT`). Mutating clauses (`CREATE`, `MERGE`, `DELETE`, `SET`) are rejected.

---

## 5. GraphRAG Query Pipeline

### 5.1 Architecture

```
User Query
    ↓
[Intent Classifier] (GPT-4o lightweight call)
    ↓
    ├── "document_search"  →  Vector RAG (existing Qdrant pipeline)
    ├── "structured_query" →  GraphRAG (Neo4j)
    ├── "hybrid"           →  Both in parallel → merge contexts → LLM
    └── "general"          →  LLM direct (no retrieval)
```

### 5.2 Intent Classification

Single GPT-4o call with a short prompt. Categories:
- `document_search` — questions about manuals, procedures, unstructured docs
- `structured_query` — questions about assets, faults, maintenance, relationships, hierarchies, statistics
- `hybrid` — requires both document knowledge AND structured CMMS data
- `general` — not related to CMMS or documents

### 5.3 Entity Extraction (for GraphRAG queries)

GPT-4o structured output call extracts:
- `asset_names`, `asset_types`, `fault_codes`, `fault_severities`
- `sensor_types`, `maintenance_types`, `maintenance_statuses`
- `time_range` (start, end, relative)
- `locations`
- `query_type`: `asset_tree | fault_chain | sensor_status | maintenance_schedule | statistics | relationship | search`

### 5.4 NL → Cypher (Two-tier approach)

**Tier 1: Template-based** (safe, fast) — Predefined Cypher templates keyed by `query_type`, parameterized with extracted entities. 7 templates covering: `asset_tree`, `fault_chain`, `sensor_status`, `maintenance_schedule`, `relationship`, `statistics`, `search`.

**Tier 2: LLM-generated** (flexible) — When no template matches, GPT-4o generates Cypher from the graph schema + user question. Output is validated against a clause whitelist before execution.

### 5.5 Graph Context Formatting

Neo4j results are formatted as structured text for the LLM:

```
[Graph Result 1]
  Asset: {"name": "CNC Mill #3", "asset_type": "machine", "status": "active"}
  Fault: {"code": "VIB-001", "name": "Excessive Vibration", "severity": "high"}
  Path: Excessive Vibration -CAUSES-> Bearing Overheating -CAUSES-> Line Shutdown

[Graph Result 2]
  MaintenanceSchedule: {"title": "Bearing Inspection", "status": "scheduled", "scheduled_date": "2026-04-15"}
```

### 5.6 Hybrid Merge

When intent is `hybrid`, both pipelines run in parallel:
1. Vector RAG → `{doc_context, sources}`
2. GraphRAG → `{graph_context, cypher_used}`
3. Both contexts combined into a single LLM prompt that instructs synthesis from both sources with citations

---

## 6. MCP Server Design

### 6.1 Transport

Streamable HTTP (SSE-based), mounted at `/mcp` on the FastAPI app. Accessible over the network for Claude Desktop, Cursor, and any MCP-compatible client.

### 6.2 Tools (8 total)

| Tool | Description | Key Parameters |
|------|-------------|---------------|
| `query_assets` | Search/filter assets | `search`, `asset_type`, `status`, `location`, `limit` |
| `get_asset_details` | Full asset with sensors, faults, maintenance | `asset_id`, `include_children`, `include_sensors`, `include_faults`, `include_maintenance` |
| `get_asset_tree` | Hierarchical asset tree | `root_asset_id?`, `max_depth` |
| `search_faults` | Filter faults across assets | `asset_id?`, `severity?`, `status?`, `code?`, `include_chain?` |
| `get_fault_chain` | Full cause-effect propagation | `fault_id`, `direction` (upstream/downstream/both), `max_depth` |
| `get_sensor_status` | Sensor readings and summaries | `asset_id?`, `sensor_id?`, `window`, `include_latest_reading` |
| `get_maintenance_schedule` | Filter maintenance schedules | `asset_id?`, `status?`, `maintenance_type?`, `priority?` |
| `graph_query` | Natural language → graph query | `question`, `include_documents?` |
| `hybrid_query` | NL query across both graph + documents | `question` |

### 6.3 Resources (6 total)

| URI | Description |
|-----|-------------|
| `cmms://assets/catalog` | All assets with basic info |
| `cmms://assets/{id}/summary` | Asset summary: sensors, open faults, upcoming maintenance |
| `cmms://faults/active` | All active (non-resolved) faults |
| `cmms://maintenance/overdue` | All overdue maintenance schedules |
| `cmms://sensors/anomalies` | Sensor summaries flagged as anomalous (last 24h) |
| `cmms://graph/schema` | Description of the Neo4j graph schema |

### 6.4 Authentication

API key via `X-MCP-API-Key` header. Configured via `MCP_API_KEY` env var. If unset, no auth (for local dev).

---

## 7. MCP Client Design

### 7.1 Purpose

The app connects to external MCP servers for context enrichment during query answering (e.g., equipment manufacturer docs, industry standards, parts inventory).

### 7.2 Configuration

```env
MCP_CLIENT_ENABLED=false
MCP_CLIENT_SERVERS=[{"name":"equipment_docs","url":"http://equipment-mcp:3001/mcp","api_key":"..."}]
```

### 7.3 Client Manager

`MCPClientManager` singleton:
- Connects to configured servers at startup
- Discovers available tools from each server
- Provides `call_tool(tool_name, arguments)` interface
- Integrates with GraphRAG pipeline: external tools called when intent classifier determines external context would help

---

## 8. API Changes

### 8.1 Modified Endpoint

`POST /api/v1/query` — add optional `mode` parameter:

```python
class QueryRequest(BaseModel):
    question: str
    mode: Literal["auto", "vector", "graph", "hybrid"] = "auto"
```

Response extended with `graph_sources`, `mode_used` fields (present when graph was used).

### 8.2 New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/query/graph` | Direct GraphRAG query |
| `POST` | `/api/v1/query/hybrid` | Hybrid vector+graph query |
| `POST` | `/api/v1/admin/graph/sync/full` | Full Neo4j rebuild |
| `POST` | `/api/v1/admin/graph/sync/incremental` | Incremental sync |
| `GET` | `/api/v1/admin/graph/sync/status` | Sync status |
| `GET` | `/api/v1/graph/info` | Neo4j connectivity and node counts |
| (MCP) | `/mcp` | MCP server endpoint |

### 8.3 Modified

`GET /api/v1/health` — add `neo4j_connected` and `graph_info` to health response.

---

## 9. Infrastructure Changes

### 9.1 docker-compose.yml — Add Neo4j

```yaml
neo4j:
  image: neo4j:5-community
  ports:
    - "7474:7474"  # HTTP browser
    - "7687:7687"  # Bolt protocol
  environment:
    NEO4J_AUTH: ${NEO4J_USER:-neo4j}/${NEO4J_PASSWORD:-password123}
    NEO4J_PLUGINS: '["apoc"]'
  volumes:
    - neo4j_data:/data
  healthcheck:
    test: ["CMD-SHELL", "cypher-shell -u neo4j -p password123 'RETURN 1' || exit 1"]
    interval: 10s
```

### 9.2 New Dependencies (pyproject.toml)

```toml
"neo4j>=5.0.0",       # Neo4j async Python driver
"mcp[cli]>=1.0.0",    # MCP SDK (FastMCP server)
"httpx-sse>=0.4.0",   # SSE client for MCP client connections
```

### 9.3 New Environment Variables (.env.example)

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
NEO4J_DATABASE=neo4j

# MCP Server
MCP_SERVER_ENABLED=true
MCP_API_KEY=

# MCP Client
MCP_CLIENT_ENABLED=false
MCP_CLIENT_SERVERS=[]
```

### 9.4 New Alembic Migration

`003_graph_sync_log.py` — creates `graph_sync_log` table.

---

## 10. Implementation Phases

### Phase 1: Neo4j Infrastructure + Sync Pipeline
- Neo4j service in docker-compose
- `app/core/neo4j.py` — driver connection manager (follow `database.py` singleton pattern)
- `app/utils/neo4j_setup.py` — schema/constraint initialization (follow `qdrant_setup.py` pattern)
- `app/services/graph_sync_service.py` — full/incremental sync logic
- `app/models/graph_sync_log.py` + Alembic migration `003_graph_sync_log.py`
- `app/api/routes/graph_admin.py` — admin sync endpoints
- Update `app/core/config.py` with Neo4j settings
- Update `app/main.py` lifespan for Neo4j driver cleanup
- Update `docker-compose.yml`, `.env.example`, `pyproject.toml`
- Update `app/api/routes/health.py` with Neo4j health check

**Validation**: Run full sync against PostgreSQL, verify all nodes/relationships in Neo4j Browser.

### Phase 2: GraphRAG Query Pipeline
- `app/services/intent_classifier.py` — LLM-based intent classification
- `app/services/entity_extractor.py` — LLM-based entity extraction
- `app/services/cypher_templates.py` — predefined Cypher query templates
- `app/services/cypher_generator.py` — LLM-based Cypher generation + safety validation
- `app/core/graph_rag_pipeline.py` — GraphRAG pipeline (follow `rag_pipeline.py` singleton pattern)
- `app/core/hybrid_pipeline.py` — merged vector+graph pipeline
- Modify `app/api/routes/query.py` — add `mode` parameter, route to appropriate pipeline
- Add new query schemas to `app/models/schemas.py`

**Validation**: Test various query types — asset hierarchies, fault chains, maintenance schedules, sensor summaries. Verify hybrid queries merge correctly.

### Phase 3: MCP Server
- `app/mcp/server.py` — MCP server setup with FastMCP
- `app/mcp/tools/` — 8 tool implementations (asset, fault, sensor, maintenance, query tools)
- `app/mcp/resources/` — 6 resource implementations
- `app/mcp/auth.py` — API key authentication
- Mount at `/mcp` in `app/main.py`

**Validation**: Connect Claude Desktop or Cursor to `/mcp`. Test all tools and resources.

### Phase 4: MCP Client
- `app/mcp/client.py` — client manager
- External tool discovery and invocation
- Integration with GraphRAG pipeline for context enrichment
- Configuration in `.env`

**Validation**: Configure sample external MCP server, verify tool discovery and invocation.

### Phase 5: Testing + Documentation
- Integration tests for sync pipeline, GraphRAG queries, MCP tools/resources
- Update API docs, README with Neo4j setup
- Docker Compose documentation

---

## 11. File Structure

### New Files

```
app/
  core/
    neo4j.py                              # Neo4j async driver manager
    graph_rag_pipeline.py                 # GraphRAG query pipeline
    hybrid_pipeline.py                    # Vector+Graph merged pipeline
  services/
    graph_sync_service.py                 # Full/incremental sync logic
    intent_classifier.py                  # Query intent classification
    entity_extractor.py                   # Entity extraction from queries
    cypher_templates.py                   # Predefined Cypher templates
    cypher_generator.py                   # LLM Cypher generation + validation
  mcp/
    __init__.py
    server.py                             # FastMCP server setup
    client.py                             # MCP client manager
    auth.py                               # API key auth middleware
    tools/
      __init__.py
      asset_tools.py                      # query_assets, get_asset_details, get_asset_tree
      fault_tools.py                      # search_faults, get_fault_chain
      sensor_tools.py                     # get_sensor_status
      maintenance_tools.py                # get_maintenance_schedule
      query_tools.py                      # graph_query, hybrid_query
    resources/
      __init__.py
      asset_resources.py                  # cmms://assets/* resources
      fault_resources.py                  # cmms://faults/* resources
      maintenance_resources.py            # cmms://maintenance/* resources
      sensor_resources.py                 # cmms://sensors/* resources
      graph_resources.py                  # cmms://graph/schema
  api/routes/
    graph_admin.py                        # Sync admin endpoints
  models/
    graph_sync_log.py                     # Sync log SQLAlchemy model
  utils/
    neo4j_setup.py                        # Neo4j schema initialization

alembic/versions/
  003_graph_sync_log.py                   # Migration for graph_sync_log table
```

### Files to Modify

```
app/core/config.py                        # Add Neo4j, MCP server, MCP client settings
app/main.py                               # Mount MCP server, add routers, update lifespan
app/api/routes/query.py                   # Add mode parameter, hybrid routing
app/api/routes/health.py                  # Add Neo4j health check
app/models/__init__.py                    # Import GraphSyncLog
app/models/schemas.py                     # Add query mode schemas
docker-compose.yml                        # Add neo4j service
pyproject.toml                            # Add neo4j, mcp dependencies
.env.example                              # Add Neo4j, MCP variables
scripts/docker_init_qdrant.sh             # Add Neo4j wait + schema init
```

---

## 12. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Neo4j memory pressure with large graphs | Medium | High | Monitor memory; paginate sync batches; Neo4j config tuning |
| LLM-generated Cypher injection | Medium | Critical | Whitelist-only clauses; reject mutating queries; parameterize all inputs |
| Data drift between PG and Neo4j | High | Medium | Visible sync status; health checks; incremental sync endpoint |
| Intent classifier misclassification | Medium | Medium | Explicit `mode` parameter override; log for tuning |
| Concurrent sync operations | Medium | Medium | `sync_in_progress` lock; 10-min stale lock timeout |
