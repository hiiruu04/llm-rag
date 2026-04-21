# 07 - GraphRAG Improvements: CMMS-Document Links & Fallback Pipeline

## Overview

Two improvements to the GraphRAG system:

1. **Direct CMMS → DocumentChunk relationships** (`HAS_DOCUMENT`): When an extracted entity links to a CMMS node (Asset, Sensor, Fault, etc.), create a direct relationship from that CMMS node to all DocumentChunks where the entity was mentioned.

2. **Fallback to direct graph query**: When vector search finds no matching documents, fall back to querying the knowledge graph directly (entity extraction + Cypher) instead of returning "no results."

---

## Architecture

```
QUERY PIPELINE (Improved):

User Query
  │
  ├─ Embed → Vector Search (Qdrant)
  │
  ├─── Relevant docs found?
  │      │
  │      ├── YES → Use chunk_ids to query Knowledge Graph (Neo4j)
  │      │         Traverse: DocEntity, RELATED_TO, REFERS_TO, HAS_DOCUMENT
  │      │         → Synthesize doc passages + graph context + CMMS refs → Answer
  │      │
  │      └── NO → Entity Extraction from query → Cypher Generation
  │                → Query Knowledge Graph directly
  │                → Generate answer from graph results only
  │
  └── Final Answer


INGESTION PIPELINE (Improved):

Document → Chunks → Qdrant (vectors)
                    └→ Neo4j:
                        1. DocumentChunk nodes
                        2. Entity extraction (LLM)
                        3. DocEntity nodes + MENTIONED_IN + RELATED_TO
                        4. NEXT_CHUNK (sequential)
                        5. Entity linking → REFERS_TO CMMS nodes
                        6. HAS_DOCUMENT: CMMS nodes → DocumentChunk  ← NEW
```

---

## Files to Modify

| File | Change |
|---|---|
| `app/services/graph_ingestion_service.py` | Add Step 6: create `HAS_DOCUMENT` relationships after entity linking |
| `app/core/graphrag_pipeline.py` | Add fallback logic, update `GRAPH_CONTEXT_QUERY` to include direct CMMS links |
| `app/services/cypher_generator.py` | Update `GRAPH_SCHEMA` to document `HAS_DOCUMENT` |
| `app/api/routes/query.py` | Include `cypher_used` in GraphRAG response |

---

## Step 1: Create `HAS_DOCUMENT` Relationships During Ingestion

**File**: `app/services/graph_ingestion_service.py`

After Step 5 (entity linking to CMMS via `REFERS_TO`, around line 164), add a new Step 6 that creates direct `(CMMS_Node)-[:HAS_DOCUMENT]->(DocumentChunk)` relationships.

Logic:
- Build `entity_id → set(chunk_ids)` mapping from the existing `entity_chunk_map` and `all_entities` data
- For each CMMS link (which has `entity_id`, `cmms_pg_id`, `cmms_label`), look up the associated chunk IDs
- Use a batched `UNWIND` Cypher query to create the relationships

```python
# Step 6: Create direct CMMS -> DocumentChunk relationships
entity_id_to_chunks: dict[str, set[int]] = {}
for name_key, chunk_id in entity_chunk_map:
    eid = all_entities[name_key]["entity_id"]
    entity_id_to_chunks.setdefault(eid, set()).add(chunk_id)

cmms_chunk_pairs = []
for link in cmms_links:
    for cid in entity_id_to_chunks.get(link["entity_id"], set()):
        cmms_chunk_pairs.append({
            "pg_id": link["cmms_pg_id"],
            "label": link["cmms_label"],
            "chunk_id": cid,
        })

if cmms_chunk_pairs:
    async with driver.session(database=settings.neo4j_database) as session:
        await session.run(
            """
            UNWIND $pairs AS p
            MATCH (c) WHERE c.pg_id = p.pg_id AND p.label IN labels(c)
            MATCH (chunk:DocumentChunk {chunk_id: p.chunk_id})
            MERGE (c)-[:HAS_DOCUMENT]->(chunk)
            """,
            pairs=cmms_chunk_pairs,
        )
```

No changes to `delete_document_graph()` — `DETACH DELETE` on DocumentChunk already removes `HAS_DOCUMENT` edges.

---

## Step 2: Update Cypher Generator Schema

**File**: `app/services/cypher_generator.py`

Add `HAS_DOCUMENT` relationship to the `GRAPH_SCHEMA` string so the LLM Cypher generator can use it:
```
- (Asset|Sensor|Fault|Location|Worker|Task|Material)-[:HAS_DOCUMENT]->(DocumentChunk)
```

---

## Step 3: Add Fallback to Direct Graph Query

**File**: `app/core/graphrag_pipeline.py`

### 3a. New imports
```python
from app.services.entity_extractor import get_entity_extractor
from app.services.cypher_generator import get_cypher_generator
from app.services.cypher_templates import get_template
```

### 3b. New fallback prompt
```python
GRAPH_FALLBACK_PROMPT = """\
You are a CMMS analyst assistant. Answer the user's question based on \
the knowledge graph query results below.
Format your answer with structured information.

--- KNOWLEDGE GRAPH RESULTS ---
{graph_context}

Question: {question}

Answer:"""
```

### 3c. Modify `query()` method
Replace the early return at lines 99-106 (the "no results" block) with:
```python
if not retrieved_docs:
    logger.info("No vector results, falling back to direct graph query")
    return await self._fallback_graph_query(question)
```

### 3d. New `_fallback_graph_query()` method
Reuses the same entity extraction + Cypher generation pattern from `graph_rag_pipeline.py`:
1. Extract entities from question via `entity_extractor.extract()`
2. Try template-based Cypher first, then LLM-generated Cypher
3. Execute Cypher against Neo4j
4. Generate answer with `GRAPH_FALLBACK_PROMPT`
5. Return with `mode_used: "graphrag_fallback"` and `cypher_used` populated

---

## Step 4: Enhance GRAPH_CONTEXT_QUERY with Direct CMMS Links

**File**: `app/core/graphrag_pipeline.py`

Add Step 5 to the existing Cypher query to also traverse the new `HAS_DOCUMENT` relationships:

```cypher
// Step 5: Get direct CMMS -> DocumentChunk links
UNWIND chunks AS ch
OPTIONAL MATCH (cmms_direct)-[:HAS_DOCUMENT]->(ch)
WHERE cmms_direct IS NOT NULL
WITH entities, chunks, relationships, neighbors, cmms_refs,
     collect(DISTINCT {
       chunk_id: ch.chunk_id,
       cmms_label: labels(cmms_direct)[0],
       cmms_name: cmms_direct.name,
       cmms_pg_id: cmms_direct.pg_id
     }) AS direct_cmms_refs
RETURN entities, chunks, relationships, neighbors, cmms_refs, direct_cmms_refs
```

Update `_query_graph_context()` to include `direct_cmms_refs` in the returned dict.
Update `_format_cmms_context()` to format both `cmms_refs` (entity-based) and `direct_cmms_refs` (direct links).

---

## Step 5: Update API Response

**File**: `app/api/routes/query.py`

In the `query_graphrag` endpoint, include `cypher_used` in the response:
```python
data = QueryData(
    ...,
    cypher_used=result.get("cypher_used"),  # add this
)
```

---

## Backfill for Existing Data

Run a one-time Cypher to create `HAS_DOCUMENT` for already-ingested documents:
```cypher
MATCH (e:DocEntity)-[:REFERS_TO]->(cmms)
MATCH (e)-[:MENTIONED_IN]->(chunk:DocumentChunk)
MERGE (cmms)-[:HAS_DOCUMENT]->(chunk)
```

This can be added as an admin endpoint or run directly in Neo4j Browser.

---

## New Graph Schema

After implementation, the complete relationship model:

```
CMMS Nodes (Asset, Sensor, Fault, etc.)
  ├─[:HAS_DOCUMENT]→ DocumentChunk          ← NEW (direct link)
  ├─[:HAS_SENSOR], [:HAS_FAULT], etc.       ← existing CMMS relationships
  └─←[:REFERS_TO]─ DocEntity                ← existing (entity linking)

DocEntity
  ├─[:MENTIONED_IN]→ DocumentChunk           ← existing
  ├─[:RELATED_TO]→ DocEntity                 ← existing
  └─[:REFERS_TO]→ CMMS Nodes                 ← existing

DocumentChunk
  ├─[:NEXT_CHUNK]→ DocumentChunk             ← existing
  └─←[:HAS_DOCUMENT]─ CMMS Nodes             ← NEW (reverse)
```

---

## Verification

1. Upload a document that references known CMMS assets
2. Check Neo4j for `HAS_DOCUMENT` relationships:
   ```cypher
   MATCH (a:Asset)-[r:HAS_DOCUMENT]->(c:DocumentChunk) RETURN a.name, c.chunk_id
   ```
3. Query with GraphRAG mode for something matching the document → verify `direct_cmms_refs` appears in context
4. Query with GraphRAG mode for something NOT in any document → verify fallback to graph query works (check `mode_used: "graphrag_fallback"`)
5. Verify pure graph mode (`/query/graph`) still works independently
6. Run `ruff check .` and `ruff format .`
