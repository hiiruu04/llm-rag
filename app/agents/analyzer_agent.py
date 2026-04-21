from loguru import logger

from app.agents.base import Agent, AgentResponse
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

Context data:
{context}

Question: {question}"""


class AnalyzerAgent(Agent):
    def get_system_prompt(self) -> str:
        return ANALYZER_SYSTEM_PROMPT

    async def handle(self, question: str, entities: dict) -> AgentResponse:
        logger.info("AnalyzerAgent handling: {}...", question[:80])
        agent_name = "analyzer"
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
        answer = self.generate_answer(system_prompt, context, question)

        return AgentResponse(
            answer=answer,
            mode_used="agent",
            agent_used=agent_name,
            data_used=data_used,
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
