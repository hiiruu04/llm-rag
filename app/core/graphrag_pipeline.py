import asyncio
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings
from app.core.embeddings import get_embedding_service
from app.core.neo4j import get_neo4j_driver
from app.core.vector_store import get_vector_store

GRAPHRAG_PROMPT = """\
You are a CMMS analyst assistant with access to both document passages and \
a knowledge graph. Answer the user's question by synthesizing information \
from all the sources below.

--- DOCUMENT PASSAGES ---
{doc_context}

--- EXTRACTED ENTITIES & RELATIONSHIPS ---
{graph_context}

--- CMMS REFERENCES ---
{cmms_context}

Question: {question}

Instructions:
1. Use document passages as your primary source of information.
2. Use the graph entities and relationships to enrich and connect information.
3. Use CMMS references to link document knowledge to known assets, faults, or systems.
4. Cite which source(s) you used for each part of your answer.
5. Be concise but thorough.

Answer:"""

GRAPH_CONTEXT_QUERY = """
// Step 1: Find entities mentioned in the given chunks
MATCH (e:DocEntity)-[:MENTIONED_IN]->(c:DocumentChunk)
WHERE c.chunk_id IN $chunk_ids
WITH collect(DISTINCT e) AS entities, collect(DISTINCT c) AS chunks

// Step 2: Get relationships between those entities
UNWIND entities AS e1
UNWIND entities AS e2
MATCH (e1)-[r:RELATED_TO]->(e2)
WITH entities, chunks, collect({source: e1.name, target: e2.name,
     relation: r.relation_type}) AS relationships

// Step 3: Get extended neighborhood (2 hops)
UNWIND entities AS e
MATCH path = (e)-[:RELATED_TO*1..2]-(neighbor:DocEntity)
WHERE NOT neighbor IN entities
WITH entities, chunks, relationships,
     collect(DISTINCT {
       name: neighbor.name,
       type: neighbor.entity_type,
       description: neighbor.description
     }) AS neighbors

// Step 4: Get CMMS references
UNWIND entities AS e
OPTIONAL MATCH (e)-[:REFERS_TO]->(cmms)
WITH entities, chunks, relationships, neighbors,
     collect(DISTINCT {
       entity_name: e.name,
       cmms_label: labels(cmms)[0],
       cmms_name: cmms.name,
       cmms_pg_id: cmms.pg_id
     }) AS cmms_refs

RETURN entities, chunks, relationships, neighbors, cmms_refs
"""


class GraphRAGPipeline:
    def __init__(self):
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        self.model = settings.openai_llm_model
        self.vector_store = get_vector_store()
        self.embedding_service = get_embedding_service()

    async def query(self, question: str) -> dict:
        logger.info(f"GraphRAG pipeline query: {question[:100]}...")

        # Step 1: Embed query and search Qdrant for relevant chunks
        query_embedding = await asyncio.to_thread(
            self.embedding_service.get_text_embedding, question
        )
        retrieved_docs = await asyncio.to_thread(
            self.vector_store.search,
            query_embedding=query_embedding,
            limit=settings.default_top_k,
            score_threshold=settings.similarity_threshold,
        )

        if not retrieved_docs:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "graph_entities": [],
                "cmms_references": [],
                "mode_used": "graphrag",
            }

        # Step 2: Extract chunk IDs (Qdrant point IDs)
        chunk_ids = [doc["id"] for doc in retrieved_docs]

        # Step 3: Query Neo4j graph around those chunk IDs
        graph_data = await self._query_graph_context(chunk_ids)

        # Step 4: Format all contexts
        doc_context = self._format_doc_context(retrieved_docs)
        graph_context = self._format_graph_context(graph_data)
        cmms_context = self._format_cmms_context(graph_data.get("cmms_refs", []))

        # Step 5: Generate answer using LLM
        prompt = GRAPHRAG_PROMPT.format(
            doc_context=doc_context,
            graph_context=graph_context,
            cmms_context=cmms_context,
            question=question,
        )

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"GraphRAG answer generation failed: {e}")
            answer = (
                "Found relevant documents and graph data "
                f"but couldn't generate an answer: {str(e)}"
            )

        # Build sources list
        sources = [
            {
                "document_id": doc["metadata"].get("document_id"),
                "filename": doc["metadata"].get("file_name", "Unknown"),
                "chunk_index": doc["metadata"].get("chunk_index"),
                "similarity_score": doc["similarity_score"],
                "preview_text": doc["text"][:200] + "..."
                if len(doc["text"]) > 200
                else doc["text"],
            }
            for doc in retrieved_docs
        ]

        # Build graph_entities and cmms_references from graph data
        graph_entities = self._extract_graph_entities(graph_data)
        cmms_references = [ref for ref in graph_data.get("cmms_refs", []) if ref.get("cmms_pg_id")]

        logger.info(
            f"GraphRAG query complete: {len(sources)} sources, "
            f"{len(graph_entities)} entities, {len(cmms_references)} CMMS refs"
        )

        return {
            "answer": answer,
            "sources": sources,
            "graph_entities": graph_entities,
            "cmms_references": cmms_references,
            "mode_used": "graphrag",
        }

    async def _query_graph_context(self, chunk_ids: list[int]) -> dict:
        """Query Neo4j for entities, relationships, and CMMS references around chunk IDs."""
        driver = await get_neo4j_driver()

        try:
            async with driver.session(database=settings.neo4j_database) as session:
                result = await session.run(
                    GRAPH_CONTEXT_QUERY,
                    chunk_ids=chunk_ids,
                )
                records = await result.data()

                if not records:
                    return {
                        "entities": [],
                        "relationships": [],
                        "neighbors": [],
                        "cmms_refs": [],
                    }

                record = records[0]

                # Serialize Neo4j node objects to dicts
                entities = []
                for node in record.get("entities", []):
                    entities.append(dict(node))

                chunks = []
                for node in record.get("chunks", []):
                    chunks.append(dict(node))

                return {
                    "entities": entities,
                    "chunks": chunks,
                    "relationships": record.get("relationships", []),
                    "neighbors": record.get("neighbors", []),
                    "cmms_refs": record.get("cmms_refs", []),
                }

        except Exception as e:
            logger.error(f"Graph context query failed: {e}")
            return {
                "entities": [],
                "relationships": [],
                "neighbors": [],
                "cmms_refs": [],
            }

    def _format_doc_context(self, retrieved_docs: list[dict]) -> str:
        parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc["metadata"].get("file_name", "Unknown")
            score = doc["similarity_score"]
            parts.append(f"[Passage {i} from '{source}' (score: {score:.2f})]\n{doc['text']}")
        return "\n\n".join(parts)

    def _format_graph_context(self, graph_data: dict) -> str:
        parts = []

        entities = graph_data.get("entities", [])
        if entities:
            entity_lines = ["Entities found in relevant passages:"]
            for e in entities:
                entity_lines.append(
                    f"  - {e.get('name', 'Unknown')} ({e.get('entity_type', '?')}): "
                    f"{e.get('description', '')}"
                )
            parts.append("\n".join(entity_lines))

        relationships = graph_data.get("relationships", [])
        if relationships:
            rel_lines = ["Entity relationships:"]
            for r in relationships:
                rel_lines.append(
                    f"  - {r.get('source', '?')} --[{r.get('relation', 'related_to')}]--> "
                    f"{r.get('target', '?')}"
                )
            parts.append("\n".join(rel_lines))

        neighbors = graph_data.get("neighbors", [])
        if neighbors:
            neighbor_lines = ["Related entities (neighborhood):"]
            for n in neighbors:
                neighbor_lines.append(
                    f"  - {n.get('name', 'Unknown')} ({n.get('type', '?')}): "
                    f"{n.get('description', '')}"
                )
            parts.append("\n".join(neighbor_lines))

        return "\n\n".join(parts) if parts else "No graph data available."

    def _format_cmms_context(self, cmms_refs: list[dict]) -> str:
        if not cmms_refs:
            return "No CMMS references found."

        parts = ["Linked CMMS records:"]
        for ref in cmms_refs:
            if ref.get("cmms_pg_id"):
                parts.append(
                    f"  - Entity '{ref.get('entity_name', '?')}' refers to "
                    f"{ref.get('cmms_label', '?')} '{ref.get('cmms_name', '?')}' "
                    f"(ID: {ref.get('cmms_pg_id')})"
                )
        return "\n".join(parts)

    def _extract_graph_entities(self, graph_data: dict) -> list[dict]:
        """Extract a flat list of unique entities for the response."""
        seen = set()
        entities = []

        for e in graph_data.get("entities", []):
            name = e.get("name", "")
            if name and name not in seen:
                seen.add(name)
                entities.append(
                    {
                        "name": name,
                        "entity_type": e.get("entity_type", "Unknown"),
                        "description": e.get("description", ""),
                    }
                )

        for n in graph_data.get("neighbors", []):
            name = n.get("name", "")
            if name and name not in seen:
                seen.add(name)
                entities.append(
                    {
                        "name": name,
                        "entity_type": n.get("type", "Unknown"),
                        "description": n.get("description", ""),
                    }
                )

        return entities


_graphrag_pipeline: Optional[GraphRAGPipeline] = None


def get_graphrag_pipeline() -> GraphRAGPipeline:
    global _graphrag_pipeline
    if _graphrag_pipeline is None:
        _graphrag_pipeline = GraphRAGPipeline()
    return _graphrag_pipeline
