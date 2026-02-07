import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import settings


def create_collection():
    logger.info(f"Connecting to Qdrant at {settings.qdrant_url}")
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
    )

    collections = client.get_collections().collections
    exists = any(c.name == settings.qdrant_collection_name for c in collections)

    if exists:
        logger.info(f"Collection '{settings.qdrant_collection_name}' already exists")
        info = client.get_collection(settings.qdrant_collection_name)
        logger.info(f"Vectors count: {info.points_count}")
        logger.info(f"Status: {info.status}")
    else:
        logger.info(f"Creating collection '{settings.qdrant_collection_name}'")
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(
                size=settings.qdrant_vector_size, distance=Distance.COSINE
            ),
        )
        logger.info(f"Collection '{settings.qdrant_collection_name}' created successfully")


def reset_collection():
    logger.info(f"Connecting to Qdrant at {settings.qdrant_url}")
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
    )

    try:
        logger.info(f"Deleting collection: {settings.qdrant_collection_name}")
        client.delete_collection(settings.qdrant_collection_name)
        logger.info(f"Collection '{settings.qdrant_collection_name}' deleted successfully")

        logger.info(f"Recreating collection with vector size {settings.qdrant_vector_size}")
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(
                size=settings.qdrant_vector_size, distance=Distance.COSINE
            ),
        )
        logger.info(f"Collection '{settings.qdrant_collection_name}' recreated successfully")

    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Collection might not exist. Creating new one...")

        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(
                size=settings.qdrant_vector_size, distance=Distance.COSINE
            ),
        )
        logger.info(f"Collection '{settings.qdrant_collection_name}' created successfully")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_collection()
    else:
        create_collection()
