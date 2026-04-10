import json
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings

ENTITY_PROMPT = """\
Extract structured entities from this CMMS-related query. \
Return a JSON object with these fields (use null for any not found):

{{
  "asset_names": ["name1"] or null,
  "asset_types": ["machine"] or null,
  "fault_codes": ["VIB-001"] or null,
  "fault_severities": ["high"] or null,
  "sensor_types": ["temperature"] or null,
  "maintenance_types": ["preventive"] or null,
  "maintenance_statuses": ["overdue"] or null,
  "time_range": {{
    "start": "ISO date or null",
    "end": "ISO date or null",
    "relative": "last 7 days or null"
  }} or null,
  "locations": ["Building A"] or null,
  "query_type": "asset_tree | fault_chain | sensor_status | "
    "maintenance_schedule | relationship | statistics | search"
}}

Query types:
- asset_tree: asking about asset hierarchy, parent-child, structure
- fault_chain: asking about fault cause-effect propagation
- sensor_status: asking about sensor readings or summaries
- maintenance_schedule: asking about maintenance schedules or overdue items
- relationship: asking about connections between entities
- statistics: asking for counts, aggregations, summaries
- search: general search for entities

Respond with ONLY the JSON object.

Query: {question}"""


class EntityExtractor:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.model = settings.openai_llm_model

    def extract(self, question: str) -> dict:
        prompt = ENTITY_PROMPT.format(question=question)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.0,
            )
            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            entities = json.loads(content)
            logger.info(f"Extracted entities: {entities}")
            return entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {"query_type": "search"}


_entity_extractor: Optional[EntityExtractor] = None


def get_entity_extractor() -> EntityExtractor:
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
    return _entity_extractor
