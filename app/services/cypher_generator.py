import re
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings

ALLOWED_CLAUSES = {
    "MATCH", "OPTIONAL", "WHERE", "WITH", "RETURN", "ORDER", "BY",
    "LIMIT", "SKIP", "AS", "AND", "OR", "NOT", "IN", "IS", "NULL",
    "TRUE", "FALSE", "DISTINCT", "COLLECT", "COUNT", "SUM", "AVG",
    "MIN", "MAX", "CONTAINS", "STARTS", "ENDS", "EXISTS", "CALL",
    "YIELD", "UNWIND", "CASE", "WHEN", "THEN", "ELSE", "END",
    "DETACH", "DESC", "ASC", "ON", "SET",
}

BLOCKED_CLAUSES = {"CREATE", "MERGE", "DELETE", "DROP", "REMOVE", "LOAD", "CSV"}

GRAPH_SCHEMA = """
Node labels and properties:
- Asset: pg_id, name, description, asset_type, status, \
location, created_at, updated_at
- Sensor: pg_id, name, sensor_type, unit, status, \
created_at, updated_at
- SensorSummary: sensor_pg_id, window, window_start, window_end, \
avg_value, min_value, max_value, stddev, sample_count, anomaly_flag
- Fault: pg_id, code, name, description, severity, status, \
detected_at, resolved_at, created_at, updated_at
- MaintenanceSchedule: pg_id, title, description, \
maintenance_type, status, priority, scheduled_date, completed_date, \
assigned_to, recurrence, estimated_duration_hours, notes, \
created_at, updated_at

Relationships:
- (Asset)-[:HAS_PARENT]->(Asset)
- (Asset)-[:HAS_SENSOR]->(Sensor)
- (Sensor)-[:HAS_SUMMARY]->(SensorSummary)
- (Asset)-[:HAS_FAULT]->(Fault)
- (Fault)-[:CAUSES]->(Fault)
- (Asset)-[:HAS_MAINTENANCE]->(MaintenanceSchedule)
- (MaintenanceSchedule)-[:ADDRESSES_FAULT]->(Fault)
"""

CYPHER_GEN_PROMPT = """You are a Cypher query generator for a Neo4j CMMS knowledge graph.
Given the graph schema and user question, generate a single READ-ONLY Cypher query.

Schema:
{schema}

Rules:
1. Only use MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT
2. Do NOT use CREATE, MERGE, DELETE, SET, DROP, REMOVE
3. Use parameterized values with $param_name notation
4. Return relevant node properties, not full nodes

Question: {question}

Respond with ONLY the Cypher query, nothing else."""


def validate_cypher(cypher: str) -> bool:
    """Validate that a Cypher query only contains read-only clauses."""
    # Remove string literals and comments
    cleaned = re.sub(r"'[^']*'", "", cypher)
    cleaned = re.sub(r'"[^"]*"', "", cleaned)
    cleaned = re.sub(r"//.*$", "", cleaned, flags=re.MULTILINE)

    # Extract words (potential clause keywords)
    words = re.findall(r"\b([A-Z][A-Z]+)\b", cleaned.upper())

    for word in words:
        if word in BLOCKED_CLAUSES:
            logger.warning(f"Blocked Cypher clause detected: {word}")
            return False

    return True


class CypherGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.model = settings.openai_llm_model

    def generate(self, question: str) -> Optional[str]:
        prompt = CYPHER_GEN_PROMPT.format(schema=GRAPH_SCHEMA, question=question)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.0,
            )
            cypher = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if cypher.startswith("```"):
                cypher = cypher.split("\n", 1)[1]
                cypher = cypher.rsplit("```", 1)[0].strip()

            if not validate_cypher(cypher):
                logger.warning(f"Generated Cypher failed validation: {cypher}")
                return None

            logger.info(f"Generated Cypher: {cypher}")
            return cypher
        except Exception as e:
            logger.error(f"Cypher generation failed: {e}")
            return None


_cypher_generator: Optional[CypherGenerator] = None


def get_cypher_generator() -> CypherGenerator:
    global _cypher_generator
    if _cypher_generator is None:
        _cypher_generator = CypherGenerator()
    return _cypher_generator
