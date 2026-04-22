# Chat Sessions & Agent Orchestration Implementation Plan

## Overview

Two major features:
1. **Chat/Session Persistence** — Conversation context persists across messages so the LLM has history
2. **Agent-to-Agent Communication** — Multi-intent queries are routed to multiple collaborating agents via an orchestrator

---

## Phase 1: Chat Session & Message Models (Backend)

### New file: `app/models/chat.py`

Two SQLAlchemy models:

```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id          = UUID PK, auto-generated
    title       = String(255), nullable=True  # auto-set from first user message
    mode        = String(20), default="auto"   # query mode used
    created_at  = DateTime, server_default=now
    updated_at  = DateTime, onupdate=now
    messages    = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id           = UUID PK, auto-generated
    session_id   = UUID FK -> chat_sessions.id, CASCADE
    role         = String(20)  # "user" | "assistant" | "system"
    content      = Text
    metadata_    = JSON  # stores agent_used, mode_used, sources, etc.
    created_at   = DateTime, server_default=now
```

### New file: `alembic/versions/010_chat_sessions.py`

Migration creating `chat_sessions` and `chat_messages` tables.

### Modify: `app/models/schemas.py`

Add Pydantic schemas:
- `ChatSessionCreate(title?, mode?)` -> `ChatSessionResponse(id, title, mode, created_at, updated_at)`
- `ChatMessageCreate(role, content, metadata_?)` -> `ChatMessageResponse(id, session_id, role, content, metadata_, created_at)`
- `ChatSessionDetailResponse` — session + its messages

### Modify: `app/models/__init__.py`

Export `ChatSession`, `ChatMessage`

---

## Phase 2: Chat Service & API Routes (Backend)

### New file: `app/services/chat_service.py`

CRUD operations:
- `create_session(db, data) -> ChatSession`
- `get_session(db, session_id) -> ChatSession`
- `list_sessions(db, page, per_page) -> (list[ChatSession], total)`
- `delete_session(db, session_id)`
- `add_message(db, session_id, data) -> ChatMessage`
- `get_messages(db, session_id, limit=20, offset=0) -> list[ChatMessage]`
- `get_recent_messages(db, session_id, window_size=10) -> list[ChatMessage]`

### New file: `app/api/routes/chats.py`

```
POST   /api/v1/chats                        -> create session
GET    /api/v1/chats                         -> list sessions (paginated)
GET    /api/v1/chats/{session_id}           -> get session + messages
DELETE /api/v1/chats/{session_id}            -> delete session
GET    /api/v1/chats/{session_id}/messages   -> get messages (paginated)
```

### Modify: `app/main.py`

Register `chats` router.

---

## Phase 3: Integrate Sessions into Query Flow (Backend)

### Modify: `app/agents/base.py`

- Add `history` parameter to `handle()` and `generate_answer()`
- `generate_answer()` constructs messages: system prompt + history (sliding window) + current user message
- Add abstract `gather_data()` method for agent-to-agent delegation

### Modify: All 4 agents

Update `handle()` signature to accept `history` and pass it to `generate_answer()`.

### Modify: `app/agents/router.py`

Pass `history` through to agent.

### Modify: `app/api/routes/query.py`

- Add optional `session_id` to `QueryRequest` and `AgentQueryRequest`
- If `session_id` provided, load recent messages (sliding window of last 10)
- Pass `history` to `AgentRouter.route()`
- After response, persist user message + assistant message as `ChatMessage` rows
- Return `session_id` in response

---

## Phase 4: Agent-to-Agent Communication (Backend)

### Add `gather_data()` to each agent in `app/agents/base.py`

Abstract method that returns raw context string without LLM synthesis. Each agent implements by running its `_gather_*` methods.

### Implement `gather_data()` on each agent:

- `SchedulingAgent.gather_data()` -> shift + schedule + task + worker data
- `CompetencyAgent.gather_data()` -> competence + availability + task requirements data
- `AnalyzerAgent.gather_data()` -> KPI + down_event + fault + sensor + statistics data
- `RecommenderAgent.gather_data()` -> fault + cause + task + material + doc data

### New file: `app/agents/orchestrator.py`

`AgentOrchestrator` class:
- Receives question, entities, list of agents to collaborate
- Calls `gather_data()` on each agent in parallel via `asyncio.gather()`
- Merges all contexts with labeled sections
- Makes final LLM call with synthesis prompt
- Returns `AgentResponse` with `agent_used` = e.g. `"scheduling+competency+recommender"`

### Modify: `app/services/intent_classifier.py`

Add `classify_multi()` method:
- Extended prompt that detects cross-domain queries
- Returns `(single_intent_or_None, agent_list_or_None)`
- Collaboration patterns:
  - `"recommend_worker"` -> ["scheduling", "competency", "recommender"]
  - `"troubleshoot_assignment"` -> ["recommender", "competency", "scheduling"]
  - `"maintenance_analysis"` -> ["analyzer", "recommender"]

### Modify: `app/agents/router.py`

Detect multi-intent queries and route to `AgentOrchestrator`.

---

## Phase 5: Frontend — Session-Aware Chat UI

### New file: `frontend/src/types/chat.ts`

TypeScript types for `ChatSession`, `ChatMessage`.

### New file: `frontend/src/api/chats.ts`

TanStack Query hooks for session CRUD and message listing.

### New file: `frontend/src/stores/chat-store.ts`

Zustand store for `activeSessionId` state management.

### Modify: `frontend/src/types/query.ts`

Add `session_id` field to `QueryData`.

### Modify: `frontend/src/api/query.ts`

Pass `session_id` in query mutations; update `QueryRequest` type.

### Rewrite: `frontend/src/features/query/query-page.tsx`

Session-aware chat UI with:
- Session sidebar listing all sessions
- New Chat button
- Auto-create session on first message
- Load messages from DB when switching sessions
- Persist user + assistant messages

### Modify: `frontend/src/router/index.tsx`

Add `/chats/:sessionId` route.

### Delete: `frontend/src/stores/query-history-store.ts`

Replaced by `chat-store.ts`.

---

## Phase 6: Run Migration & Verify

- Run `alembic upgrade head`
- Verify all endpoints work
- Test multi-agent queries

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| History format | Sliding window (last 10 messages) | Balances token cost and context quality |
| Orchestration style | Router-level | Keeps agents decoupled; orchestrator coordinates |
| Frontend scope | Full stack | Session management UI needed for the feature to be usable |
| Session creation | Auto-create on first message | Seamless UX |
| Multi-agent synthesis | Single LLM call with merged contexts | Simpler than multi-LLM-chain; cost-effective |