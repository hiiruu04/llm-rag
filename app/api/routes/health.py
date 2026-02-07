from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.api.models import SuccessResponse
from app.core.config import settings
from app.core.vector_store import get_vector_store

router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthData(BaseModel):
    status: str
    qdrant_connected: bool
    openai_connected: bool
    collection_info: Optional[dict]


@router.get("/health")
async def health_check():
    logger.info("Health check requested")

    try:
        vector_store = get_vector_store()
        collection_info = vector_store.get_collection_info()

        qdrant_connected = bool(collection_info)
        openai_connected = bool(settings.openai_api_key)

        status = "healthy" if qdrant_connected and openai_connected else "unhealthy"

        data = HealthData(
            status=status,
            qdrant_connected=qdrant_connected,
            openai_connected=openai_connected,
            collection_info=collection_info,
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
