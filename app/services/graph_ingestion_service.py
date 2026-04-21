import hashlib
from typing import Optional

from loguru import logger

from app.core.config import settings
from app.core.neo4j import get_neo4j_driver
from app.services.document_entity_extractor import get_document_entity_extractor
from app.services.entity_linking_service import get_entity_linking_service


def _generate_point_id(document_id: str, chunk_index: int) -> int:
    unique_string = f"{document_id}_{chunk_index}"
    hash_obj = hashlib.md5(unique_string.encode())
    return int(hash_obj.hexdigest()[:8], 16)


class GraphIngestionService:
    async def ingest_document_graph(
        self,
        document_id: str,
        chunks: list[dict],
        file_name: str,
    ) -> dict:
        """Ingest document chunks and extracted entities into Neo4j.

        Called after Qdrant storage to create the graph representation:
        - DocumentChunk nodes (linked by chunk_id to Qdrant point IDs)
        - DocEntity nodes (extracted via LLM)
        - MENTIONED_IN relationships
        - RELATED_TO relationships between entities
        - NEXT_CHUNK sequential relationships
        - REFERS_TO links to CMMS nodes
        """
        logger.info(f"Starting graph ingestion for document {document_id}")

        driver = await get_neo4j_driver()
        extractor = get_document_entity_extractor()

        all_entities = {}  # name -> entity dict (dedup across chunks)
        entity_chunk_map = []  # [(entity_name, chunk_id)]
        all_relationships = []

        # Step 1: Create DocumentChunk nodes and extract entities per chunk
        chunk_ids = []
        async with driver.session(database=settings.neo4j_database) as session:
            for i, chunk in enumerate(chunks):
                text = chunk.get("text", "").strip()
                if not text:
                    continue

                chunk_index = chunk.get("metadata", {}).get("chunk_index", i)
                chunk_id = _generate_point_id(document_id, chunk_index)
                chunk_ids.append(chunk_id)

                # Create DocumentChunk node
                await session.run(
                    """
                    MERGE (c:DocumentChunk {chunk_id: $chunk_id})
                    SET c.document_id = $document_id,
                        c.chunk_index = $chunk_index,
                        c.text = $text,
                        c.file_name = $file_name
                    """,
                    chunk_id=chunk_id,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    text=text[:2000],  # Store truncated text for context
                    file_name=file_name,
                )

                # Extract entities from this chunk
                extraction = extractor.extract(text, document_id)
                entities = extraction.get("entities", [])
                relationships = extraction.get("relationships", [])

                # Deduplicate entities by name across chunks
                for entity in entities:
                    name_key = entity["name"].lower().strip()
                    if name_key not in all_entities:
                        all_entities[name_key] = entity
                    entity_chunk_map.append((name_key, chunk_id))

                all_relationships.extend(relationships)

            # Step 2: Create NEXT_CHUNK relationships for sequential ordering
            for idx in range(len(chunk_ids) - 1):
                await session.run(
                    """
                    MATCH (a:DocumentChunk {chunk_id: $chunk_id_a})
                    MATCH (b:DocumentChunk {chunk_id: $chunk_id_b})
                    MERGE (a)-[:NEXT_CHUNK]->(b)
                    """,
                    chunk_id_a=chunk_ids[idx],
                    chunk_id_b=chunk_ids[idx + 1],
                )

        # Step 3: Create DocEntity nodes and MENTIONED_IN relationships
        async with driver.session(database=settings.neo4j_database) as session:
            for name_key, entity in all_entities.items():
                await session.run(
                    """
                    MERGE (e:DocEntity {entity_id: $entity_id})
                    SET e.name = $name,
                        e.entity_type = $entity_type,
                        e.description = $description,
                        e.source_document_id = $source_document_id
                    """,
                    entity_id=entity["entity_id"],
                    name=entity["name"],
                    entity_type=entity.get("entity_type", "Unknown"),
                    description=entity.get("description", ""),
                    source_document_id=entity.get("source_document_id", document_id),
                )

            # Create MENTIONED_IN relationships
            for name_key, chunk_id in entity_chunk_map:
                entity = all_entities[name_key]
                await session.run(
                    """
                    MATCH (e:DocEntity {entity_id: $entity_id})
                    MATCH (c:DocumentChunk {chunk_id: $chunk_id})
                    MERGE (e)-[:MENTIONED_IN]->(c)
                    """,
                    entity_id=entity["entity_id"],
                    chunk_id=chunk_id,
                )

            # Step 4: Create RELATED_TO relationships between entities
            for rel in all_relationships:
                source_key = rel.get("source", "").lower().strip()
                target_key = rel.get("target", "").lower().strip()
                relation = rel.get("relation", "related_to")

                if source_key in all_entities and target_key in all_entities:
                    await session.run(
                        """
                        MATCH (s:DocEntity {entity_id: $source_id})
                        MATCH (t:DocEntity {entity_id: $target_id})
                        MERGE (s)-[r:RELATED_TO]->(t)
                        SET r.relation_type = $relation_type
                        """,
                        source_id=all_entities[source_key]["entity_id"],
                        target_id=all_entities[target_key]["entity_id"],
                        relation_type=relation,
                    )

        # Step 5: Link entities to CMMS nodes
        entity_list = list(all_entities.values())
        linking_service = get_entity_linking_service()
        cmms_links = await linking_service.link_entities_to_cmms(entity_list)

        async with driver.session(database=settings.neo4j_database) as session:
            for link in cmms_links:
                await session.run(
                    """
                    MATCH (e:DocEntity {entity_id: $entity_id})
                    MATCH (c) WHERE c.pg_id = $pg_id AND $label IN labels(c)
                    MERGE (e)-[:REFERS_TO]->(c)
                    """,
                    entity_id=link["entity_id"],
                    pg_id=link["cmms_pg_id"],
                    label=link["cmms_label"],
                )

        # Step 6: Create direct CMMS -> DocumentChunk relationships
        entity_id_to_chunks: dict[str, set[int]] = {}
        for name_key, chunk_id in entity_chunk_map:
            eid = all_entities[name_key]["entity_id"]
            entity_id_to_chunks.setdefault(eid, set()).add(chunk_id)

        cmms_chunk_pairs = []
        for link in cmms_links:
            for cid in entity_id_to_chunks.get(link["entity_id"], set()):
                cmms_chunk_pairs.append(
                    {
                        "pg_id": link["cmms_pg_id"],
                        "label": link["cmms_label"],
                        "chunk_id": cid,
                    }
                )

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
            logger.info(f"Created {len(cmms_chunk_pairs)} HAS_DOCUMENT relationships")

        result = {
            "document_id": document_id,
            "chunks_created": len(chunk_ids),
            "entities_created": len(all_entities),
            "relationships_created": len(all_relationships),
            "cmms_links": len(cmms_links),
            "has_document_links": len(cmms_chunk_pairs),
        }

        logger.info(
            f"Graph ingestion complete for {document_id}: "
            f"{result['chunks_created']} chunks, "
            f"{result['entities_created']} entities, "
            f"{result['relationships_created']} relationships, "
            f"{result['cmms_links']} CMMS links, "
            f"{result['has_document_links']} HAS_DOCUMENT links"
        )

        return result

    async def delete_document_graph(self, document_id: str) -> bool:
        """Delete all graph data (DocumentChunk + DocEntity) for a document."""
        logger.info(f"Deleting graph data for document {document_id}")

        try:
            driver = await get_neo4j_driver()
            async with driver.session(database=settings.neo4j_database) as session:
                # Delete DocumentChunk nodes and their relationships
                await session.run(
                    """
                    MATCH (c:DocumentChunk {document_id: $document_id})
                    DETACH DELETE c
                    """,
                    document_id=document_id,
                )

                # Delete DocEntity nodes that originated from this document
                # Only delete if not also referenced by other documents
                await session.run(
                    """
                    MATCH (e:DocEntity {source_document_id: $document_id})
                    WHERE NOT EXISTS {
                        MATCH (e)-[:MENTIONED_IN]->(c:DocumentChunk)
                        WHERE c.document_id <> $document_id
                    }
                    DETACH DELETE e
                    """,
                    document_id=document_id,
                )

            logger.info(f"Graph data deleted for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting graph data for document {document_id}: {e}")
            return False


_graph_ingestion_service: Optional[GraphIngestionService] = None


def get_graph_ingestion_service() -> GraphIngestionService:
    global _graph_ingestion_service
    if _graph_ingestion_service is None:
        _graph_ingestion_service = GraphIngestionService()
    return _graph_ingestion_service
