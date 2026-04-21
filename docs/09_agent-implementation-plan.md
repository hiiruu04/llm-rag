# Agent Implementation Plan

## Intent Categories (v2 CRM Vocabulary)

| Intent           | Trigger Patterns                                         | Routed To         | Example                                                                          |
|------------------|----------------------------------------------------------|-------------------|----------------------------------------------------------------------------------|
| Scheduling       | shift, roster, availability, assign, planning            | Scheduling Agent  | "Who is available for the Night shift on ES12 tomorrow?"                         |
| Competency       | skill, competence, fitness, stress, can X do, training   | Competency Agent  | "Is Tech Tina cleared for bearing replacement tonight given her load?"           |
| Analysis         | MTTR, MTBF, KPI, report, performance, trend, statistics   | Analyzer Agent    | "What is the MTTR for cooling-system down events on ES12 over the last 90 days?" |
| Recommendation   | failure, anomaly, repair, spare, fix, troubleshoot, why  | Recommender Agent | "ES12 vibration is spiking -- what should we do?"                                |
| Status inquiry   | what's going on, current state, show me                   | Analyzer Agent    | "What's going on with ES12?"                                                     |
| Documentation    | log it, document, record this, close action               | Recommender Agent | "Close action AC-001 with outcome 'bearing replaced, vibration back to baseline'"|

## Architecture

Agents sit between the intent classifier and the existing pipelines. When `mode=auto` or `mode=agent`, the query is classified and dispatched to the appropriate agent. Explicit modes (`vector`, `graph`, `graphrag`, `hybrid`) bypass agents entirely.

```
Query → Intent Classifier → Agent Router → Specific Agent → Pipeline(s) + Services → LLM → Response
```

Each agent:
1. Receives the classified intent + extracted entities
2. Gathers data via Cypher queries + SQL services + vector search (Recommender also uses RAG)
3. Passes gathered context to a domain-specific system prompt for the LLM
4. Returns a structured `AgentResponse`

## New/Modified Files

| File                                      | Action   | Description                                        |
|-------------------------------------------|----------|----------------------------------------------------|
| `app/agents/__init__.py`                  | New      | Package init, exports                              |
| `app/agents/base.py`                      | New      | Agent base class + AgentResponse                   |
| `app/agents/router.py`                    | New      | Intent -> Agent dispatcher                         |
| `app/agents/scheduling_agent.py`           | New      | Scheduling Agent implementation                    |
| `app/agents/competency_agent.py`           | New      | Competency Agent implementation                    |
| `app/agents/analyzer_agent.py`            | New      | Analyzer Agent implementation                      |
| `app/agents/recommender_agent.py`          | New      | Recommender Agent implementation (incl. writes)     |
| `app/services/intent_classifier.py`        | Modify   | New 6-intent taxonomy                              |
| `app/services/kpi_service.py`             | New      | MTTR/MTBF/KPI computation via SQL                  |
| `app/agents/mutation_service.py`           | New      | Write operations wrapper for Recommender           |
| `app/api/routes/query.py`                 | Modify   | Agent routing, /query/agent endpoint              |
| `app/api/models.py`                       | Modify   | Add agent_used field                               |
| `app/mcp/tools/agent_tools.py`             | New      | 4 MCP agent tools                                 |
| `app/mcp/server.py`                        | Modify   | Import agent_tools                                 |

## Phase 1: Foundation

### Agent Base Class (`app/agents/base.py`)

```python
class AgentResponse:
    answer: str
    sources: list[dict]
    graph_entities: list[dict]
    cmms_references: list[dict]
    mode_used: str
    agent_used: str
    data_used: list[str]
    cypher_used: str | None
    tokens_used: dict | None

class Agent(ABC):
    @abstractmethod
    async def handle(question: str, entities: dict) -> AgentResponse: ...

    # Shared helpers:
    async def _execute_cypher(cypher, params) -> list[dict]
    def _format_cypher_results(results) -> str
    def _generate_answer(system_prompt, context, question) -> str
```

### Updated Intent Classifier (`app/services/intent_classifier.py`)

New 6-intent taxonomy replacing the old 5-mode one:
- `scheduling`, `competency`, `analysis`, `recommendation`, `status_inquiry`, `documentation`

When no agent intent matches, fall back to existing pipelines:
- If mode is explicitly set to `vector`/`graph`/`graphrag`/`hybrid`, bypass agents

## Phase 2: Agent Implementations

### Scheduling Agent

- **Data sources**: Shift, Worker, WorkerShift, MaintenanceSchedule, Task, AssetWorker
- **Cypher templates**: `worker_availability`, `maintenance_schedule`, `equipment_workers`
- **SQL services**: shift_service, worker_service, task_service
- **System prompt**: Specialized for shift planning, conflict detection, roster creation
- **Logic**: Gather worker/shift/schedule data -> detect conflicts -> LLM synthesizes scheduling recommendations

### Competency Agent

- **Data sources**: Competence, WorkerCompetence, Level, TaskCompetence, Role, Worker
- **Cypher templates**: `worker_competences`, `worker_availability`, `task_requirements`
- **SQL services**: competence_service, worker queries
- **System prompt**: Specialized for skill assessments, fitness-for-task clearance, training gap analysis
- **Logic**: Match worker competences against task requirements -> identify gaps -> LLM assesses fitness

### Analyzer Agent

- **Data sources**: DownEvent, Fault, SensorData, MaintenanceSchedule, Sensor
- **Cypher templates**: `down_event_analysis`, `statistics`, `fault_chain`, `sensor_status`
- **SQL services**: kpi_service (MTTR, MTBF, availability), down_event_service, fault_service
- **System prompt**: Specialized for metrics interpretation, trend analysis, reporting
- **Logic**: Compute KPIs in Python/SQL -> feed structured results + raw data to LLM -> narrative interpretation
- **Also handles**: `status_inquiry` intent

### Recommender Agent

- **Data sources**: Fault, DownEvent, Cause, Material, Task + RAG doc chunks
- **Cypher templates**: `fault_chain`, `cause_analysis`, `task_requirements`, `material_planning`
- **SQL services**: fault_service, cause_service, material_service, mutation_service
- **System prompt**: Specialized for root cause analysis, repair recommendations, spare part suggestions
- **Also handles**: `documentation` intent with **write operations** (close action, log event, record outcome)
- **Logic**: Gather fault/cause/material context -> optionally RAG for troubleshooting docs -> LLM generates recommendations

## Phase 3: Agent Router & API

### Agent Router (`app/agents/router.py`)

```python
INTENT_AGENT_MAP = {
    "scheduling": SchedulingAgent,
    "competency": CompetencyAgent,
    "analysis": AnalyzerAgent,
    "recommendation": RecommenderAgent,
    "status_inquiry": AnalyzerAgent,
    "documentation": RecommenderAgent,
}
```

- If mode is explicit (`vector`, `graph`, `graphrag`, `hybrid`): bypass agents
- If mode is `auto` or `agent`: classify intent -> dispatch to agent

### Query Route Updates (`app/api/routes/query.py`)

- `QueryRequest.mode` gains `agent` option
- New `/query/agent` endpoint with optional `agent_type` parameter
- Response model gains `agent_used` field

## Phase 4: MCP Integration

4 new MCP tools in `app/mcp/tools/agent_tools.py`:
- `scheduling_agent(question)` -> Scheduling Agent
- `competency_agent(question)` -> Competency Agent
- `analyzer_agent(question)` -> Analyzer Agent
- `recommender_agent(question, mutation)` -> Recommender Agent (optional mutation param for writes)

## Phase 5: KPI Computation

`app/services/kpi_service.py`:
- `compute_mttr(asset_id, fault_id, start_date, end_date)` -> dict
- `compute_mtbf(asset_id, start_date, end_date)` -> dict
- `compute_availability(asset_id, start_date, end_date)` -> dict
- `compute_kpi_summary(asset_name)` -> dict

All using SQL aggregations over down_events, faults, sensor_data tables.

## Phase 6: Write Operations

`app/agents/mutation_service.py`:
- `close_action(action_id, outcome, notes)` -> update task/order status
- `log_event(asset_id, fault_id, description)` -> create down_event
- `record_outcome(task_id, result, notes)` -> update task with results

Called by Recommender Agent when intent is `documentation`.