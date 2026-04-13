import asyncio
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings
from app.core.graph_rag_pipeline import get_graph_rag_pipeline
from app.core.rag_pipeline import get_rag_pipeline

HYBRID_PROMPT = """\
You are a CMMS analyst assistant. Answer the user's question \
by synthesizing information from BOTH document sources and \
knowledge graph data below.
Cite your sources when referencing specific information.

--- DOCUMENT SOURCES ---
{doc_context}

--- KNOWLEDGE GRAPH DATA ---
{graph_context}

Question: {question}

Instructions:
1. Synthesize information from both sources
2. Cite which source(s) you used for each part of your answer
3. If one source is more relevant, prioritize it
4. Be concise but thorough

Answer:"""


class HybridPipeline:
    def __init__(self):
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        self.model = settings.openai_llm_model

    async def query(self, question: str) -> dict:
        logger.info(f"Hybrid query: {question[:100]}...")

        # Run both pipelines in parallel
        rag_pipeline = get_rag_pipeline()
        graph_pipeline = get_graph_rag_pipeline()

        rag_task = asyncio.create_task(
            asyncio.to_thread(rag_pipeline.query, question)
        )
        graph_task = asyncio.create_task(
            graph_pipeline.query(question)
        )

        rag_result, graph_result = await asyncio.gather(
            rag_task, graph_task, return_exceptions=True
        )

        # Handle exceptions from either pipeline
        if isinstance(rag_result, Exception):
            logger.error(f"RAG pipeline error: {rag_result}")
            rag_result = {
                "answer": "Document search unavailable.",
                "sources": [],
            }
        if isinstance(graph_result, Exception):
            logger.error(f"Graph pipeline error: {graph_result}")
            graph_result = {
                "answer": "Graph query unavailable.",
                "graph_sources": [],
                "cypher_used": None,
            }

        # Build contexts
        doc_context = rag_result.get("answer", "No document results.")
        sources = rag_result.get("sources", [])
        if sources:
            source_texts = []
            for s in sources:
                preview = s.get("preview_text", "")
                source_texts.append(
                    f"[{s.get('filename', 'Unknown')} "
                    f"(score: {s.get('similarity_score', 0):.2f})]\n"
                    f"{preview}"
                )
            doc_context = "\n\n".join(source_texts)

        graph_context = "No graph results."
        if graph_result.get("graph_sources"):
            parts = []
            for i, record in enumerate(graph_result["graph_sources"], 1):
                lines = [f"[Graph Result {i}]"]
                for key, value in record.items():
                    if value is not None:
                        lines.append(f"  {key}: {value}")
                parts.append("\n".join(lines))
            graph_context = "\n\n".join(parts)

        # Generate synthesized answer
        prompt = HYBRID_PROMPT.format(
            doc_context=doc_context,
            graph_context=graph_context,
            question=question,
        )

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Hybrid answer generation failed: {e}")
            answer = (
                f"Document answer: {rag_result.get('answer', 'N/A')}\n\n"
                f"Graph answer: {graph_result.get('answer', 'N/A')}"
            )

        return {
            "answer": answer,
            "sources": sources,
            "graph_sources": graph_result.get("graph_sources", []),
            "cypher_used": graph_result.get("cypher_used"),
            "model_used": self.model,
            "mode_used": "hybrid",
        }


_hybrid_pipeline: Optional[HybridPipeline] = None


def get_hybrid_pipeline() -> HybridPipeline:
    global _hybrid_pipeline
    if _hybrid_pipeline is None:
        _hybrid_pipeline = HybridPipeline()
    return _hybrid_pipeline
