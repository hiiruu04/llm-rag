import asyncio
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.router import get_agent_router
from app.api.models import SuccessResponse
from app.core.database import get_db
from app.core.graph_rag_pipeline import get_graph_rag_pipeline
from app.core.graphrag_pipeline import get_graphrag_pipeline
from app.core.hybrid_pipeline import get_hybrid_pipeline
from app.core.rag_pipeline import get_rag_pipeline
from app.models.schemas import ChatMessageCreate, ChatSessionCreate
from app.services import chat_service
from app.services.intent_classifier import get_intent_classifier

router = APIRouter(prefix="/api/v1", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    mode: Literal["auto", "vector", "graph", "graphrag", "hybrid", "agent"] = "auto"
    session_id: Optional[str] = None


class AgentQueryRequest(BaseModel):
    question: str
    agent_type: Optional[Literal["scheduling", "competency", "analyzer", "recommender"]] = None
    session_id: Optional[str] = None


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
    agent_used: Optional[str] = None
    session_id: Optional[str] = None
    mutations: list[dict] = []


INTENT_MODE_MAP = {
    "scheduling": "agent",
    "competency": "agent",
    "analysis": "agent",
    "recommendation": "agent",
    "status_inquiry": "agent",
    "documentation": "agent",
}


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


async def _run_agent_query(
    question: str, intent: str | None = None, history: list[dict] | None = None
) -> dict:
    agent_router = get_agent_router()
    response = await agent_router.route(question, intent=intent, history=history)
    return {
        "answer": response.answer,
        "sources": response.sources,
        "graph_entities": response.graph_entities,
        "cmms_references": response.cmms_references,
        "mode_used": response.mode_used,
        "agent_used": response.agent_used,
        "data_used": response.data_used,
        "cypher_used": response.cypher_used,
        "tokens_used": response.tokens_used,
        "mutations": response.mutations,
    }


def _resolve_mode(question: str, mode: str) -> tuple[str, str | None]:
    if mode != "auto":
        return mode, None
    classifier = get_intent_classifier()
    intent = classifier.classify(question)
    resolved_mode = INTENT_MODE_MAP.get(intent, "agent")
    return resolved_mode, intent


@router.post("/query")
async def query_documents(request: QueryRequest, db: AsyncSession = Depends(get_db)):
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

    session_id = None
    history = None

    if request.session_id:
        try:
            session_id = UUID(request.session_id)
            session = await chat_service.get_session(db, session_id)
            if session:
                recent_messages = await chat_service.get_recent_messages(db, session_id)
                history = chat_service.format_history_for_llm(recent_messages)
            else:
                session_id = None
        except Exception as e:
            logger.warning(f"Failed to load session {request.session_id}: {e}")
            session_id = None

    try:
        mode, intent = _resolve_mode(request.question, request.mode)
        logger.info(f"Resolved mode: {mode}, intent: {intent}")

        if mode == "agent":
            result = await _run_agent_query(request.question, intent=intent, history=history)
        elif mode == "graph":
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

        result_session_id = str(session_id) if session_id else None

        if not session_id:
            try:
                session = await chat_service.create_session(
                    db,
                    ChatSessionCreate(
                        title=request.question[:50],
                        mode=request.mode,
                    ),
                )
                session_id = session.id
                result_session_id = str(session_id)
            except Exception as e:
                logger.warning(f"Failed to create session: {e}")

        if session_id:
            try:
                await chat_service.add_message(
                    db,
                    session_id,
                    ChatMessageCreate(role="user", content=request.question),
                )
                await chat_service.add_message(
                    db,
                    session_id,
                    ChatMessageCreate(
                        role="assistant",
                        content=result["answer"],
                        metadata_={
                            "mode_used": result.get("mode_used", mode),
                            "agent_used": result.get("agent_used"),
                            "data_used": result.get("data_used", []),
                        },
                    ),
                )
            except Exception as e:
                logger.warning(f"Failed to persist messages: {e}")

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
            agent_used=result.get("agent_used"),
            session_id=result_session_id,
            mutations=result.get("mutations", []),
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


@router.post("/query/agent")
async def query_agent(request: AgentQueryRequest, db: AsyncSession = Depends(get_db)):
    logger.info(
        f"Received agent query (agent_type={request.agent_type}): {request.question[:100]}..."
    )

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

    session_id = None
    history = None

    if request.session_id:
        try:
            session_id = UUID(request.session_id)
            session = await chat_service.get_session(db, session_id)
            if session:
                recent_messages = await chat_service.get_recent_messages(db, session_id)
                history = chat_service.format_history_for_llm(recent_messages)
            else:
                session_id = None
        except Exception as e:
            logger.warning(f"Failed to load session {request.session_id}: {e}")
            session_id = None

    try:
        agent_router = get_agent_router()
        intent = None

        if request.agent_type:
            intent_map = {
                "scheduling": "scheduling",
                "competency": "competency",
                "analyzer": "analysis",
                "recommender": "recommendation",
            }
            intent = intent_map.get(request.agent_type)

        response = await agent_router.route(request.question, intent=intent, history=history)

        if not session_id:
            try:
                session = await chat_service.create_session(
                    db,
                    ChatSessionCreate(
                        title=request.question[:50],
                        mode="agent",
                    ),
                )
                session_id = session.id
            except Exception as e:
                logger.warning(f"Failed to create session: {e}")

        if session_id:
            try:
                await chat_service.add_message(
                    db,
                    session_id,
                    ChatMessageCreate(role="user", content=request.question),
                )
                await chat_service.add_message(
                    db,
                    session_id,
                    ChatMessageCreate(
                        role="assistant",
                        content=response.answer,
                        metadata_={
                            "mode_used": response.mode_used,
                            "agent_used": response.agent_used,
                            "data_used": response.data_used,
                        },
                    ),
                )
            except Exception as e:
                logger.warning(f"Failed to persist messages: {e}")

        data = QueryData(
            answer=response.answer,
            sources=[
                Source(
                    document_id=src.get("document_id", "unknown"),
                    filename=src.get("filename", "Unknown"),
                    chunk_index=src.get("chunk_index", 0),
                    similarity_score=src.get("similarity_score", 0.0),
                    preview_text=src.get("preview_text", ""),
                )
                for src in response.sources
            ],
            graph_entities=response.graph_entities,
            cmms_references=response.cmms_references,
            mode_used=response.mode_used,
            agent_used=response.agent_used,
            cypher_used=response.cypher_used,
            tokens_used=response.tokens_used,
            session_id=str(session_id) if session_id else None,
            mutations=response.mutations,
        )

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Agent query processed by {response.agent_used} agent",
        )

    except Exception as e:
        logger.error(f"Error processing agent query: {e}")
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
            cypher_used=result.get("cypher_used"),
            mode_used=result.get("mode_used", "graphrag"),
        )

        return SuccessResponse.create(
            data=data, status_code=200, details="GraphRAG query processed successfully"
        )

    except Exception as e:
        logger.error(f"Error processing GraphRAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
