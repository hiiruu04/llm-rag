from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings

INTENT_PROMPT = """\
Classify the following user query into exactly one of these intent categories:

- "scheduling": Questions about shifts, rosters, availability, assignments, \
planning, or workforce scheduling. Keywords: shift, roster, availability, \
assign, planning, schedule, who is available, who can work.
  Example: "Who is available for the Night shift on ES12 tomorrow?"

- "competency": Questions about worker skills, competence, fitness for a task, \
stress, training, or whether someone is qualified/cleared. Keywords: skill, \
competence, fitness, stress, can X do, training, qualified, cleared, proficiency.
  Example: "Is Tech Tina cleared for bearing replacement tonight given her load?"

- "analysis": Questions about metrics, KPIs, trends, statistics, performance, \
MTTR, MTBF, reports, or asking for computed analysis. Keywords: MTTR, MTBF, \
KPI, report, performance, trend, statistics, average, mean, how many, count.
  Example: "What is the MTTR for cooling-system down events on ES12 over the last 90 days?"

- "recommendation": Questions about failures, anomalies, repairs, spares, \
troubleshooting, root cause, or asking what to do about a problem. Keywords: \
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


_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
