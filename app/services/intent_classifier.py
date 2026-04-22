from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings

INTENT_PROMPT = """\
Classify the following user query into exactly one of these intent categories:

- "scheduling": Questions about shifts, rosters, availability, assignments, \
planning, workforce scheduling, creating maintenance plans, creating tasks, or \
any request to set up new work items. Keywords: shift, roster, availability, \
assign, planning, schedule, who is available, who can work, create, plan, \
maintenance plan, create task, add task, new schedule.
  Example: "Who is available for the Night shift on ES12 tomorrow?"
  Example: "Create a maintenance plan for the boiler inspection"

- "competency": Questions about worker skills, competence, fitness for a task, \
stress, training, or whether someone is qualified/cleared. Keywords: skill, \
competence, fitness, stress, can X do, training, qualified, cleared, proficiency.
  Example: "Is Tech Tina cleared for bearing replacement tonight given her load?"

- "analysis": Questions about metrics, KPIs, trends, statistics, performance, \
MTTR, MTBF, reports, or asking for computed analysis. Keywords: MTTR, MTBF, \
KPI, report, performance, trend, statistics, average, mean, how many, count.
  Example: "What is the MTTR for cooling-system down events on ES12 over the last 90 days?"

- "recommendation": Questions about failures, anomalies, repairs, spares, \
troubleshooting, root cause, or asking what to do about a problem. \
NOTE: If the user wants to CREATE or PLAN something (not just get advice), \
that is "scheduling", not "recommendation". Keywords: \
failure, anomaly, repair, spare, fix, troubleshoot, why, root cause, recommend.
  Example: "ES12 vibration is spiking — what should we do?"

- "status_inquiry": Questions asking about current state, status, or overview \
of equipment or systems. Keywords: what's going on, current state, show me, \
status, overview, summary.
  Example: "What's going on with ES12?"

- "documentation": Requests to log, document, record, or close an action \
or event. Keywords: log it, document, record this, close action, update, mark.
  Example: "Close action AC-001 with outcome 'bearing replaced, vibration back to baseline'"

Respond with ONLY the category name, nothing else.

User query: {question}"""


MULTI_INTENT_PROMPT = """\
Analyze the following user query and determine if it requires collaboration across multiple agent domains.

Available agents and their specialties:
- scheduling: shifts, rosters, availability, workforce planning, creating \
maintenance plans, creating tasks
- competency: worker skills, fitness-for-task, training, clearance
- analyzer: metrics, KPIs, trends, statistics, status overviews, logging down events
- recommender: failures, repairs, troubleshooting, root cause, spare parts, \
closing actions, recording outcomes

Collaboration patterns:
- "recommend_worker": Needs scheduling + competency + recommendation (e.g., \
"Who should we assign to fix this?", "Recommend the best worker for this task")
- "troubleshoot_assignment": Needs recommendation + competency + scheduling \
(e.g., "Find someone qualified to fix this issue", "Who can troubleshoot this \
and when are they available?")
- "maintenance_analysis": Needs analysis + recommendation (e.g., "Analyze the \
failure and recommend next steps", "What's causing this and what should we do?")

IMPORTANT: If the user wants to CREATE a maintenance plan or task, that is \
purely "scheduling" — not multi-agent. Only classify as multi-agent if the \
query genuinely spans multiple domains.

Respond with JSON only:
- If the query is single-domain, respond: {{"multi": false, "intent": "<single_intent>"}}
- If the query is cross-domain, respond: {{"multi": true, "collaboration": "<collaboration_mode>", "agents": ["<agent1>", "<agent2>", ...]}}

Valid collaboration modes: recommend_worker, troubleshoot_assignment, maintenance_analysis
Valid agents: scheduling, competency, analyzer, recommender
Valid intents: scheduling, competency, analysis, recommendation, status_inquiry, documentation

User query: {question}"""


class IntentClassifier:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.model = settings.openai_llm_model

    def classify(self, question: str) -> str:
        prompt = INTENT_PROMPT.format(question=question)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.0,
            )
            intent = response.choices[0].message.content
            if intent:
                intent = intent.strip().strip('"').lower()
            else:
                intent = "analysis"
            valid_intents = {
                "scheduling",
                "competency",
                "analysis",
                "recommendation",
                "status_inquiry",
                "documentation",
            }
            if intent not in valid_intents:
                logger.warning(f"Unknown intent '{intent}', defaulting to 'analysis'")
                intent = "analysis"
            logger.info(f"Classified intent: {intent}")
            return intent
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return "analysis"

    def classify_multi(self, question: str) -> tuple[str | None, list[str] | None]:
        prompt = MULTI_INTENT_PROMPT.format(question=question)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.0,
            )
            content = response.choices[0].message.content
            if not content:
                return None, None

            import json

            result = json.loads(content.strip().strip("`"))

            if result.get("multi"):
                agents = result.get("agents", [])
                collaboration = result.get("collaboration", "")
                valid_agents = {"scheduling", "competency", "analyzer", "recommender"}
                agents = [a for a in agents if a in valid_agents]
                if agents:
                    logger.info(
                        f"Multi-intent detected: collaboration={collaboration}, agents={agents}"
                    )
                    return None, agents
                return None, None
            else:
                intent = result.get("intent", "analysis")
                logger.info(f"Single-intent detected: {intent}")
                return intent, None
        except Exception as e:
            logger.error(f"Multi-intent classification failed: {e}")
            return None, None


_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
