from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import text

from app.api.models import SuccessResponse
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.neo4j import check_neo4j_connection
from app.core.vector_store import get_vector_store

router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthData(BaseModel):
    status: str
    qdrant_connected: bool
    openai_connected: bool
    postgres_connected: bool
    neo4j_connected: bool
    collection_info: Optional[dict]
    graph_info: Optional[dict]


async def check_postgres() -> bool:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@router.get("/health")
async def health_check():
    logger.info("Health check requested")

    try:
        vector_store = get_vector_store()
        collection_info = vector_store.get_collection_info()

        qdrant_connected = bool(collection_info)
        openai_connected = bool(settings.openai_api_key)
        postgres_connected = await check_postgres()
        neo4j_connected = await check_neo4j_connection()

        all_healthy = qdrant_connected and openai_connected and postgres_connected
        status = "healthy" if all_healthy else "unhealthy"

        graph_info = {"connected": neo4j_connected} if neo4j_connected else None

        data = HealthData(
            status=status,
            qdrant_connected=qdrant_connected,
            openai_connected=openai_connected,
            postgres_connected=postgres_connected,
            neo4j_connected=neo4j_connected,
            collection_info=collection_info,
            graph_info=graph_info,
        )

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details="Health check completed",
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "data": None,
                "meta": {
                    "status_code": 503,
                    "details": "Service unavailable",
                    "errors": [str(e)],
                },
            },
        )
