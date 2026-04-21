import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

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


class Agent(ABC):
    def __init__(self):
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        self.model = settings.openai_llm_model

    @abstractmethod
    async def handle(self, question: str, entities: dict) -> AgentResponse:
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

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

    def generate_answer(self, system_prompt: str, context: str, question: str) -> str:
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
                ],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Agent answer generation failed: {e}")
            return f"Error generating response: {str(e)}"

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
