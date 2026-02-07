from typing import List

from llama_index.embeddings.openai import OpenAIEmbedding
from loguru import logger

from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.model = OpenAIEmbedding(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )

    def get_text_embedding(self, text: str) -> List[float]:
        logger.debug(f"Generating embedding for text (length: {len(text)})")
        embedding = self.model.get_text_embedding(text)
        return embedding

    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.model.get_text_embedding_batch(texts)
        return embeddings


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
