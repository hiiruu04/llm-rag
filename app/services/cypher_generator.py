import re
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings

ALLOWED_CLAUSES = {
    "MATCH",
    "OPTIONAL",
    "WHERE",
    "WITH",
    "RETURN",
    "ORDER",
    "BY",
    "LIMIT",
    "SKIP",
    "AS",
    "AND",
    "OR",
    "NOT",
    "IN",
    "IS",
    "NULL",
    "TRUE",
    "FALSE",
    "DISTINCT",
    "COLLECT",
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "CONTAINS",
    "STARTS",
    "ENDS",
    "EXISTS",
    "CALL",
    "YIELD",
    "UNWIND",
    "CASE",
    "WHEN",
    "THEN",
    "ELSE",
    "END",
    "DETACH",
    "DESC",
    "ASC",
    "ON",
    "SET",
}

BLOCKED_CLAUSES = {"CREATE", "MERGE", "DELETE", "DROP", "REMOVE", "LOAD", "CSV"}

GRAPH_SCHEMA = """
Node labels and properties:
- Asset: pg_id, name, description, asset_type, status, \
location, created_at, updated_at
- Sensor: pg_id, name, sensor_type, unit, status, \
created_at, updated_at
- Fault: pg_id, code, name, description, severity, status, \
detected_at, resolved_at, created_at, updated_at
- MaintenanceSchedule: pg_id, title, description, \
maintenance_type, status, priority, scheduled_date, completed_date, \
assigned_to, recurrence, estimated_duration_hours, notes, \
created_at, updated_at
- Worker: pg_id, name, employee_id, email, phone, status, \
created_at, updated_at
- Role: pg_id, name, description, created_at, updated_at
- Competence: pg_id, name, description, category, \
created_at, updated_at
- Level: pg_id, name, rank, description, created_at, updated_at
- Task: pg_id, name, description, task_type, status, \
estimated_duration_hours, doc_link, created_at, updated_at
- Action: pg_id, name, description, action_type, \
sequence_order, created_at, updated_at
- Cause: pg_id, name, description, category, severity, \
created_at, updated_at
- Material: pg_id, name, part_number, description, \
quantity_in_stock, unit, created_at, updated_at
- Shift: pg_id, name, start_time, end_time, description, \
created_at, updated_at
- DownEvent: pg_id, asset_id, started_at, ended_at, \
downtime_minutes, description, severity, status, \
created_at, updated_at
- Order: pg_id, order_number, title, description, \
order_type, status, priority, requested_date, \
created_at, updated_at
- Location: pg_id, name, description, location_type, \
parent_id, created_at, updated_at
- System: pg_id, name, description, created_at, updated_at
- Aggregate: pg_id, name, description, created_at, updated_at

Relationships:
- (Asset)-[:HAS_PARENT]->(Asset)
- (Asset)-[:HAS_SENSOR]->(Sensor)
- (Asset)-[:HAS_FAULT]->(Fault)
- (Fault)-[:CAUSES]->(Fault)
- (Asset)-[:HAS_MAINTENANCE]->(MaintenanceSchedule)
- (MaintenanceSchedule)-[:ADDRESSES_FAULT]->(Fault)
- (Asset)-[:assigned_to]->(Worker)
- (Worker)-[:has]->(Competence)
- (Worker)-[:works_in]->(Shift)
- (Competence)-[:typeOf]->(Level)
- (Task)-[:requires]->(Competence)
- (Cause)-[:requires]->(Role)
- (Action)-[:requires]->(Competence)
- (Asset)-[:consists_of]->(System)
- (System)-[:part_of]->(Aggregate)
- (Role)-[:enables]->(Task)
- (Asset)-[:is_at]->(Location)
- (Order)-[:booked_on]->(Asset)
- (Material)-[:planned_in]->(Task)
- (DownEvent)-[:has]->(Cause)
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
