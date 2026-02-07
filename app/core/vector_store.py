import hashlib
from typing import List

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, NearestQuery, PointStruct

from app.core.config import settings
from app.core.embeddings import get_embedding_service


def generate_point_id(document_id: str, chunk_index: int) -> int:
    """Generate a unique integer ID from document_id and chunk_index."""
    unique_string = f"{document_id}_{chunk_index}"
    hash_obj = hashlib.md5(unique_string.encode())
    return int(hash_obj.hexdigest()[:8], 16)


class VectorStoreManager:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
        )
        self.collection_name = settings.qdrant_collection_name
        self.vector_size = settings.qdrant_vector_size

    def add_documents(self, chunks: List[dict], document_id: str) -> List[str]:
        embedding_service = get_embedding_service()
        points = []

        logger.info(f"Processing {len(chunks)} chunks for document {document_id}")

        for chunk in chunks:
            text = chunk["text"].strip()
            if not text:
                logger.warning(f"Skipping empty chunk {chunk['metadata'].get('chunk_index')}")
                continue

            logger.debug(
                f"Processing chunk {chunk['metadata'].get('chunk_index')}: {len(text)} chars"
            )

            try:
                embedding = embedding_service.get_text_embedding(text)
                chunk_index = chunk["metadata"]["chunk_index"]
                point_id = generate_point_id(document_id, chunk_index)

                payload = {
                    "text": text,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    **{k: v for k, v in chunk["metadata"].items() if k != "chunk_index"},
                }

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                )
            except Exception as e:
                logger.error(f"Error processing chunk {chunk['metadata'].get('chunk_index')}: {e}")
                continue

        if not points:
            raise ValueError("No valid chunks to add. All chunks were empty or caused errors.")

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Added {len(points)} vectors to collection")
        return [str(p.id) for p in points]

    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
    ) -> List[dict]:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=NearestQuery(nearest=query_embedding),
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )

        documents = []
        for result in results.points:
            documents.append(
                {
                    "id": result.id,
                    "text": result.payload.get("text"),
                    "metadata": {k: v for k, v in result.payload.items() if k != "text"},
                    "similarity_score": result.score,
                }
            )

        logger.info(f"Found {len(documents)} relevant documents")
        return documents

    def delete_document(self, document_id: str) -> bool:
        try:
            logger.info(f"Attempting to delete document {document_id}")

            search_filter = Filter(must=[{"key": "document_id", "match": {"value": document_id}}])

            search_results = self.client.scroll(
                collection_name=self.collection_name,
                limit=1,
                with_payload=["document_id"],
                with_vectors=False,
                scroll_filter=search_filter,
            )

            if not search_results[0]:
                logger.warning(f"Document {document_id} not found")
                return False

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=search_filter,
            )
            logger.info(f"Deleted document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False

    def get_collection_info(self) -> dict:
        try:
            info = self.client.get_collection(self.collection_name)
            vector_size = (
                info.config.params.vectors.size
                if hasattr(info.config.params.vectors, "size")
                else self.vector_size
            )
            return {
                "name": self.collection_name,
                "vector_size": vector_size,
                "vectors_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}


def get_vector_store():
    return VectorStoreManager()
