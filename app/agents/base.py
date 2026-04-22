import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from loguru import logger
from openai import OpenAI

from app.core.config import settings
from app.core.neo4j import get_neo4j_driver


@dataclass
class AgentResponse:
    answer: str
    sources: list[dict] = field(default_factory=list)
    graph_entities: list[dict] = field(default_factory=list)
    cmms_references: list[dict] = field(default_factory=list)
    mode_used: str = "agent"
    agent_used: str = ""
    data_used: list[str] = field(default_factory=list)
    cypher_used: Optional[str] = None
    tokens_used: Optional[dict] = None
    mutations: list[dict] = field(default_factory=list)


MUTATION_TOOLS = {
    "scheduling": [
        {
            "type": "function",
            "function": {
                "name": "create_maintenance_plan",
                "description": (
                    "Create a new maintenance schedule/plan for an asset. "
                    "Returns the created plan with its ID."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset this maintenance plan is for",
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the maintenance plan",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the maintenance plan",
                        },
                        "maintenance_type": {
                            "type": "string",
                            "enum": ["preventive", "corrective", "predictive"],
                            "description": "Type of maintenance",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Priority level",
                        },
                        "scheduled_date": {
                            "type": "string",
                            "description": (
                                "ISO 8601 date string for when the maintenance is scheduled "
                                "(e.g. '2026-05-01T08:00:00Z')"
                            ),
                        },
                        "recurrence": {
                            "type": "string",
                            "enum": ["none", "daily", "weekly", "monthly", "quarterly", "yearly"],
                            "description": "Recurrence pattern, default is 'none'",
                        },
                        "estimated_duration_hours": {
                            "type": "number",
                            "description": "Estimated duration in hours",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional notes",
                        },
                    },
                    "required": ["asset_id", "title", "maintenance_type", "scheduled_date"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_task",
                "description": (
                    "Create a new task under an existing maintenance schedule. "
                    "Returns the created task with its ID."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the task",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the task",
                        },
                        "task_type": {
                            "type": "string",
                            "enum": [
                                "general",
                                "inspection",
                                "repair",
                                "installation",
                                "calibration",
                            ],
                            "description": "Type of task, default is 'general'",
                        },
                        "maintenance_schedule_id": {
                            "type": "string",
                            "description": "UUID of the maintenance schedule this task belongs to",
                        },
                        "shift_id": {
                            "type": "string",
                            "description": "UUID of the shift to assign this task to",
                        },
                        "worker_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of worker UUIDs to assign to this task",
                        },
                        "estimated_duration_hours": {
                            "type": "number",
                            "description": "Estimated duration in hours",
                        },
                        "action_type": {
                            "type": "string",
                            "description": (
                                "Action type (e.g. 'standard', 'repair', 'inspection'), "
                                "default is 'standard'"
                            ),
                        },
                        "sequence_order": {
                            "type": "integer",
                            "description": "Order within the schedule, default is 0",
                        },
                    },
                    "required": ["name", "maintenance_schedule_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "assign_task",
                "description": "Assign a worker to a task. Status becomes 'assigned'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task to assign",
                        },
                        "worker_id": {
                            "type": "string",
                            "description": "UUID of the worker to assign to the task",
                        },
                    },
                    "required": ["task_id", "worker_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_task_status",
                "description": "Update the status of a task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task",
                        },
                        "status": {
                            "type": "string",
                            "enum": [
                                "pending",
                                "assigned",
                                "in_progress",
                                "completed",
                                "cancelled",
                                "on_hold",
                            ],
                            "description": "New status for the task",
                        },
                    },
                    "required": ["task_id", "status"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "reschedule_task",
                "description": "Reschedule a task to a different shift.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task to reschedule",
                        },
                        "shift_id": {
                            "type": "string",
                            "description": "UUID of the new shift to assign the task to",
                        },
                    },
                    "required": ["task_id", "shift_id"],
                },
            },
        },
    ],
    "analyzer": [
        {
            "type": "function",
            "function": {
                "name": "log_down_event",
                "description": "Log a new down event for an asset and fault.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset",
                        },
                        "fault_id": {
                            "type": "string",
                            "description": "UUID of the fault",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Severity level of the event",
                        },
                    },
                    "required": ["asset_id", "fault_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "close_down_event",
                "description": "Close a down event with a resolution.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "down_event_id": {
                            "type": "string",
                            "description": "UUID of the down event to close",
                        },
                        "resolution": {
                            "type": "string",
                            "description": "Description of the resolution",
                        },
                    },
                    "required": ["down_event_id", "resolution"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_fault_severity",
                "description": "Update the severity of a fault.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fault_id": {
                            "type": "string",
                            "description": "UUID of the fault",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "New severity level",
                        },
                    },
                    "required": ["fault_id", "severity"],
                },
            },
        },
    ],
    "recommender": [
        {
            "type": "function",
            "function": {
                "name": "close_action",
                "description": "Close a task or order with an outcome.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action_id": {
                            "type": "string",
                            "description": "UUID of the task or order to close",
                        },
                        "outcome": {
                            "type": "string",
                            "description": "Description of the outcome",
                        },
                    },
                    "required": ["action_id", "outcome"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "record_outcome",
                "description": "Record the outcome of a completed task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task",
                        },
                        "result": {
                            "type": "string",
                            "description": "Description of the result",
                        },
                    },
                    "required": ["task_id", "result"],
                },
            },
        },
    ],
}

MUTATION_EXECUTORS = {}


def _get_mutations_for_agent(agent_name: str) -> list[dict]:
    return MUTATION_TOOLS.get(agent_name, [])


def _validate_uuid_args(function_name: str, arguments: dict) -> list[str]:
    uuid_params = {
        "assign_task": ["task_id", "worker_id"],
        "update_task_status": ["task_id"],
        "reschedule_task": ["task_id", "shift_id"],
        "create_maintenance_plan": ["asset_id"],
        "create_task": ["maintenance_schedule_id", "shift_id"],
        "log_down_event": ["asset_id", "fault_id"],
        "close_down_event": ["down_event_id"],
        "update_fault_severity": ["fault_id"],
        "close_action": ["action_id"],
        "record_outcome": ["task_id"],
    }
    errors = []
    for param in uuid_params.get(function_name, []):
        val = arguments.get(param, "")
        if val:
            try:
                UUID(str(val))
            except (ValueError, AttributeError):
                errors.append(
                    f"Parameter '{param}' must be a valid UUID, got '{val}'. "
                    f"Look up the correct UUID from the context data above."
                )
    return errors


async def _execute_mutation(agent_name: str, function_name: str, arguments: dict) -> dict:
    from app.agents.mutation_service import (
        assign_task,
        close_action,
        close_down_event,
        create_maintenance_plan,
        create_task,
        log_down_event,
        record_outcome,
        reschedule_task,
        update_fault_severity,
        update_task_status,
    )

    mapping = {
        "scheduling": {
            "create_maintenance_plan": create_maintenance_plan,
            "create_task": create_task,
            "assign_task": assign_task,
            "update_task_status": update_task_status,
            "reschedule_task": reschedule_task,
        },
        "analyzer": {
            "log_down_event": log_down_event,
            "close_down_event": close_down_event,
            "update_fault_severity": update_fault_severity,
        },
        "recommender": {
            "close_action": close_action,
            "record_outcome": record_outcome,
        },
    }

    agent_funcs = mapping.get(agent_name, {})
    func = agent_funcs.get(function_name)

    if not func:
        return {"error": f"Unknown function {function_name} for agent {agent_name}"}

    validation_errors = _validate_uuid_args(function_name, arguments)
    if validation_errors:
        return {"error": "; ".join(validation_errors)}

    try:
        result = await func(**arguments)
        return result
    except Exception as e:
        logger.error(f"Mutation {function_name} failed: {e}")
        return {"error": str(e)}


class Agent(ABC):
    def __init__(self):
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        self.model = settings.openai_llm_model

    @abstractmethod
    async def handle(
        self, question: str, entities: dict, history: list[dict] | None = None
    ) -> AgentResponse:
        pass

    async def gather_data(self, question: str, entities: dict) -> str:
        context_parts = []
        for name, method in self._gather_methods():
            try:
                result = await method(entities)
                if result:
                    context_parts.append(f"=== {name.upper()} DATA ===\n{result}")
            except Exception as e:
                logger.warning(f"Error gathering {name} data: {e}")
        return "\n\n".join(context_parts) if context_parts else ""

    def _gather_methods(self) -> list[tuple[str, callable]]:
        return []

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @property
    def agent_name(self) -> str:
        return ""

    async def execute_cypher(self, cypher: str, params: dict | None = None) -> list[dict]:
        params = params or {}
        driver = await get_neo4j_driver()
        try:
            async with driver.session(database=settings.neo4j_database) as session:
                result = await session.run(cypher, **params)
                records = await result.data()
                return records
        except Exception as e:
            logger.error(f"Cypher execution failed: {e}")
            return []

    @staticmethod
    def format_cypher_results(results: list[dict]) -> str:
        if not results:
            return "No data found."
        parts = []
        for i, record in enumerate(results, 1):
            lines = [f"[Result {i}]"]
            for key, value in record.items():
                if value is not None:
                    lines.append(f"  {key}: {value}")
            parts.append("\n".join(lines))
        return "\n\n".join(parts)

    def generate_answer(
        self, system_prompt: str, context: str, question: str, history: list[dict] | None = None
    ) -> str:
        try:
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                for msg in history:
                    if msg.get("role") in ("user", "assistant") and msg.get("content"):
                        messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append(
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            )
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Agent answer generation failed: {e}")
            return f"Error generating response: {str(e)}"

    def generate_answer_with_tools(
        self,
        system_prompt: str,
        context: str,
        question: str,
        tools: list[dict],
        history: list[dict] | None = None,
    ) -> tuple[str, list[dict] | None]:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append(
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        )

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
        except Exception as e:
            logger.error(f"Agent answer generation with tools failed: {e}")
            return f"Error generating response: {str(e)}", None

        choice = response.choices[0]
        tool_calls = choice.message.tool_calls

        if tool_calls:
            return choice.message.content or "", tool_calls

        return choice.message.content.strip() if choice.message.content else "", None

    async def execute_tool_calls(
        self, agent_name: str, tool_calls: list, max_retries: int = 1
    ) -> list[dict]:
        mutations = []
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}

            logger.info(f"Agent {agent_name} calling tool: {func_name} with args: {func_args}")

            result = await _execute_mutation(agent_name, func_name, func_args)

            if "error" in result and max_retries > 0:
                retry_result = await self._retry_tool_call(
                    agent_name, func_name, func_args, result["error"]
                )
                if retry_result:
                    result = retry_result

            mutation_record = {
                "function": func_name,
                "arguments": func_args,
                "result": result,
            }
            mutations.append(mutation_record)

        return mutations

    async def _retry_tool_call(
        self, agent_name: str, func_name: str, original_args: dict, error: str
    ) -> dict | None:
        tools = _get_mutations_for_agent(agent_name)
        if not tools:
            return None

        retry_prompt = (
            f"The tool call '{func_name}' with arguments {original_args} failed with error: "
            f"{error}. Please try again with the correct arguments. "
            f"Make sure all ID parameters are valid UUIDs found in the context data."
        )

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that corrects failed tool calls.",
                    },
                    {"role": "user", "content": retry_prompt},
                ],
                tools=tools,
                tool_choice="auto",
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )

            choice = response.choices[0]
            if not choice.message.tool_calls:
                return None

            retry_call = choice.message.tool_calls[0]
            retry_func_name = retry_call.function.name
            try:
                retry_args = json.loads(retry_call.function.arguments)
            except json.JSONDecodeError:
                return None

            logger.info(
                f"Agent {agent_name} retrying tool: {retry_func_name} with args: {retry_args}"
            )
            return await _execute_mutation(agent_name, retry_func_name, retry_args)
        except Exception as e:
            logger.warning(f"Retry tool call failed: {e}")
            return None

    async def execute_agentic_loop(
        self,
        agent_name: str,
        system_prompt: str,
        context: str,
        question: str,
        tools: list[dict],
        history: list[dict] | None = None,
        max_rounds: int = 5,
    ) -> tuple[str, list[dict]]:
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append(
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        )

        all_mutations: list[dict] = []

        for _ in range(max_rounds):
            try:
                response = self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=settings.openai_max_tokens,
                    temperature=settings.openai_temperature,
                )
            except Exception as e:
                logger.error(f"Agentic loop failed: {e}")
                break

            choice = response.choices[0]
            tool_calls = choice.message.tool_calls

            if not tool_calls:
                final_answer = choice.message.content.strip() if choice.message.content else ""
                return final_answer, all_mutations

            assistant_msg: dict = {"role": "assistant", "content": choice.message.content or ""}
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ]
            messages.append(assistant_msg)

            for tool_call in tool_calls:
                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                logger.info(f"Agent {agent_name} calling tool: {func_name} with args: {func_args}")

                result = await _execute_mutation(agent_name, func_name, func_args)

                if "error" in result:
                    retry_result = await self._retry_tool_call(
                        agent_name, func_name, func_args, result["error"]
                    )
                    if retry_result and "error" not in retry_result:
                        result = retry_result

                all_mutations.append(
                    {
                        "function": func_name,
                        "arguments": func_args,
                        "result": result,
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
            final_answer = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Agentic loop final answer failed: {e}")
            final_answer = "I completed the requested actions but could not generate a summary."

        return final_answer, all_mutations

    async def vector_search(
        self, question: str, limit: int | None = None, threshold: float | None = None
    ):
        from app.core.embeddings import get_embedding_service
        from app.core.vector_store import get_vector_store

        embedding_service = get_embedding_service()
        vector_store = get_vector_store()
        query_embedding = await asyncio.to_thread(embedding_service.get_text_embedding, question)
        retrieved = await asyncio.to_thread(
            vector_store.search,
            query_embedding=query_embedding,
            limit=limit or settings.default_top_k,
            score_threshold=threshold or settings.similarity_threshold,
        )
        sources = [
            {
                "document_id": doc["metadata"].get("document_id"),
                "filename": doc["metadata"].get("file_name", "Unknown"),
                "chunk_index": doc["metadata"].get("chunk_index"),
                "similarity_score": doc["similarity_score"],
                "preview_text": doc["text"][:200] + "..."
                if len(doc["text"]) > 200
                else doc["text"],
            }
            for doc in retrieved
        ]
        doc_context = "\n\n".join(
            f"[Source {i}: {doc['metadata'].get('file_name', 'Unknown')} "
            f"(score: {doc['similarity_score']:.2f})]\n{doc['text']}"
            for i, doc in enumerate(retrieved, 1)
        )
        return sources, doc_context
