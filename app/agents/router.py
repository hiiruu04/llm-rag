from loguru import logger

from app.agents.analyzer_agent import AnalyzerAgent
from app.agents.base import AgentResponse
from app.agents.competency_agent import CompetencyAgent
from app.agents.orchestrator import get_orchestrator
from app.agents.recommender_agent import RecommenderAgent
from app.agents.scheduling_agent import SchedulingAgent
from app.services.entity_extractor import get_entity_extractor
from app.services.intent_classifier import get_intent_classifier

INTENT_AGENT_MAP: dict[str, str] = {
    "scheduling": "scheduling",
    "competency": "competency",
    "analysis": "analyzer",
    "status_inquiry": "analyzer",
    "recommendation": "recommender",
    "documentation": "recommender",
}


class AgentRouter:
    def __init__(self):
        self._agents: dict[str, object] = {}
        self._intent_classifier = get_intent_classifier()
        self._entity_extractor = get_entity_extractor()

    def _get_agent(self, agent_name: str):
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

    async def route(
        self, question: str, intent: str | None = None, history: list[dict] | None = None
    ) -> AgentResponse:
        if intent is None:
            single_intent, multi_agents = self._intent_classifier.classify_multi(question)
            if multi_agents:
                entities = self._entity_extractor.extract(question)
                orchestrator = get_orchestrator()
                logger.info(f"Routing question to orchestrator with agents: {multi_agents}")
                return await orchestrator.orchestrate(
                    question, entities, multi_agents, history=history
                )
            intent = single_intent or self._intent_classifier.classify(question)

        agent_name = INTENT_AGENT_MAP.get(intent)
        if not agent_name:
            logger.warning(f"No agent mapping for intent '{intent}', defaulting to analyzer")
            agent_name = "analyzer"

        entities = self._entity_extractor.extract(question)

        agent = self._get_agent(agent_name)
        logger.info(f"Routing question to {agent_name} agent (intent={intent})")

        response = await agent.handle(question, entities, history=history)
        return response


_agent_router: AgentRouter | None = None


def get_agent_router() -> AgentRouter:
    global _agent_router
    if _agent_router is None:
        _agent_router = AgentRouter()
    return _agent_router
