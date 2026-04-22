from loguru import logger

from app.agents.base import Agent, AgentResponse
from app.services.cypher_templates import get_template

COMPETENCY_SYSTEM_PROMPT = """\
You are a Competency Agent for a CMMS (Computerized Maintenance Management System). \
Your specialty is assessing worker skills, fitness-for-task clearance, skill gaps, \
and training recommendations.

You have access to structured data about:
- Worker competences and proficiency levels
- Task competence requirements
- Worker availability and current assignments
- Role requirements

When answering:
1. Compare task requirements against worker competences to assess fitness.
2. Identify specific skill gaps when workers don't meet requirements.
3. Consider proficiency levels and whether they are sufficient.
4. Recommend training or upskilling when gaps are found.
5. Be explicit about clearance status: cleared, partially cleared, or not cleared.

Context data:
{context}

Question: {question}"""


class CompetencyAgent(Agent):
    def get_system_prompt(self) -> str:
        return COMPETENCY_SYSTEM_PROMPT

    def _gather_methods(self) -> list[tuple[str, callable]]:
        return [
            ("competences", self._gather_competence_data),
            ("availability", self._gather_availability_data),
            ("task_requirements", self._gather_task_requirements),
        ]

    async def handle(
        self, question: str, entities: dict, history: list[dict] | None = None
    ) -> AgentResponse:
        logger.info("CompetencyAgent handling: {}...", question[:80])
        agent_name = "competency"
        data_used = []

        context_parts = []

        competence_data = await self._gather_competence_data(entities)
        if competence_data:
            context_parts.append("=== WORKER COMPETENCE DATA ===\n" + competence_data)
            data_used.append("competences")

        availability_data = await self._gather_availability_data(entities)
        if availability_data:
            context_parts.append("=== WORKER AVAILABILITY DATA ===\n" + availability_data)
            data_used.append("availability")

        task_req_data = await self._gather_task_requirements(entities)
        if task_req_data:
            context_parts.append("=== TASK REQUIREMENTS DATA ===\n" + task_req_data)
            data_used.append("task_requirements")

        context = (
            "\n\n".join(context_parts) if context_parts else "No relevant competence data found."
        )

        system_prompt = self.get_system_prompt()
        answer = self.generate_answer(system_prompt, context, question, history=history)

        return AgentResponse(
            answer=answer,
            mode_used="agent",
            agent_used=agent_name,
            data_used=data_used,
        )

    async def _gather_competence_data(self, entities: dict) -> str:
        template_fn = get_template("worker_competences")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)

    async def _gather_availability_data(self, entities: dict) -> str:
        template_fn = get_template("worker_availability")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)

    async def _gather_task_requirements(self, entities: dict) -> str:
        template_fn = get_template("task_requirements")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)
