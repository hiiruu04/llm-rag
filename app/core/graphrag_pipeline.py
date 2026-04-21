import asyncio
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings
from app.core.embeddings import get_embedding_service
from app.core.neo4j import get_neo4j_driver
from app.core.vector_store import get_vector_store
from app.services.cypher_generator import get_cypher_generator
from app.services.cypher_templates import get_template
from app.services.entity_extractor import get_entity_extractor

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

GRAPH_FALLBACK_PROMPT = """\
You are a CMMS analyst assistant. Answer the user's question based on \
the knowledge graph query results below.
Format your answer with structured information.

--- KNOWLEDGE GRAPH RESULTS ---
{graph_context}

Question: {question}

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
        logger.info("GraphRAG pipeline query: {}...", question[:100])
        logger.debug("[Step 1] Embedding query and searching vector store")
        logger.debug(
            "[Step 1] Vector store config: collection={}, limit={}, threshold={}",
            settings.qdrant_collection_name,
            settings.default_top_k,
            settings.similarity_threshold,
        )

        # Step 1: Embed query and search Qdrant for relevant chunks
        query_embedding = await asyncio.to_thread(
            self.embedding_service.get_text_embedding, question
        )
        logger.debug("[Step 1] Query embedding generated: dim={}", len(query_embedding))

        retrieved_docs = await asyncio.to_thread(
            self.vector_store.search,
            query_embedding=query_embedding,
            limit=settings.default_top_k,
            score_threshold=settings.similarity_threshold,
        )
        logger.debug("[Step 1] Vector search returned {} docs", len(retrieved_docs))
        for i, doc in enumerate(retrieved_docs):
            logger.debug(
                "[Step 1]   doc[{}]: id={} score={} file={}",
                i,
                doc["id"],
                doc["similarity_score"],
                doc["metadata"].get("file_name", "?"),
            )

        if not retrieved_docs:
            logger.info("[Fallback] No vector results, falling back to direct graph query")
            return await self._fallback_graph_query(question)

        # Step 2: Extract chunk IDs (Qdrant point IDs)
        chunk_ids = [doc["id"] for doc in retrieved_docs]
        logger.debug("[Step 2] Extracted chunk IDs: {}", chunk_ids)

        # Step 3: Query Neo4j graph around those chunk IDs
        logger.debug("[Step 3] Querying Neo4j graph context for chunk IDs")
        graph_data = await self._query_graph_context(chunk_ids)
        logger.debug(
            "[Step 3] Graph context retrieved: entities={} relationships={} "
            "neighbors={} cmms_refs={} direct_cmms_refs={}",
            len(graph_data.get("entities", [])),
            len(graph_data.get("relationships", [])),
            len(graph_data.get("neighbors", [])),
            len(graph_data.get("cmms_refs", [])),
            len(graph_data.get("direct_cmms_refs", [])),
        )

        # Step 4: Format all contexts
        logger.debug("[Step 4] Formatting contexts for LLM prompt")
        doc_context = self._format_doc_context(retrieved_docs)
        graph_context = self._format_graph_context(graph_data)
        cmms_context = self._format_cmms_context(
            graph_data.get("cmms_refs", []),
            graph_data.get("direct_cmms_refs", []),
        )
        logger.debug(
            "[Step 4] Context sizes: doc={} chars, graph={} chars, cmms={} chars",
            len(doc_context),
            len(graph_context),
            len(cmms_context),
        )

        # Step 5: Generate answer using LLM
        logger.debug("[Step 5] Generating answer with LLM")
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
            logger.debug("[Step 5] LLM answer generated: {} chars", len(answer))
        except Exception as e:
            logger.error("[Step 5] GraphRAG answer generation failed: {}", e)
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

        result = {
            "answer": answer,
            "sources": sources,
            "graph_entities": graph_entities,
            "cmms_references": cmms_references,
            "mode_used": "graphrag",
        }

        logger.debug(
            "GraphRAG query result | mode={} | sources={} | entities={} | "
            "cmms_refs={} | direct_cmms_refs={} | answer={}",
            result["mode_used"],
            len(sources),
            len(graph_entities),
            len(cmms_references),
            len(graph_data.get("direct_cmms_refs", [])),
            answer[:200],
        )
        logger.debug("GraphRAG sources: {}", sources)
        logger.debug("GraphRAG graph_entities: {}", graph_entities)
        logger.debug("GraphRAG cmms_references: {}", cmms_references)
        logger.debug(
            "GraphRAG direct_cmms_refs: {}",
            graph_data.get("direct_cmms_refs", []),
        )

        return result

    async def _query_graph_context(self, chunk_ids: list[int]) -> dict:
        """Query Neo4j for entities, relationships, and CMMS references around chunk IDs."""
        driver = await get_neo4j_driver()
        logger.debug(
            "[Graph Context] Querying with chunk_ids={} (db={})",
            chunk_ids,
            settings.neo4j_database,
        )

        try:
            async with driver.session(database=settings.neo4j_database) as session:
                result = await session.run(
                    GRAPH_CONTEXT_QUERY,
                    chunk_ids=chunk_ids,
                )
                records = await result.data()
                logger.debug("[Graph Context] Neo4j returned {} records", len(records))

                if not records:
                    logger.debug("[Graph Context] No records returned from Neo4j")
                    return {
                        "entities": [],
                        "relationships": [],
                        "neighbors": [],
                        "cmms_refs": [],
                        "direct_cmms_refs": [],
                    }

                record = records[0]

                # Serialize Neo4j node objects to dicts
                entities = []
                for node in record.get("entities", []):
                    entities.append(dict(node))

                chunks = []
                for node in record.get("chunks", []):
                    chunks.append(dict(node))

                logger.debug(
                    "[Graph Context] Parsed: {} entities, {} chunks, "
                    "{} relationships, {} neighbors, {} cmms_refs, {} direct_cmms_refs",
                    len(entities),
                    len(chunks),
                    len(record.get("relationships", [])),
                    len(record.get("neighbors", [])),
                    len(record.get("cmms_refs", [])),
                    len(record.get("direct_cmms_refs", [])),
                )

                return {
                    "entities": entities,
                    "chunks": chunks,
                    "relationships": record.get("relationships", []),
                    "neighbors": record.get("neighbors", []),
                    "cmms_refs": record.get("cmms_refs", []),
                    "direct_cmms_refs": record.get("direct_cmms_refs", []),
                }

        except Exception as e:
            logger.error(f"Graph context query failed: {e}")
            return {
                "entities": [],
                "relationships": [],
                "neighbors": [],
                "cmms_refs": [],
                "direct_cmms_refs": [],
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

    def _format_cmms_context(self, cmms_refs: list[dict], direct_cmms_refs: list[dict]) -> str:
        parts = []

        if cmms_refs:
            entity_parts = ["Linked CMMS records (via entity):"]
            for ref in cmms_refs:
                if ref.get("cmms_pg_id"):
                    entity_parts.append(
                        f"  - Entity '{ref.get('entity_name', '?')}' refers to "
                        f"{ref.get('cmms_label', '?')} '{ref.get('cmms_name', '?')}' "
                        f"(ID: {ref.get('cmms_pg_id')})"
                    )
            parts.append("\n".join(entity_parts))

        if direct_cmms_refs:
            direct_parts = ["Direct CMMS -> Document links:"]
            for ref in direct_cmms_refs:
                if ref.get("cmms_pg_id"):
                    direct_parts.append(
                        f"  - {ref.get('cmms_label', '?')} '{ref.get('cmms_name', '?')}' "
                        f"(ID: {ref.get('cmms_pg_id')}) has document chunk "
                        f"{ref.get('chunk_id')}"
                    )
            parts.append("\n".join(direct_parts))

        if not parts:
            return "No CMMS references found."

        return "\n\n".join(parts)

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

    async def _fallback_graph_query(self, question: str) -> dict:
        """Fallback: query the knowledge graph directly when vector search finds nothing."""
        logger.debug("[Fallback Step 1] Extracting entities from question")
        entity_extractor = get_entity_extractor()
        cypher_generator = get_cypher_generator()

        # Step 1: Extract entities from question
        entities = entity_extractor.extract(question)
        query_type = entities.get("query_type", "search")
        logger.debug(
            "[Fallback Step 1] Extracted entities: query_type={}, entities={}",
            query_type,
            entities,
        )

        # Step 2: Try template-based Cypher first, then LLM-generated
        logger.debug(
            "[Fallback Step 2] Resolving Cypher (template for '{}' then LLM fallback)",
            query_type,
        )
        cypher, params = self._get_fallback_cypher(
            query_type, entities, question, cypher_generator
        )
        logger.debug(
            "[Fallback Step 2] Cypher resolved: {} | params: {}",
            cypher,
            params,
        )
        if not cypher:
            logger.debug("[Fallback Step 2] No Cypher could be generated")
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "graph_entities": [],
                "cmms_references": [],
                "mode_used": "graphrag_fallback",
                "cypher_used": None,
            }

        # Step 3: Execute Cypher against Neo4j
        logger.debug("[Fallback Step 3] Executing Cypher against Neo4j")
        try:
            results = await self._execute_fallback_cypher(cypher, params)
            logger.debug("[Fallback Step 3] Neo4j returned {} results", len(results))
        except Exception as e:
            logger.error("[Fallback Step 3] Cypher execution failed: {}", e)
            return {
                "answer": f"Error querying the knowledge graph: {str(e)}",
                "sources": [],
                "graph_entities": [],
                "cmms_references": [],
                "mode_used": "graphrag_fallback",
                "cypher_used": cypher,
            }

        if not results:
            logger.debug("[Fallback Step 3] No results from graph query")
            return {
                "answer": "No results found in the knowledge graph for your query.",
                "sources": [],
                "graph_entities": [],
                "cmms_references": [],
                "mode_used": "graphrag_fallback",
                "cypher_used": cypher,
            }

        # Step 4: Format and generate answer
        logger.debug("[Fallback Step 4] Formatting results and generating answer")
        graph_context = self._format_fallback_results(results)
        prompt = GRAPH_FALLBACK_PROMPT.format(graph_context=graph_context, question=question)
        logger.debug(
            "[Fallback Step 4] Graph context ({} chars): {}",
            len(graph_context),
            graph_context[:500],
        )

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
            answer = response.choices[0].message.content.strip()
            logger.debug("[Fallback Step 4] LLM answer generated: {} chars", len(answer))
        except Exception as e:
            logger.error("[Fallback Step 4] Answer generation failed: {}", e)
            answer = f"Found graph data but couldn't generate an answer: {str(e)}"

        result = {
            "answer": answer,
            "sources": [],
            "graph_entities": [],
            "cmms_references": [],
            "mode_used": "graphrag_fallback",
            "cypher_used": cypher,
        }

        logger.debug(
            "GraphRAG fallback result | mode={} | cypher={} | graph_results={} | answer={}",
            result["mode_used"],
            cypher,
            len(results),
            answer[:200],
        )
        logger.debug("GraphRAG fallback cypher_used: {}", cypher)
        logger.debug("GraphRAG fallback graph_results: {}", results)

        return result

    def _get_fallback_cypher(
        self,
        query_type: str,
        entities: dict,
        question: str,
        cypher_generator,
    ) -> tuple:
        """Get Cypher query: try template first, then LLM-generated."""
        template_fn = get_template(query_type)
        if template_fn:
            cypher, params = template_fn(entities)
            logger.info(f"Fallback: using template for {query_type}")
            return cypher, params

        cypher = cypher_generator.generate(question)
        if cypher:
            return cypher, {}

        return None, {}

    async def _execute_fallback_cypher(self, cypher: str, params: dict) -> list[dict]:
        """Execute a Cypher query against Neo4j."""
        driver = await get_neo4j_driver()
        async with driver.session(database=settings.neo4j_database) as session:
            result = await session.run(cypher, **params)
            records = await result.data()
        return records

    def _format_fallback_results(self, results: list[dict]) -> str:
        """Format graph query results into a string for the LLM prompt."""
        parts = []
        for i, record in enumerate(results, 1):
            lines = [f"[Graph Result {i}]"]
            for key, value in record.items():
                if value is not None:
                    lines.append(f"  {key}: {value}")
            parts.append("\n".join(lines))
        return "\n\n".join(parts)


_graphrag_pipeline: Optional[GraphRAGPipeline] = None


def get_graphrag_pipeline() -> GraphRAGPipeline:
    global _graphrag_pipeline
    if _graphrag_pipeline is None:
        _graphrag_pipeline = GraphRAGPipeline()
    return _graphrag_pipeline
