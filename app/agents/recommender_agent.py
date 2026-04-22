from loguru import logger

from app.agents.base import Agent, AgentResponse, _get_mutations_for_agent
from app.services.cypher_templates import get_template

RECOMMENDER_SYSTEM_PROMPT = """\
You are a Recommender Agent for a CMMS (Computerized Maintenance Management System). \
Your specialty is troubleshooting, root cause analysis, repair recommendations, \
spare part suggestions, and action documentation.

You have access to:
- Fault chains and cause-effect relationships
- Task requirements and required materials
- Material stock levels
- Troubleshooting documentation (from uploaded manuals and procedures)
- Cause analysis with required roles

You have the following tool capabilities:
- close_action: Close a task or order with an outcome description.
- record_outcome: Record the outcome/result of a completed task.

NOTE: You CANNOT create maintenance plans, tasks, or log down events. If the user \
asks to create a maintenance plan or task, tell them to use the scheduling agent instead.

When answering:
1. Prioritize safety — always note any critical or high-severity findings first.
2. Provide step-by-step troubleshooting or repair recommendations when possible.
3. Reference specific fault codes, causes, and affected components.
4. Mention required spare parts and check stock availability.
5. For documentation requests, confirm the action being taken and provide a clear summary.
6. If multiple solutions exist, rank them by likelihood and cost-effectiveness.

IMPORTANT - TOOL CALL RULES:
- When the user asks you to close an action or record an outcome, use the available \
tool calls to execute the action immediately. Do NOT just describe what command to run.
- All id parameters (action_id, task_id) MUST be valid UUID strings in the format \
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx. Do NOT pass names, numbers, or other \
non-UUID values.
- Always extract the exact UUID from the context data above. If you cannot find a UUID \
in the context, tell the user you don't have the ID and ask them to provide it.

Context data:
{context}

Question: {question}"""


class RecommenderAgent(Agent):
    def get_system_prompt(self) -> str:
        return RECOMMENDER_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        return "recommender"

    def _gather_methods(self) -> list[tuple[str, callable]]:
        return [
            ("fault_chain", self._gather_fault_data),
            ("causes", self._gather_cause_data),
            ("tasks", self._gather_task_data),
            ("materials", self._gather_material_data),
        ]

    async def handle(
        self, question: str, entities: dict, history: list[dict] | None = None
    ) -> AgentResponse:
        logger.info("RecommenderAgent handling: {}...", question[:80])
        data_used = []
        sources = []
        graph_entities = []
        cmms_references = []

        context_parts = []

        fault_data = await self._gather_fault_data(entities)
        if fault_data:
            context_parts.append("=== FAULT CHAIN DATA ===\n" + fault_data)
            data_used.append("fault_chain")

        cause_data = await self._gather_cause_data(entities)
        if cause_data:
            context_parts.append("=== CAUSE ANALYSIS DATA ===\n" + cause_data)
            data_used.append("causes")

        task_data = await self._gather_task_data(entities)
        if task_data:
            context_parts.append("=== TASK & MATERIAL REQUIREMENTS ===\n" + task_data)
            data_used.append("tasks")

        material_data = await self._gather_material_data(entities)
        if material_data:
            context_parts.append("=== MATERIAL & SPARE PART DATA ===\n" + material_data)
            data_used.append("materials")

        doc_sources, doc_context = await self.vector_search(question)
        if doc_context:
            context_parts.append("=== TROUBLESHOOTING DOCUMENTATION ===\n" + doc_context)
            data_used.append("documents")
            sources = doc_sources
            for src in sources:
                graph_entities.append(
                    {
                        "name": src.get("filename", "Unknown"),
                        "entity_type": "Document",
                        "description": src.get("preview_text", "")[:100],
                    }
                )

        context = "\n\n".join(context_parts) if context_parts else "No relevant data found."

        system_prompt = self.get_system_prompt()
        tools = _get_mutations_for_agent("recommender")
        mutations = []

        if tools:
            answer, mutations = await self.execute_agentic_loop(
                "recommender", system_prompt, context, question, tools, history=history
            )
        else:
            answer = self.generate_answer(system_prompt, context, question, history=history)

        return AgentResponse(
            answer=answer,
            sources=sources,
            graph_entities=graph_entities,
            cmms_references=cmms_references,
            mode_used="agent",
            agent_used="recommender",
            data_used=data_used,
            mutations=mutations,
        )

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

    async def _gather_cause_data(self, entities: dict) -> str:
        template_fn = get_template("cause_analysis")
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

    async def _gather_material_data(self, entities: dict) -> str:
        template_fn = get_template("material_planning")
        if not template_fn:
            return ""
        cypher, params = template_fn(entities)
        if not cypher:
            return ""
        results = await self.execute_cypher(cypher, params)
        if not results:
            return ""
        return self.format_cypher_results(results)
