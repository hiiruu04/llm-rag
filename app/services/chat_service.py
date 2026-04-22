import math
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession
from app.models.schemas import ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate


async def create_session(db: AsyncSession, data: ChatSessionCreate) -> ChatSession:
    session = ChatSession(**data.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID) -> Optional[ChatSession]:
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[ChatSession], int]:
    count_query = select(func.count(ChatSession.id))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    sessions = list(result.scalars().all())
    return sessions, total


async def update_session(
    db: AsyncSession, session: ChatSession, data: ChatSessionUpdate
) -> ChatSession:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    await db.commit()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session: ChatSession) -> None:
    await db.delete(session)
    await db.commit()


async def add_message(db: AsyncSession, session_id: UUID, data: ChatMessageCreate) -> ChatMessage:
    message = ChatMessage(session_id=session_id, **data.model_dump())
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_messages(
    db: AsyncSession,
    session_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ChatMessage], int]:
    count_query = select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    messages = list(result.scalars().all())
    return messages, total


async def get_recent_messages(
    db: AsyncSession, session_id: UUID, window_size: int = 10
) -> list[ChatMessage]:
    query = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(window_size)
    )
    result = await db.execute(query)
    messages = list(result.scalars().all())
    messages.reverse()
    return messages


def format_history_for_llm(messages: list[ChatMessage]) -> list[dict]:
    history = []
    for msg in messages:
        history.append({"role": msg.role, "content": msg.content})
    return history
