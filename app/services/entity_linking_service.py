from typing import Optional

from loguru import logger

from app.core.config import settings
from app.core.neo4j import get_neo4j_driver

# CMMS node labels to search for entity linking
CMMS_LABELS = ["Asset", "Fault", "Sensor", "Location", "Worker", "Task", "Material"]


class EntityLinkingService:
    async def link_entities_to_cmms(self, entities: list[dict]) -> list[dict]:
        """Link DocEntity nodes to existing CMMS nodes via fuzzy name matching.

        Returns a list of dicts with entity_id, cmms_label, cmms_pg_id, and score.
        """
        if not entities:
            return []

        driver = await get_neo4j_driver()
        links = []

        async with driver.session(database=settings.neo4j_database) as session:
            for entity in entities:
                name = entity.get("name", "")
                if not name:
                    continue

                best_match = await self._find_best_match(session, name)
                if best_match:
                    links.append(
                        {
                            "entity_id": entity["entity_id"],
                            "cmms_label": best_match["label"],
                            "cmms_pg_id": best_match["pg_id"],
                            "cmms_name": best_match["name"],
                            "score": best_match["score"],
                        }
                    )
                    logger.info(
                        f"Linked entity '{name}' to {best_match['label']} "
                        f"'{best_match['name']}' (score: {best_match['score']:.2f})"
                    )

        logger.info(f"Linked {len(links)} entities to CMMS nodes")
        return links

    async def _find_best_match(self, session, name: str) -> Optional[dict]:
        """Use fulltext indexes to find the best CMMS match for an entity name."""
        best_match = None

        for label in CMMS_LABELS:
            index_name = f"{label.lower()}_name_search"
            try:
                result = await session.run(
                    "CALL db.index.fulltext.queryNodes($index_name, $search_term, "
                    "{limit: 1}) YIELD node, score "
                    "RETURN node.pg_id AS pg_id, node.name AS name, "
                    "labels(node)[0] AS label, score",
                    index_name=index_name,
                    search_term=name,
                )
                records = await result.data()
                if records and records[0]["score"] > 0.5:
                    if best_match is None or records[0]["score"] > best_match["score"]:
                        best_match = records[0]
            except Exception as e:
                logger.debug(f"Fulltext search on {index_name} failed: {e}")
                continue

        return best_match


_entity_linking_service: Optional[EntityLinkingService] = None


def get_entity_linking_service() -> EntityLinkingService:
    global _entity_linking_service
    if _entity_linking_service is None:
        _entity_linking_service = EntityLinkingService()
    return _entity_linking_service
