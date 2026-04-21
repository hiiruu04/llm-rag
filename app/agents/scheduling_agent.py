from loguru import logger

from app.agents.base import Agent, AgentResponse
from app.services.cypher_templates import get_template

SCHEDULING_SYSTEM_PROMPT = """\
You are a Scheduling Agent for a CMMS (Computerized Maintenance Management System). \
Your specialty is workforce planning, shift management, task assignment, and scheduling.

You have access to structured data about:
- Workers, their shifts, and availability
- Maintenance schedules and their tasks
- Equipment-to-worker assignments
- Task requirements (competences, materials)

When answering:
1. Always consider worker availability, shift constraints, and competence requirements.
2. Identify scheduling conflicts or gaps.
3. Propose concrete assignments with specific workers, shifts, and timeframes.
4. If data is incomplete, say so clearly rather than speculating.
5. Present schedules in a clear, structured format.

Context data:
{context}

Question: {question}"""


class SchedulingAgent(Agent):
    def get_system_prompt(self) -> str:
        return SCHEDULING_SYSTEM_PROMPT

    async def handle(self, question: str, entities: dict) -> AgentResponse:
        logger.info("SchedulingAgent handling: {}...", question[:80])
        agent_name = "scheduling"
        data_used = []

        context_parts = []

        shift_data = await self._gather_shift_data(entities)
        if shift_data:
            context_parts.append("=== SHIFT & AVAILABILITY DATA ===\n" + shift_data)
            data_used.append("shifts")

        schedule_data = await self._gather_schedule_data(entities)
        if schedule_data:
            context_parts.append("=== MAINTENANCE SCHEDULE DATA ===\n" + schedule_data)
            data_used.append("schedules")

        task_data = await self._gather_task_data(entities)
        if task_data:
            context_parts.append("=== TASK & ASSIGNMENT DATA ===\n" + task_data)
            data_used.append("tasks")

        worker_data = await self._gather_worker_assignment_data(entities)
        if worker_data:
            context_parts.append("=== EQUIPMENT-WORKER ASSIGNMENTS ===\n" + worker_data)
            data_used.append("worker_assignments")

        context = (
            "\n\n".join(context_parts) if context_parts else "No relevant scheduling data found."
        )

        system_prompt = self.get_system_prompt()
        answer = self.generate_answer(system_prompt, context, question)

        return AgentResponse(
            answer=answer,
            mode_used="agent",
            agent_used=agent_name,
            data_used=data_used,
        )

    async def _gather_shift_data(self, entities: dict) -> str:
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

    async def _gather_schedule_data(self, entities: dict) -> str:
        template_fn = get_template("maintenance_schedule")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)

    async def _gather_task_data(self, entities: dict) -> str:
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

    async def _gather_worker_assignment_data(self, entities: dict) -> str:
        template_fn = get_template("equipment_workers")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)
