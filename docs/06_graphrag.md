# GraphRAG Pipeline Implementation Plan

## Overview

Implement a true GraphRAG system following the Qdrant + Neo4j pattern:

- **Ingestion**: Documents are chunked, embedded into Qdrant **AND** entities/relationships are extracted via LLM and stored in Neo4j
- **Retrieval**: Query is vectorized, semantic search finds relevant chunks in Qdrant, chunk IDs are used to traverse the Neo4j graph for enriched context, then the LLM generates an answer

This is **separate** from the existing `graph_rag_pipeline.py` (which extracts entities from queries and generates Cypher). The new pipeline uses vector similarity as the entry point and enriches with graph context.

---

## Architecture

```
INGESTION:
  Document -> Text Extraction -> Chunks
    -> Embedding -> Store in Qdrant (existing)
    -> LLM Entity/Rel Extraction -> Store in Neo4j (NEW)
    -> Link extracted entities to CMMS nodes (NEW)

RETRIEVAL:
  Query -> Embed -> Semantic Search (Qdrant) -> Extract Chunk IDs
    -> Query Neo4j graph around those IDs -> Graph Context
    -> Graph Context + Doc Passages + Query -> LLM -> Answer
```

---

## Neo4j Schema (New Nodes)

| Node Label | Key Properties | Purpose |
|---|---|---|
| `DocumentChunk` | `chunk_id` (Qdrant point ID), `document_id`, `chunk_index`, `text`, `file_name` | Bridge between Qdrant and Neo4j |
| `DocEntity` | `entity_id`, `name`, `entity_type`, `description`, `source_document_id` | Entities extracted from documents |

**New Relationships:**

| Type | From -> To | Description |
|---|---|---|
| `MENTIONED_IN` | DocEntity -> DocumentChunk | Entity found in this chunk |
| `RELATED_TO` | DocEntity -> DocEntity | Extracted relationships between entities |
| `NEXT_CHUNK` | DocumentChunk -> DocumentChunk | Sequential ordering within a document |
| `REFERS_TO` | DocEntity -> Asset/Fault/Sensor/... | Links to existing CMMS entities |

These coexist with the existing CMMS graph nodes (Asset, Fault, Sensor, Worker, etc.) and their relationships (HAS_SENSOR, HAS_FAULT, etc.).

---

## Implementation Steps

### Step 1: Configuration & Schema Updates

**`app/core/config.py`** -- Add GraphRAG settings:
```python
graphrag_enabled: bool = True
graphrag_max_entities_per_chunk: int = 20
graphrag_neighborhood_hops: int = 2
```

**`app/utils/neo4j_setup.py`** -- Add constraints/indexes for `DocumentChunk` and `DocEntity` nodes:
- Unique constraint on `DocumentChunk.chunk_id`
- Unique constraint on `DocEntity.entity_id`
- Index on `DocumentChunk.document_id`
- Index on `DocEntity.entity_type` and `DocEntity.source_document_id`
- Fulltext index on `DocEntity.name` and `DocEntity.description`

**`docker-compose.yml`** + **`.env.example`** -- Add GraphRAG env vars (`GRAPHRAG_ENABLED`, `GRAPHRAG_MAX_ENTITIES_PER_CHUNK`, `GRAPHRAG_NEIGHBORHOOD_HOPS`).

### Step 2: Document Entity Extraction Service

**`app/services/document_entity_extractor.py`** (NEW):
- LLM-based extraction of entities and relationships from text chunks
- Uses OpenAI API with structured JSON output prompt
- Entity types: Equipment, Component, Procedure, FailureMode, Material, Symptom, Measurement, Action, Specification, Person, Location
- Returns `{"entities": [...], "relationships": [...]}`

**`app/services/entity_linking_service.py`** (NEW):
- Links `DocEntity` nodes to existing CMMS nodes (Asset, Fault, Sensor, etc.)
- Uses Neo4j fulltext indexes for fuzzy name matching (score threshold > 0.5)
- Creates `REFERS_TO` relationships

### Step 3: Graph Ingestion Service

**`app/services/graph_ingestion_service.py`** (NEW):
- Orchestrates writing DocumentChunk nodes, DocEntity nodes, and all relationships into Neo4j
- Called during document ingestion after Qdrant storage (as a background task)
- Handles entity deduplication across chunks by name
- Generates deterministic chunk IDs from `document_id + chunk_index` to match Qdrant point IDs
- Provides `delete_document_graph()` for cleanup on document deletion

**`app/api/routes/documents.py`** (MODIFY):
- Add `enable_graph: bool = Form(True)` parameter to ingestion endpoint
- After Qdrant storage, trigger graph ingestion as `BackgroundTasks`
- On document delete, also clean up graph data

### Step 4: GraphRAG Retrieval Pipeline

**`app/core/graphrag_pipeline.py`** (NEW):
1. Embed query -> Semantic search in Qdrant
2. Extract chunk IDs from Qdrant results
3. Query Neo4j for entities mentioned in those chunks, their relationships, and any linked CMMS nodes
4. Get extended graph neighborhood (configurable hops, default 2)
5. LLM generates answer from doc passages + graph context + CMMS references

Graph context Cypher query:
```cypher
MATCH (e:DocEntity)-[:MENTIONED_IN]->(c:DocumentChunk)
WHERE c.chunk_id IN $chunk_ids
WITH collect(DISTINCT e) AS entities, collect(DISTINCT c) AS chunks
// Get relationships between those entities
UNWIND entities AS e1 UNWIND entities AS e2
MATCH (e1)-[r:RELATED_TO]->(e2)
WITH entities, chunks, collect({...}) AS relationships
// Get extended neighborhood (2 hops)
UNWIND entities AS e
MATCH path = (e)-[:RELATED_TO*1..2]-(neighbor:DocEntity)
WHERE NOT neighbor IN entities
WITH entities, chunks, relationships, collect(DISTINCT neighbor) AS neighbors
// Get CMMS references
UNWIND entities AS e
OPTIONAL MATCH (e)-[:REFERS_TO]->(cmms)
RETURN entities, chunks, relationships, neighbors,
       collect(DISTINCT {...cmms info...}) AS cmms_refs
```

### Step 5: API Integration

**`app/api/routes/query.py`** (MODIFY):
- Add `"graphrag"` to the mode literal: `Literal["auto", "vector", "graph", "graphrag", "hybrid"]`
- Add `_run_graphrag_query()` function
- Add `POST /api/v1/query/graphrag` endpoint
- Route `mode="graphrag"` to the new pipeline
- Add `graph_entities` and `cmms_references` to `QueryData` response model

**`app/services/intent_classifier.py`** (MODIFY):
- Add `graphrag` as an intent category for queries about entity relationships, equipment connections, or cross-referencing documents with CMMS data

---

## Files Summary

### New Files (4)

| File | Purpose |
|---|---|
| `app/services/document_entity_extractor.py` | LLM entity/relationship extraction from chunks |
| `app/services/entity_linking_service.py` | Link doc entities to CMMS graph nodes |
| `app/services/graph_ingestion_service.py` | Write document graph data to Neo4j |
| `app/core/graphrag_pipeline.py` | GraphRAG retrieval pipeline |

### Modified Files (7)

| File | Changes |
|---|---|
| `app/core/config.py` | Add GraphRAG settings |
| `app/utils/neo4j_setup.py` | Add DocumentChunk/DocEntity constraints & indexes |
| `app/api/routes/documents.py` | Trigger graph ingestion on upload, cleanup on delete |
| `app/api/routes/query.py` | Add `graphrag` mode + endpoint |
| `app/services/intent_classifier.py` | Add `graphrag` intent |
| `docker-compose.yml` | Add GraphRAG env vars |
| `.env.example` | Add GraphRAG env vars |

---

## Key Design Decisions

1. **Coexists with existing pipelines** -- doesn't replace `graph_rag_pipeline.py` (Cypher-based) or `hybrid_pipeline.py`
2. **Background graph ingestion** -- entity extraction is LLM-intensive; runs as FastAPI `BackgroundTasks` so API returns quickly
3. **Qdrant point ID as bridge** -- `generate_point_id()` produces the same deterministic hash from `document_id + chunk_index` that Qdrant uses, linking vectors to `DocumentChunk` nodes
4. **Cross-linking to CMMS** -- `REFERS_TO` edges bridge unstructured documents to the structured CMMS graph via fulltext matching
5. **2-hop neighborhood** -- balances rich context vs. performance; configurable via `GRAPHRAG_NEIGHBORHOOD_HOPS`
6. **Entity deduplication** -- entities with the same name (case-insensitive) across chunks are merged into a single `DocEntity` node with multiple `MENTIONED_IN` edges

---

## Verification

1. Start all services: `docker-compose up -d`
2. Trigger a full graph sync: `POST /api/v1/admin/graph/sync/full`
3. Seed the database: `uv run python scripts/seed_db.py --clean`
4. Verify Neo4j has CMMS nodes (Asset, Fault, Sensor, etc.)
5. Ingest a document: `curl -X POST localhost:8000/api/v1/documents -F "file=@test.pdf"`
6. Check Neo4j for `DocumentChunk` and `DocEntity` nodes
7. Query with GraphRAG mode: `curl -X POST localhost:8000/api/v1/query/graphrag -H "Content-Type: application/json" -d '{"question": "..."}'`
8. Verify response includes `graph_entities` and `cmms_references`
9. Run `ruff check .` and `ruff format .` for code quality
