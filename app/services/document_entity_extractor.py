import json
import uuid
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings

EXTRACTION_PROMPT = """\
You are an expert entity and relationship extractor for industrial/CMMS documents.
Analyze the following text chunk and extract entities and relationships.

Entity types to look for:
- Equipment: Machines, devices, or systems mentioned
- Component: Parts or sub-components of equipment
- Procedure: Maintenance procedures, operating steps, safety protocols
- FailureMode: Types of failures, faults, or malfunctions described
- Material: Materials, consumables, or spare parts mentioned
- Symptom: Observable signs, indicators, or warning signals
- Measurement: Numerical values, tolerances, specifications
- Action: Tasks, operations, or corrective actions
- Specification: Technical specs, standards, or requirements
- Person: People, roles, or positions mentioned
- Location: Places, areas, or physical locations

For each entity provide:
- name: A short canonical name
- entity_type: One of the types listed above
- description: Brief description of what this entity is in context

For relationships between entities provide:
- source: Name of the source entity
- target: Name of the target entity
- relation: Type of relationship (e.g., "has_component", "causes", "requires", \
"located_in", "performed_on", "measures", "related_to")

IMPORTANT: Return valid JSON only. Respond with this exact structure:
{{
  "entities": [
    {{"name": "...", "entity_type": "...", "description": "..."}}
  ],
  "relationships": [
    {{"source": "...", "target": "...", "relation": "..."}}
  ]
}}

If no entities or relationships are found, return empty arrays.
Maximum {max_entities} entities.

Text chunk:
{text}"""


class DocumentEntityExtractor:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.model = settings.openai_llm_model
        self.max_entities = settings.graphrag_max_entities_per_chunk

    def extract(self, text: str, document_id: str) -> dict:
        logger.info(f"Extracting entities from chunk ({len(text)} chars) of doc {document_id}")

        prompt = EXTRACTION_PROMPT.format(
            text=text[:3000],  # Limit text to avoid token overflow
            max_entities=self.max_entities,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.0,
            )
            content = response.choices[0].message.content.strip()

            # Parse JSON - handle possible markdown code fences
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])

            result = json.loads(content)

            entities = result.get("entities", [])
            relationships = result.get("relationships", [])

            # Assign unique IDs to entities
            for entity in entities:
                entity["entity_id"] = str(uuid.uuid4())
                entity["source_document_id"] = document_id

            logger.info(
                f"Extracted {len(entities)} entities and "
                f"{len(relationships)} relationships from doc {document_id}"
            )

            return {"entities": entities, "relationships": relationships}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse entity extraction JSON: {e}")
            return {"entities": [], "relationships": []}
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {"entities": [], "relationships": []}


_document_entity_extractor: Optional[DocumentEntityExtractor] = None


def get_document_entity_extractor() -> DocumentEntityExtractor:
    global _document_entity_extractor
    if _document_entity_extractor is None:
        _document_entity_extractor = DocumentEntityExtractor()
    return _document_entity_extractor
