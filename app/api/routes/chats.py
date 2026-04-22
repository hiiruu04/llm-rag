import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Pagination, SuccessResponse
from app.core.database import get_db
from app.models.schemas import (
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionDetailResponse,
    ChatSessionResponse,
    ChatSessionUpdate,
)
from app.services import chat_service

router = APIRouter(prefix="/api/v1", tags=["chats"])


@router.post("/chats", status_code=201)
async def create_chat_session(
    data: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Creating chat session (mode={data.mode})")

    try:
        session = await chat_service.create_session(db, data)
        return SuccessResponse.create(
            data=ChatSessionResponse(**session.to_dict()),
            status_code=201,
            details="Chat session created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
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


@router.get("/chats")
async def list_chat_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Listing chat sessions (page={page}, per_page={per_page})")

    try:
        sessions, total = await chat_service.list_sessions(db, page=page, per_page=per_page)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [ChatSessionResponse(**s.to_dict()) for s in sessions]

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} chat sessions",
            pagination=Pagination(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
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


@router.get("/chats/{session_id}")
async def get_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Getting chat session {session_id}")

    session = await chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Chat session not found",
                    "errors": [f"Chat session {session_id} does not exist"],
                },
            },
        )

    messages, total = await chat_service.get_messages(db, session_id)
    session_dict = session.to_dict()
    session_dict["messages"] = [ChatMessageResponse(**m.to_dict()) for m in messages]

    return SuccessResponse.create(
        data=ChatSessionDetailResponse(**session_dict),
        status_code=200,
        details="Chat session retrieved",
    )


@router.patch("/chats/{session_id}")
async def update_chat_session(
    session_id: UUID,
    data: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Updating chat session {session_id}")

    session = await chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Chat session not found",
                    "errors": [f"Chat session {session_id} does not exist"],
                },
            },
        )

    try:
        updated = await chat_service.update_session(db, session, data)
        return SuccessResponse.create(
            data=ChatSessionResponse(**updated.to_dict()),
            status_code=200,
            details="Chat session updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating chat session: {e}")
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


@router.delete("/chats/{session_id}")
async def delete_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Deleting chat session {session_id}")

    session = await chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Chat session not found",
                    "errors": [f"Chat session {session_id} does not exist"],
                },
            },
        )

    try:
        await chat_service.delete_session(db, session)
        return SuccessResponse.create(
            data={"id": str(session_id)},
            status_code=200,
            details="Chat session deleted successfully",
        )
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
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


@router.get("/chats/{session_id}/messages")
async def get_chat_messages(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Getting messages for chat session {session_id}")

    session = await chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "data": None,
                "meta": {
                    "status_code": 404,
                    "details": "Chat session not found",
                    "errors": [f"Chat session {session_id} does not exist"],
                },
            },
        )

    try:
        messages, total = await chat_service.get_messages(
            db, session_id, limit=limit, offset=offset
        )
        data = [ChatMessageResponse(**m.to_dict()) for m in messages]
        total_pages = math.ceil(total / limit) if total > 0 else 0

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(data)} messages",
            pagination=Pagination(
                page=(offset // limit) + 1,
                per_page=limit,
                total=total,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}")
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
