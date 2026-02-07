from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.api.models import SuccessResponse
from app.core.rag_pipeline import get_rag_pipeline

router = APIRouter(prefix="/api/v1", tags=["query"])


class QueryRequest(BaseModel):
    question: str


class Source(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    similarity_score: float
    preview_text: str


class TokenUsage(BaseModel):
    prompt: int
    completion: int
    total: int


class QueryData(BaseModel):
    answer: str
    sources: list[Source]
    model_used: str
    tokens_used: TokenUsage


@router.post("/query")
async def query_documents(request: QueryRequest):
    logger.info(f"Received query: {request.question[:100]}...")

    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "data": None,
                "meta": {
                    "status_code": 400,
                    "details": "Question cannot be empty",
                    "errors": ["Question cannot be empty"],
                },
            },
        )

    try:
        rag_pipeline = get_rag_pipeline()

        result = rag_pipeline.query(question=request.question)

        sources = [
            Source(
                document_id=src.get("document_id", "unknown"),
                filename=src.get("filename", "Unknown"),
                chunk_index=src.get("chunk_index", 0),
                similarity_score=src.get("similarity_score", 0.0),
                preview_text=src.get("preview_text", ""),
            )
            for src in result.get("sources", [])
        ]

        tokens_used_data = result.get("tokens_used", {})
        tokens_used = TokenUsage(
            prompt=tokens_used_data.get("prompt", 0),
            completion=tokens_used_data.get("completion", 0),
            total=tokens_used_data.get("total", 0),
        )

        logger.info(f"Query processed successfully with {len(sources)} sources")

        data = QueryData(
            answer=result["answer"],
            sources=sources,
            model_used=result["model_used"],
            tokens_used=tokens_used,
        )

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details="Query processed successfully",
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )
