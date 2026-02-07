from typing import List, Optional

from loguru import logger

from app.core.config import settings
from app.core.embeddings import get_embedding_service
from app.core.llm import get_llm_service
from app.core.vector_store import get_vector_store


class RAGPipeline:
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.llm_service = get_llm_service()
        self.vector_store = get_vector_store()

    def query(self, question: str) -> dict:
        logger.info(f"Processing query: {question[:100]}...")

        query_embedding = self.embedding_service.get_text_embedding(question)

        retrieved_docs = self.vector_store.search(
            query_embedding=query_embedding,
            limit=settings.default_top_k,
            score_threshold=settings.similarity_threshold,
        )

        if not retrieved_docs:
            logger.warning("No relevant documents found")
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "model_used": "N/A",
            }

        context = self._build_context(retrieved_docs)
        prompt = self._construct_prompt(question, context)

        answer = self.llm_service.generate_response(prompt)

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
            for doc in retrieved_docs
        ]

        token_count = self.llm_service.get_token_count(prompt, answer)

        logger.info(f"Generated answer with {len(sources)} sources")

        return {
            "answer": answer,
            "sources": sources,
            "model_used": self.llm_service.llm.model,
            "tokens_used": token_count,
        }

    def _build_context(self, retrieved_docs: List[dict]) -> str:
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc["metadata"]
            source = metadata.get("file_name", "Unknown")
            similarity = doc["similarity_score"]
            context_parts.append(
                f"[Source {i}: {source} (Similarity: {similarity:.2f})]\n{doc['text']}"
            )
        return "\n\n".join(context_parts)

    def _construct_prompt(self, question: str, context: str) -> str:
        prompt = f"""
        You are a helpful assistant that answers questions based on the provided context.
        Context:
        {context}

        Question: {question}

        Instructions:
        1. Answer the question using only the information from the context above.
        2. If the context doesn't contain enough information to answer the question, say so clearly.
        3. Be concise but thorough in your answer.
        4. If relevant, mention which source(s) you used in your answer.

        Answer:"""  # noqa: E501
        return prompt


_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
