from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings

INTENT_PROMPT = """\
Classify the following user query into exactly one of these categories:

- "document_search": Questions about manuals, procedures, \
documentation, unstructured text
- "structured_query": Questions about assets, faults, maintenance, \
sensors, relationships, hierarchies, statistics in the CMMS
- "hybrid": Questions requiring BOTH document knowledge \
AND structured CMMS data
- "general": Questions not related to CMMS or documents

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
            intent = response.choices[0].message.content.strip().strip('"').lower()
            valid_intents = {"document_search", "structured_query", "hybrid", "general"}
            if intent not in valid_intents:
                logger.warning(f"Unknown intent '{intent}', defaulting to 'general'")
                intent = "general"
            logger.info(f"Classified intent: {intent}")
            return intent
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return "general"


_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
