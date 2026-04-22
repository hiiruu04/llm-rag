from loguru import logger

from app.agents.base import Agent, AgentResponse, _get_mutations_for_agent
from app.services.cypher_templates import get_template

SCHEDULING_SYSTEM_PROMPT = """\
You are a Scheduling Agent for a CMMS (Computerized Maintenance Management System). \
Your specialty is workforce planning, shift management, task assignment, scheduling, \
creating maintenance plans, and creating tasks.

You have access to structured data about:
- Workers, their shifts, and availability
- Maintenance schedules and their tasks
- Equipment-to-worker assignments
- Task requirements (competences, materials)

You have the following tool capabilities:
- create_maintenance_plan: Create a new maintenance schedule/plan for an asset. \
Use this when the user asks to create, set up, or plan new maintenance work.
- create_task: Create a new task under an existing maintenance schedule. Use this \
when the user asks to create or add a task to a maintenance plan.
- assign_task: Assign a worker to an existing task.
- update_task_status: Update the status of a task.
- reschedule_task: Move a task to a different shift.

When answering:
1. Always consider worker availability, shift constraints, and competence requirements.
2. Identify scheduling conflicts or gaps.
3. Propose concrete assignments with specific workers, shifts, and timeframes.
4. If data is incomplete, say so clearly rather than speculating.
5. Present schedules in a clear, structured format.
6. When the user asks to create a maintenance plan, use create_maintenance_plan. \
You MUST supply asset_id, title, maintenance_type, and scheduled_date at minimum.
7. When the user asks to create a task, first ensure a maintenance schedule exists \
(or create one first), then use create_task with the schedule's ID.

IMPORTANT - TOOL CALL RULES:
- When the user asks you to create, assign, reschedule, or update a task, use the \
available tool calls to execute the action immediately. Do NOT just describe what \
command to run.
- All id parameters (task_id, worker_id, shift_id, asset_id, maintenance_schedule_id) \
MUST be valid UUID strings in the format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx. Do NOT \
pass names, numbers, or other non-UUID values.
- Always extract the exact UUID from the context data above. If you cannot find a UUID \
in the context, tell the user you don't have the ID and ask them to provide it.

Context data:
{context}

Question: {question}"""


class SchedulingAgent(Agent):
    def get_system_prompt(self) -> str:
        return SCHEDULING_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        return "scheduling"

    def _gather_methods(self) -> list[tuple[str, callable]]:
        return [
            ("assets", self._gather_asset_data),
            ("shifts", self._gather_shift_data),
            ("schedules", self._gather_schedule_data),
            ("tasks", self._gather_task_data),
            ("worker_assignments", self._gather_worker_assignment_data),
        ]

    async def handle(
        self, question: str, entities: dict, history: list[dict] | None = None
    ) -> AgentResponse:
        logger.info("SchedulingAgent handling: {}...", question[:80])
        data_used = []

        context_parts = []

        asset_data = await self._gather_asset_data(entities)
        if asset_data:
            context_parts.append("=== ASSET DATA ===\n" + asset_data)
            data_used.append("assets")

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
        tools = _get_mutations_for_agent("scheduling")
        mutations = []

        if tools:
            answer, mutations = await self.execute_agentic_loop(
                "scheduling", system_prompt, context, question, tools, history=history
            )
        else:
            answer = self.generate_answer(system_prompt, context, question, history=history)

        return AgentResponse(
            answer=answer,
            mode_used="agent",
            agent_used="scheduling",
            data_used=data_used,
            mutations=mutations,
        )

    async def _gather_asset_data(self, entities: dict) -> str:
        template_fn = get_template("asset_list")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)

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
