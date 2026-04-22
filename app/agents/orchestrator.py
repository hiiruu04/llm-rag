import asyncio
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.agents.base import Agent, AgentResponse
from app.agents.competency_agent import CompetencyAgent
from app.agents.recommender_agent import RecommenderAgent
from app.agents.scheduling_agent import SchedulingAgent
from app.agents.analyzer_agent import AnalyzerAgent
from app.core.config import settings

COLLABORATION_MODES = {
    "recommend_worker": ["scheduling", "competency", "recommender"],
    "troubleshoot_assignment": ["recommender", "competency", "scheduling"],
    "maintenance_analysis": ["analyzer", "recommender"],
}

ORCHESTRATOR_SYSTEM_PROMPT = """\
You are a Multi-Agent Orchestrator for a CMMS (Computerized Maintenance Management System). \
You have gathered data from multiple specialized agents and must synthesize their perspectives \
into a coherent, actionable answer.

The following agent contexts are available:
{agent_summaries}

Guidelines:
1. Integrate information from all agent perspectives — do not ignore any provided context.
2. When agents provide conflicting information, present both views and explain the discrepancy.
3. Prioritize safety-relevant findings (high severity, critical issues).
4. Provide concrete, actionable recommendations combining insights from all agents.
5. Structure your answer clearly: start with key findings, then detailed analysis, then recommendations.
6. If data from one agent is sparse, acknowledge what is missing rather than speculating.

Context data:
{context}

Question: {question}"""


class AgentOrchestrator:
    def __init__(self):
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        self.model = settings.openai_llm_model
        self._agents: dict[str, Agent] = {}

    def _get_agent(self, agent_name: str) -> Agent:
        if agent_name not in self._agents:
            if agent_name == "scheduling":
                self._agents[agent_name] = SchedulingAgent()
            elif agent_name == "competency":
                self._agents[agent_name] = CompetencyAgent()
            elif agent_name == "analyzer":
                self._agents[agent_name] = AnalyzerAgent()
            elif agent_name == "recommender":
                self._agents[agent_name] = RecommenderAgent()
            else:
                raise ValueError(f"Unknown agent: {agent_name}")
        return self._agents[agent_name]

    async def orchestrate(
        self,
        question: str,
        entities: dict,
        agent_names: list[str],
        history: list[dict] | None = None,
    ) -> AgentResponse:
        logger.info(f"Orchestrating agents: {agent_names}")

        gather_tasks = []
        for name in agent_names:
            try:
                agent = self._get_agent(name)
                gather_tasks.append(self._gather_from_agent(name, agent, question, entities))
            except ValueError as e:
                logger.warning(f"Skipping unknown agent {name}: {e}")

        results = await asyncio.gather(*gather_tasks, return_exceptions=True)

        context_parts = []
        agent_summaries = []
        data_used = []

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent data gathering failed: {result}")
                continue
            name, context = result
            if context:
                context_parts.append(f"=== {name.upper()} AGENT DATA ===\n{context}")
                agent_summaries.append(f"- {name}: provided data on {name}-related aspects")
                data_used.append(name)
            else:
                agent_summaries.append(f"- {name}: no relevant data found")

        combined_context = (
            "\n\n".join(context_parts)
            if context_parts
            else "No relevant data found from any agent."
        )

        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(
            agent_summaries="\n".join(agent_summaries),
            context=combined_context,
            question=question,
        )

        answer = self._generate_answer(system_prompt, combined_context, question, history)

        return AgentResponse(
            answer=answer,
            mode_used="agent",
            agent_used="+".join(agent_names),
            data_used=data_used,
        )

    async def _gather_from_agent(
        self, name: str, agent: Agent, question: str, entities: dict
    ) -> tuple[str, str]:
        try:
            context = await agent.gather_data(question, entities)
            return (name, context)
        except Exception as e:
            logger.error(f"Error gathering data from {name} agent: {e}")
            return (name, "")

    def _generate_answer(
        self,
        system_prompt: str,
        context: str,
        question: str,
        history: list[dict] | None = None,
    ) -> str:
        try:
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                for msg in history:
                    if msg.get("role") in ("user", "assistant") and msg.get("content"):
                        messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": question})
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Orchestrator answer generation failed: {e}")
            return f"Error generating response: {str(e)}"


_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
