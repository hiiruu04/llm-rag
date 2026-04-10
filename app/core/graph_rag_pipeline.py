from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings
from app.core.neo4j import get_neo4j_driver
from app.services.cypher_generator import get_cypher_generator
from app.services.cypher_templates import get_template
from app.services.entity_extractor import get_entity_extractor

ANSWER_PROMPT = """\
You are a CMMS analyst assistant. Answer the user's question \
based on the graph query results below.
If the results are empty, say you couldn't find relevant data \
in the knowledge graph.
Format your answer clearly with structured information.

Graph query results:
{graph_context}

Question: {question}

Answer:"""


class GraphRAGPipeline:
    def __init__(self):
        self.entity_extractor = get_entity_extractor()
        self.cypher_generator = get_cypher_generator()
        self.llm_client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.model = settings.openai_llm_model

    async def query(self, question: str) -> dict:
        logger.info(f"GraphRAG query: {question[:100]}...")

        # Step 1: Extract entities
        entities = self.entity_extractor.extract(question)
        query_type = entities.get("query_type", "search")

        # Step 2: Get Cypher query (template first, then LLM fallback)
        cypher, params = self._get_cypher(query_type, entities, question)
        if not cypher:
            return {
                "answer": (
                    "I couldn't determine how to query "
                    "the knowledge graph for your question."
                ),
                "graph_sources": [],
                "cypher_used": None,
                "mode_used": "graph",
            }

        # Step 3: Execute Cypher against Neo4j
        try:
            results = await self._execute_cypher(cypher, params)
        except Exception as e:
            logger.error(f"Cypher execution failed: {e}")
            return {
                "answer": f"Error querying the knowledge graph: {str(e)}",
                "graph_sources": [],
                "cypher_used": cypher,
                "mode_used": "graph",
            }

        if not results:
            return {
                "answer": "No results found in the knowledge graph for your query.",
                "graph_sources": [],
                "cypher_used": cypher,
                "mode_used": "graph",
            }

        # Step 4: Format graph context
        graph_context = self._format_results(results)

        # Step 5: Generate answer
        answer = self._generate_answer(question, graph_context)

        return {
            "answer": answer,
            "graph_sources": results,
            "cypher_used": cypher,
            "mode_used": "graph",
        }

    def _get_cypher(self, query_type: str, entities: dict, question: str) -> tuple:
        # Try template first
        template_fn = get_template(query_type)
        if template_fn:
            cypher, params = template_fn(entities)
            logger.info(f"Using template for {query_type}")
            return cypher, params

        # Fallback to LLM-generated Cypher
        cypher = self.cypher_generator.generate(question)
        if cypher:
            return cypher, {}

        return None, {}

    async def _execute_cypher(self, cypher: str, params: dict) -> list[dict]:
        driver = await get_neo4j_driver()
        async with driver.session(database=settings.neo4j_database) as session:
            result = await session.run(cypher, **params)
            records = await result.data()
        return records

    def _format_results(self, results: list[dict]) -> str:
        parts = []
        for i, record in enumerate(results, 1):
            lines = [f"[Graph Result {i}]"]
            for key, value in record.items():
                if value is not None:
                    lines.append(f"  {key}: {value}")
            parts.append("\n".join(lines))
        return "\n\n".join(parts)

    def _generate_answer(self, question: str, graph_context: str) -> str:
        prompt = ANSWER_PROMPT.format(graph_context=graph_context, question=question)
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return f"Found graph data but couldn't generate an answer: {str(e)}"


_graph_rag_pipeline: Optional[GraphRAGPipeline] = None


def get_graph_rag_pipeline() -> GraphRAGPipeline:
    global _graph_rag_pipeline
    if _graph_rag_pipeline is None:
        _graph_rag_pipeline = GraphRAGPipeline()
    return _graph_rag_pipeline
