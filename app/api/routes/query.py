import asyncio
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.api.models import SuccessResponse
from app.core.graph_rag_pipeline import get_graph_rag_pipeline
from app.core.graphrag_pipeline import get_graphrag_pipeline
from app.core.hybrid_pipeline import get_hybrid_pipeline
from app.core.rag_pipeline import get_rag_pipeline
from app.services.intent_classifier import get_intent_classifier

router = APIRouter(prefix="/api/v1", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    mode: Literal["auto", "vector", "graph", "graphrag", "hybrid"] = "auto"


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


class GraphSource(BaseModel):
    data: dict


class QueryData(BaseModel):
    answer: str
    sources: list[Source] = []
    model_used: Optional[str] = None
    tokens_used: Optional[TokenUsage] = None
    graph_sources: Optional[list[dict]] = None
    cypher_used: Optional[str] = None
    mode_used: Optional[str] = None
    graph_entities: Optional[list[dict]] = None
    cmms_references: Optional[list[dict]] = None


async def _run_vector_query(question: str) -> dict:
    rag_pipeline = get_rag_pipeline()
    result = await asyncio.to_thread(rag_pipeline.query, question)
    result["mode_used"] = "vector"
    return result


async def _run_graph_query(question: str) -> dict:
    graph_pipeline = get_graph_rag_pipeline()
    return await graph_pipeline.query(question)


async def _run_hybrid_query(question: str) -> dict:
    hybrid_pipeline = get_hybrid_pipeline()
    return await hybrid_pipeline.query(question)


async def _run_graphrag_query(question: str) -> dict:
    graphrag_pipeline = get_graphrag_pipeline()
    return await graphrag_pipeline.query(question)


def _resolve_mode(question: str, mode: str) -> str:
    if mode != "auto":
        return mode
    classifier = get_intent_classifier()
    intent = classifier.classify(question)
    mode_map = {
        "document_search": "vector",
        "structured_query": "graph",
        "hybrid": "hybrid",
        "graphrag": "graphrag",
        "general": "vector",
    }
    return mode_map.get(intent, "vector")


@router.post("/query")
async def query_documents(request: QueryRequest):
    logger.info(f"Received query (mode={request.mode}): {request.question[:100]}...")

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
        mode = _resolve_mode(request.question, request.mode)
        logger.info(f"Resolved mode: {mode}")

        if mode == "graph":
            result = await _run_graph_query(request.question)
        elif mode == "hybrid":
            result = await _run_hybrid_query(request.question)
        elif mode == "graphrag":
            result = await _run_graphrag_query(request.question)
        else:
            result = await _run_vector_query(request.question)

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
        tokens_used = None
        if tokens_used_data:
            tokens_used = TokenUsage(
                prompt=tokens_used_data.get("prompt", 0),
                completion=tokens_used_data.get("completion", 0),
                total=tokens_used_data.get("total", 0),
            )

        data = QueryData(
            answer=result["answer"],
            sources=sources,
            model_used=result.get("model_used"),
            tokens_used=tokens_used,
            graph_sources=result.get("graph_sources"),
            cypher_used=result.get("cypher_used"),
            mode_used=result.get("mode_used", mode),
            graph_entities=result.get("graph_entities"),
            cmms_references=result.get("cmms_references"),
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


@router.post("/query/graph")
async def query_graph(request: QueryRequest):
    logger.info(f"Received graph query: {request.question[:100]}...")

    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        graph_pipeline = get_graph_rag_pipeline()
        result = await graph_pipeline.query(request.question)

        data = QueryData(
            answer=result["answer"],
            graph_sources=result.get("graph_sources"),
            cypher_used=result.get("cypher_used"),
            mode_used="graph",
        )

        return SuccessResponse.create(
            data=data, status_code=200, details="Graph query processed successfully"
        )

    except Exception as e:
        logger.error(f"Error processing graph query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/hybrid")
async def query_hybrid(request: QueryRequest):
    logger.info(f"Received hybrid query: {request.question[:100]}...")

    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        hybrid_pipeline = get_hybrid_pipeline()
        result = await hybrid_pipeline.query(request.question)

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

        data = QueryData(
            answer=result["answer"],
            sources=sources,
            graph_sources=result.get("graph_sources"),
            cypher_used=result.get("cypher_used"),
            model_used=result.get("model_used"),
            mode_used="hybrid",
        )

        return SuccessResponse.create(
            data=data, status_code=200, details="Hybrid query processed successfully"
        )

    except Exception as e:
        logger.error(f"Error processing hybrid query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/graphrag")
async def query_graphrag(request: QueryRequest):
    logger.info(f"Received GraphRAG query: {request.question[:100]}...")

    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        graphrag_pipeline = get_graphrag_pipeline()
        result = await graphrag_pipeline.query(request.question)

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

        data = QueryData(
            answer=result["answer"],
            sources=sources,
            graph_entities=result.get("graph_entities"),
            cmms_references=result.get("cmms_references"),
            mode_used="graphrag",
        )

        return SuccessResponse.create(
            data=data, status_code=200, details="GraphRAG query processed successfully"
        )

    except Exception as e:
        logger.error(f"Error processing GraphRAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
