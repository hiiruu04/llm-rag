from loguru import logger

from app.agents.base import Agent, AgentResponse, _get_mutations_for_agent
from app.services.cypher_templates import get_template
from app.services.kpi_service import (
    compute_kpi_summary,
)

ANALYZER_SYSTEM_PROMPT = """\
You are an Analyzer Agent for a CMMS (Computerized Maintenance Management System). \
Your specialty is computing and interpreting performance metrics, analyzing trends, \
generating reports, and providing status overviews.

You have access to:
- Pre-computed KPI data (MTTR, MTBF, availability percentages)
- Down event analysis data
- Fault chain information
- Sensor status data
- Performance statistics

When answering:
1. Present metrics clearly with units (hours, minutes, percentages).
2. Compare current values against benchmarks when possible.
3. Identify trends (improving, degrading, stable).
4. Highlight anomalies or critical issues.
5. Provide actionable insights based on the data.
6. For status inquiries, give a comprehensive overview of the current state.

IMPORTANT - TOOL CALL RULES:
- When the user asks you to log an event, close an event, or update fault severity, \
use the available tool calls to execute the action immediately. Do NOT just describe what \
command to run.
- All id parameters (asset_id, fault_id, down_event_id) MUST be valid UUID strings in \
the format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx. Do NOT pass names, numbers, or other \
non-UUID values.
- Always extract the exact UUID from the context data above. If you cannot find a UUID \
in the context, tell the user you don't have the ID and ask them to provide it.

Context data:
{context}

Question: {question}"""


class AnalyzerAgent(Agent):
    def get_system_prompt(self) -> str:
        return ANALYZER_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        return "analyzer"

    def _gather_methods(self) -> list[tuple[str, callable]]:
        return [
            ("kpi_metrics", self._gather_kpi_data),
            ("down_events", self._gather_down_event_data),
            ("faults", self._gather_fault_data),
            ("sensors", self._gather_sensor_data),
            ("statistics", self._gather_statistics),
        ]

    async def handle(
        self, question: str, entities: dict, history: list[dict] | None = None
    ) -> AgentResponse:
        logger.info("AnalyzerAgent handling: {}...", question[:80])
        data_used = []

        context_parts = []

        kpi_data = await self._gather_kpi_data(entities)
        if kpi_data:
            context_parts.append("=== KPI METRICS ===\n" + kpi_data)
            data_used.append("kpi_metrics")

        down_event_data = await self._gather_down_event_data(entities)
        if down_event_data:
            context_parts.append("=== DOWN EVENT ANALYSIS ===\n" + down_event_data)
            data_used.append("down_events")

        fault_data = await self._gather_fault_data(entities)
        if fault_data:
            context_parts.append("=== FAULT DATA ===\n" + fault_data)
            data_used.append("faults")

        sensor_data = await self._gather_sensor_data(entities)
        if sensor_data:
            context_parts.append("=== SENSOR STATUS ===\n" + sensor_data)
            data_used.append("sensors")

        statistics_data = await self._gather_statistics(entities)
        if statistics_data:
            context_parts.append("=== STATISTICS ===\n" + statistics_data)
            data_used.append("statistics")

        context = (
            "\n\n".join(context_parts) if context_parts else "No relevant analysis data found."
        )

        system_prompt = self.get_system_prompt()
        tools = _get_mutations_for_agent("analyzer")
        mutations = []

        if tools:
            answer, mutations = await self.execute_agentic_loop(
                "analyzer", system_prompt, context, question, tools, history=history
            )
        else:
            answer = self.generate_answer(system_prompt, context, question, history=history)

        return AgentResponse(
            answer=answer,
            mode_used="agent",
            agent_used="analyzer",
            data_used=data_used,
            mutations=mutations,
        )

    async def _gather_kpi_data(self, entities: dict) -> str:
        try:
            asset_name = None
            if entities.get("asset_names"):
                asset_name = entities["asset_names"][0]
            kpi_data = await compute_kpi_summary(asset_name=asset_name)
            if not kpi_data:
                return ""
            parts = []
            if "mttr" in kpi_data:
                mttr = kpi_data["mttr"]
                mean = mttr.get("mean_minutes", "N/A")
                cnt = mttr.get("count", 0)
                parts.append(f"MTTR: {mean} minutes (count: {cnt})")
            if "mtbf" in kpi_data:
                mtbf = kpi_data["mtbf"]
                mean = mtbf.get("mean_minutes", "N/A")
                cnt = mtbf.get("count", 0)
                parts.append(f"MTBF: {mean} minutes (count: {cnt})")
            if "availability" in kpi_data:
                avail = kpi_data["availability"]
                pct = avail.get("percentage", "N/A")
                up = avail.get("uptime_minutes", "N/A")
                down = avail.get("downtime_minutes", "N/A")
                parts.append(f"Availability: {pct}% (uptime: {up} min, downtime: {down} min)")
            return "\n".join(parts) if parts else ""
        except Exception as e:
            logger.error(f"KPI data gathering failed: {e}")
            return ""

    async def _gather_down_event_data(self, entities: dict) -> str:
        template_fn = get_template("down_event_analysis")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)

    async def _gather_fault_data(self, entities: dict) -> str:
        template_fn = get_template("fault_chain")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)

    async def _gather_sensor_data(self, entities: dict) -> str:
        template_fn = get_template("sensor_status")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)

    async def _gather_statistics(self, entities: dict) -> str:
        template_fn = get_template("statistics")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)
