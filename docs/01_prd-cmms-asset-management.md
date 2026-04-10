# PRD: CMMS Asset Management Module

## 1. Overview

### 1.1 Purpose

Extend the existing llm-rag FastAPI application with a CMMS (Computerized Maintenance Management System) asset management module. This module provides CRUD services for industrial assets, their attached sensors, and registered faults — including hierarchical asset structures and fault cause/effect linkages.

### 1.2 Goals

- Introduce PostgreSQL as a persistent relational store alongside the existing Qdrant vector database.
- Add SQLAlchemy (async) as the ORM layer and Alembic for schema migrations.
- Expose RESTful API endpoints under the existing `/api/v1/` prefix following current project conventions.
- Keep the new module self-contained so existing RAG functionality is unaffected.

### 1.3 Non-Goals

- RAG-augmented querying over CMMS data (future milestone).
- User authentication / authorization.
- Real-time sensor data ingestion pipelines.
- Mobile or frontend UI.

---

## 2. Technology Stack Additions

| Component        | Version        | Purpose                          |
| ---------------- | -------------- | -------------------------------- |
| PostgreSQL       | 16+            | Primary relational database      |
| SQLAlchemy       | 2.0+ (async)   | ORM with async session support   |
| Alembic          | 1.13+          | Database schema migrations       |
| asyncpg          | 0.29+          | Async PostgreSQL driver          |
| psycopg2-binary  | 2.9+           | Sync driver (Alembic migrations) |

### 2.1 New Dependencies (`pyproject.toml`)

```toml
"sqlalchemy[asyncio]>=2.0.0",
"alembic>=1.13.0",
"asyncpg>=0.29.0",
"psycopg2-binary>=2.9.0",
```

### 2.2 New Configuration Fields (`app/core/config.py`)

```python
# PostgreSQL
postgres_user: str = "postgres"
postgres_password: str = "postgres"
postgres_host: str = "localhost"
postgres_port: int = 5432
postgres_db: str = "llm_rag"

@property
def database_url(self) -> str:
    return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

@property
def database_url_sync(self) -> str:
    return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
```

---

## 3. Data Model

### 3.1 Entity-Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐
│      Asset       │       │      Sensor      │
├──────────────────┤       ├──────────────────┤
│ id (PK, UUID)    │◄──────│ id (PK, UUID)    │
│ name             │  1:N  │ asset_id (FK)    │
│ description      │       │ name             │
│ asset_type       │       │ sensor_type      │
│ parent_id (FK)   │──┐    │ unit             │
│ status           │  │    │ status           │
│ location         │  │    │ created_at       │
│ created_at       │  │    │ updated_at       │
│ updated_at       │  │    └────────┬─────────┘
└──────────────────┘  │             │
        ▲             │             │ 1:N
        │ self-ref    │             ▼
        └─────────────┘    ┌──────────────────┐
                           │   SensorData     │
                           ├──────────────────┤
                           │ id (PK, BIGSERIAL)│
                           │ sensor_id (FK)   │
                           │ timestamp        │
                           │ value            │
                           └──────────────────┘
        │
        │ 1:N
        ▼
┌──────────────────┐       ┌──────────────────────────────┐
│      Fault       │       │      fault_cause_effect      │
├──────────────────┤       │      (association table)     │
│ id (PK, UUID)    │       ├──────────────────────────────┤
│ asset_id (FK)    │       │ causing_fault_id (FK)        │
│ code             │       │ affected_fault_id (FK)       │
│ name             │       │ link_type (enum)             │
│ description      │       └──────────────────────────────┘
│ severity         │
│ status           │
│ detected_at      │
│ resolved_at      │
│ created_at       │
│ updated_at       │
└──────────────────┘
```

### 3.2 Tables

#### `assets`

| Column       | Type             | Constraints                            |
| ------------ | ---------------- | -------------------------------------- |
| id           | UUID             | PK, server-default `gen_random_uuid()` |
| name         | VARCHAR(255)     | NOT NULL                               |
| description  | TEXT             |                                        |
| asset_type   | VARCHAR(100)     | NOT NULL                               |
| parent_id    | UUID             | FK `assets.id`, ON DELETE SET NULL     |
| status       | VARCHAR(50)      | NOT NULL, default `"active"`           |
| location     | VARCHAR(255)     |                                        |
| created_at   | TIMESTAMPTZ      | NOT NULL, default `now()`              |
| updated_at   | TIMESTAMPTZ      | NOT NULL, default `now()`, auto-update |

**Self-referential hierarchy**: `parent_id` references `assets.id`. A `NULL` `parent_id` indicates a root-level asset. Max depth is not enforced at DB level but should be validated in application logic.

#### `sensors`

| Column      | Type             | Constraints                            |
| ----------- | ---------------- | -------------------------------------- |
| id          | UUID             | PK, server-default `gen_random_uuid()` |
| asset_id    | UUID             | FK `assets.id`, ON DELETE CASCADE      |
| name        | VARCHAR(255)     | NOT NULL                               |
| sensor_type | VARCHAR(100)     | NOT NULL                               |
| unit        | VARCHAR(50)      |                                        |
| status      | VARCHAR(50)      | NOT NULL, default `"active"`           |
| created_at  | TIMESTAMPTZ      | NOT NULL, default `now()`              |
| updated_at  | TIMESTAMPTZ      | NOT NULL, default `now()`, auto-update |

#### `sensor_data`

Stores individual sensor readings over time.

| Column     | Type         | Constraints                                   |
| ---------- | ------------ | --------------------------------------------- |
| id         | BIGSERIAL    | PK                                            |
| sensor_id  | UUID         | FK `sensors.id`, ON DELETE CASCADE            |
| timestamp  | TIMESTAMPTZ  | NOT NULL, default `now()`                     |
| value      | DOUBLE       | NOT NULL                                      |

**Index**: `ix_sensor_data_sensor_id_timestamp` on `(sensor_id, timestamp DESC)` — optimizes queries that fetch recent readings for a specific sensor.

#### `faults`

| Column      | Type             | Constraints                            |
| ----------- | ---------------- | -------------------------------------- |
| id          | UUID             | PK, server-default `gen_random_uuid()` |
| asset_id    | UUID             | FK `assets.id`, ON DELETE CASCADE      |
| code        | VARCHAR(50)      | NOT NULL                               |
| name        | VARCHAR(255)     | NOT NULL                               |
| description | TEXT             |                                        |
| severity    | VARCHAR(20)      | NOT NULL, default `"medium"`           |
| status      | VARCHAR(50)      | NOT NULL, default `"open"`             |
| detected_at | TIMESTAMPTZ      | NOT NULL, default `now()`              |
| resolved_at | TIMESTAMPTZ      |                                        |
| created_at  | TIMESTAMPTZ      | NOT NULL, default `now()`              |
| updated_at  | TIMESTAMPTZ      | NOT NULL, default `now()`, auto-update |

**Unique constraint**: `(asset_id, code)` — fault codes are unique per asset.

#### `fault_cause_effect` (association table)

| Column             | Type         | Constraints                                   |
| ------------------ | ------------ | --------------------------------------------- |
| causing_fault_id   | UUID         | FK `faults.id`, ON DELETE CASCADE             |
| affected_fault_id  | UUID         | FK `faults.id`, ON DELETE CASCADE             |
| link_type          | VARCHAR(20)  | NOT NULL, `"cause"` or `"effect"`             |

**Unique constraint**: `(causing_fault_id, affected_fault_id)`.

**Check constraint**: `causing_fault_id <> affected_fault_id` (no self-loops).

### 3.3 Enums (Application-Level)

These are enforced via Pydantic validators rather than PostgreSQL enum types for migration flexibility.

**AssetStatus**: `active`, `inactive`, `maintenance`, `decommissioned`

**SensorStatus**: `active`, `inactive`, `faulty`

**FaultSeverity**: `low`, `medium`, `high`, `critical`

**FaultStatus**: `open`, `investigating`, `resolved`, `closed`

**FaultLinkType**: `cause`, `effect`

---

## 4. API Design

All endpoints follow existing conventions:
- Prefix: `/api/v1`
- Response wrapper: `SuccessResponse[T]` / `ErrorResponse`
- Pagination: `page` + `per_page` query parameters, `Pagination` metadata
- Router tags for OpenAPI grouping

### 4.1 Assets

| Method | Path                           | Description                    |
| ------ | ------------------------------ | ------------------------------ |
| POST   | `/api/v1/assets`               | Create an asset                |
| GET    | `/api/v1/assets`               | List assets (paginated)        |
| GET    | `/api/v1/assets/{asset_id}`    | Get asset by ID                |
| PUT    | `/api/v1/assets/{asset_id}`    | Update asset                   |
| DELETE | `/api/v1/assets/{asset_id}`    | Delete asset                   |
| GET    | `/api/v1/assets/{asset_id}/children` | List child assets (paginated) |
| GET    | `/api/v1/assets/tree`          | Get full asset tree            |

#### `POST /api/v1/assets`

**Request body:**

```json
{
  "name": "Compressor Unit A",
  "description": "Main air compressor for Building 3",
  "asset_type": "equipment",
  "parent_id": null,
  "status": "active",
  "location": "Building 3, Room 12"
}
```

**Response `data`:**

```json
{
  "id": "01234567-...",
  "name": "Compressor Unit A",
  "description": "Main air compressor for Building 3",
  "asset_type": "equipment",
  "parent_id": null,
  "status": "active",
  "location": "Building 3, Room 12",
  "created_at": "2026-04-08T10:00:00Z",
  "updated_at": "2026-04-08T10:00:00Z"
}
```

#### `GET /api/v1/assets`

**Query parameters:**

| Param      | Type   | Default | Description                     |
| ---------- | ------ | ------- | ------------------------------- |
| page       | int    | 1       | Page number (>= 1)              |
| per_page   | int    | 10      | Items per page (1–100)          |
| status     | string | —       | Filter by status                |
| asset_type | string | —       | Filter by asset type            |
| parent_id  | string | —       | Filter by parent (use "null" for roots) |

#### `GET /api/v1/assets/tree`

Returns the full asset hierarchy as a nested tree structure.

**Response `data`:**

```json
[
  {
    "id": "...",
    "name": "Building 3",
    "asset_type": "facility",
    "status": "active",
    "children": [
      {
        "id": "...",
        "name": "Compressor Unit A",
        "asset_type": "equipment",
        "status": "active",
        "children": []
      }
    ]
  }
]
```

### 4.2 Sensors

| Method | Path                                        | Description              |
| ------ | ------------------------------------------- | ------------------------ |
| POST   | `/api/v1/assets/{asset_id}/sensors`         | Create sensor for asset  |
| GET    | `/api/v1/assets/{asset_id}/sensors`         | List sensors for asset   |
| GET    | `/api/v1/sensors/{sensor_id}`               | Get sensor by ID         |
| PUT    | `/api/v1/sensors/{sensor_id}`               | Update sensor            |
| DELETE | `/api/v1/sensors/{sensor_id}`               | Delete sensor            |

#### `POST /api/v1/assets/{asset_id}/sensors`

**Request body:**

```json
{
  "name": "Temperature Sensor 1",
  "sensor_type": "temperature",
  "unit": "celsius",
  "status": "active"
}
```

**Response `data`:**

```json
{
  "id": "...",
  "asset_id": "...",
  "name": "Temperature Sensor 1",
  "sensor_type": "temperature",
  "unit": "celsius",
  "status": "active",
  "created_at": "2026-04-08T10:00:00Z",
  "updated_at": "2026-04-08T10:00:00Z"
}
```

### 4.3 Sensor Data

| Method | Path                                                  | Description                       |
| ------ | ----------------------------------------------------- | --------------------------------- |
| POST   | `/api/v1/sensors/{sensor_id}/data`                    | Record a sensor reading           |
| POST   | `/api/v1/sensors/{sensor_id}/data/batch`              | Record multiple readings at once  |
| GET    | `/api/v1/sensors/{sensor_id}/data`                    | List readings (paginated, newest first) |
| GET    | `/api/v1/sensors/{sensor_id}/data/latest`             | Get the most recent reading       |
| DELETE | `/api/v1/sensors/{sensor_id}/data`                    | Delete readings in a time range   |

#### `POST /api/v1/sensors/{sensor_id}/data`

**Request body:**

```json
{
  "timestamp": "2026-04-08T10:00:00Z",
  "value": 72.5
}
```

If `timestamp` is omitted, the server defaults to `now()`.

**Response `data`:**

```json
{
  "id": 1042,
  "sensor_id": "...",
  "timestamp": "2026-04-08T10:00:00Z",
  "value": 72.5
}
```

#### `POST /api/v1/sensors/{sensor_id}/data/batch`

**Request body:**

```json
{
  "readings": [
    {"timestamp": "2026-04-08T10:00:00Z", "value": 72.5},
    {"timestamp": "2026-04-08T10:01:00Z", "value": 73.1},
    {"timestamp": "2026-04-08T10:02:00Z", "value": 72.8}
  ]
}
```

**Response `data`:**

```json
{
  "count": 3
}
```

#### `GET /api/v1/sensors/{sensor_id}/data`

**Query parameters:**

| Param      | Type   | Default | Description                     |
| ---------- | ------ | ------- | ------------------------------- |
| page       | int    | 1       | Page number (>= 1)              |
| per_page   | int    | 50      | Items per page (1–1000)         |
| start_time | string | —       | Filter readings >= this time    |
| end_time   | string | —       | Filter readings <= this time    |

Readings are returned newest-first (descending `timestamp`), leveraging the `(sensor_id, timestamp DESC)` index.

#### `GET /api/v1/sensors/{sensor_id}/data/latest`

**Response `data`:**

```json
{
  "id": 1042,
  "sensor_id": "...",
  "timestamp": "2026-04-08T10:02:00Z",
  "value": 72.8
}
```

Returns `404` if no readings exist for the sensor.

#### `DELETE /api/v1/sensors/{sensor_id}/data`

**Query parameters:**

| Param      | Type   | Description                       |
| ---------- | ------ | --------------------------------- |
| start_time | string | Required. Delete readings >= this |
| end_time   | string | Required. Delete readings <= this |

**Response `data`:**

```json
{
  "deleted_count": 150
}
```

### 4.4 Faults

| Method | Path                                            | Description                    |
| ------ | ----------------------------------------------- | ------------------------------ |
| POST   | `/api/v1/assets/{asset_id}/faults`              | Register fault for asset       |
| GET    | `/api/v1/assets/{asset_id}/faults`              | List faults for asset          |
| GET    | `/api/v1/faults/{fault_id}`                     | Get fault by ID                |
| PUT    | `/api/v1/faults/{fault_id}`                     | Update fault                   |
| DELETE | `/api/v1/faults/{fault_id}`                     | Delete fault                   |
| POST   | `/api/v1/faults/{fault_id}/links`               | Add cause/effect link          |
| DELETE | `/api/v1/faults/{fault_id}/links/{linked_id}`   | Remove cause/effect link       |
| GET    | `/api/v1/faults/{fault_id}/causes`              | List causes of fault           |
| GET    | `/api/v1/faults/{fault_id}/effects`             | List effects of fault          |

#### `POST /api/v1/assets/{asset_id}/faults`

**Request body:**

```json
{
  "code": "OVERHEAT-001",
  "name": "Bearing Overheat",
  "description": "Bearings running above threshold temperature",
  "severity": "high",
  "status": "open",
  "detected_at": "2026-04-08T09:30:00Z"
}
```

#### `POST /api/v1/faults/{fault_id}/links`

**Request body:**

```json
{
  "linked_fault_id": "98765432-...",
  "link_type": "cause"
}
```

This records that `linked_fault_id` is a **cause** of `fault_id`. The inverse relationship (effect) is automatically queryable.

#### `GET /api/v1/faults/{fault_id}/causes`

Returns all faults that are recorded as causes of the given fault.

#### `GET /api/v1/faults/{fault_id}/effects`

Returns all faults that are recorded as effects of the given fault.

---

## 5. Project Structure Changes

New files and directories to add:

```
app/
├── api/
│   └── routes/
│       ├── assets.py          # Asset endpoints
│       ├── sensors.py         # Sensor endpoints
│       ├── sensor_data.py     # Sensor data (readings) endpoints
│       └── faults.py          # Fault endpoints
├── core/
│   ├── config.py              # (modify) add PostgreSQL settings
│   └── database.py            # NEW: engine, session factory, base class
├── models/
│   ├── __init__.py            # (modify) export all models
│   ├── asset.py               # Asset SQLAlchemy model
│   ├── sensor.py              # Sensor SQLAlchemy model
│   ├── sensor_data.py         # SensorData SQLAlchemy model
│   ├── fault.py               # Fault SQLAlchemy model + association table
│   └── schemas.py             # Pydantic request/response schemas
├── services/
│   ├── __init__.py
│   ├── asset_service.py       # Asset business logic
│   ├── sensor_service.py      # Sensor business logic
│   ├── sensor_data_service.py # Sensor data business logic
│   └── fault_service.py       # Fault business logic
└── main.py                    # (modify) register new routers, init DB

alembic/
├── env.py
├── script.py.mako
└── versions/
    └── 001_initial_cmms.py

alembic.ini
```

### 5.1 Database Session Module (`app/core/database.py`)

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
```

`get_db` is used as a FastAPI `Depends` injection in route handlers.

---

## 6. Migration Strategy

### 6.1 Alembic Setup

1. Initialize Alembic in the project root:

   ```bash
   alembic init alembic
   ```

2. Configure `alembic/env.py` to:
   - Import `Base.metadata` from `app.core.database` as `target_metadata`.
   - Use `settings.database_url_sync` for the synchronous connection Alembic requires.
   - Configure `render_as_batch=True` for SQLite compatibility during testing (optional).

3. Configure `alembic.ini`:

   ```ini
   sqlalchemy.url = postgresql+psycopg2://postgres:postgres@localhost:5432/llm_rag
   ```

   > The actual URL is overridden in `env.py` from `settings.database_url_sync`.

### 6.2 Initial Migration

```bash
alembic revision --autogenerate -m "001_initial_cmms"
alembic upgrade head
```

This creates all five tables: `assets`, `sensors`, `sensor_data`, `faults`, `fault_cause_effect`.

### 6.3 Migration Workflow

- Every schema change generates a new Alembic revision.
- Migrations run automatically on app startup in development (via `alembic upgrade head` in the Docker entrypoint).
- In production, migrations are run explicitly before deployment.

---

## 7. Docker Compose Changes

Add a PostgreSQL service to `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: llm-rag-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-llm_rag}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    # ... existing config ...
    environment:
      # ... existing vars ...
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${POSTGRES_DB:-llm_rag}
    depends_on:
      qdrant:
        condition: service_healthy
      postgres:
        condition: service_healthy

volumes:
  qdrant_data:
    driver: local
  postgres_data:
    driver: local
```

---

## 8. Error Handling

Follow existing error patterns from `app/api/routes/documents.py`:

- **400 Bad Request**: Validation errors (invalid status, self-referential parent loop, self-loop in fault links).
- **404 Not Found**: Asset, Sensor, or Fault not found.
- **409 Conflict**: Duplicate fault code for the same asset.
- **422 Unprocessable Entity**: Pydantic validation failures (handled automatically by FastAPI).
- **500 Internal Server Error**: Unexpected database or application errors.

All errors use the `ErrorResponse` format:

```json
{
  "data": null,
  "meta": {
    "status_code": 404,
    "details": "Asset not found",
    "errors": ["Asset 01234567-... does not exist"]
  }
}
```

---

## 9. Implementation Sequence

| Step | Task                                        | Files / Areas                                      |
| ---- | ------------------------------------------- | -------------------------------------------------- |
| 1    | Add dependencies to `pyproject.toml`        | `pyproject.toml`                                   |
| 2    | Add PostgreSQL config to Settings           | `app/core/config.py`                               |
| 3    | Create database module                      | `app/core/database.py`                             |
| 4    | Create SQLAlchemy models                    | `app/models/asset.py`, `sensor.py`, `sensor_data.py`, `fault.py` |
| 5    | Create Pydantic schemas                     | `app/models/schemas.py`                            |
| 6    | Initialize Alembic, generate initial migration | `alembic/`, `alembic.ini`                       |
| 7    | Create service layer                        | `app/services/asset_service.py`, etc.              |
| 8    | Create route handlers                       | `app/api/routes/assets.py`, `sensor_data.py`, etc. |
| 9    | Register routers in `main.py`               | `app/main.py`                                      |
| 10   | Update Docker Compose                       | `docker-compose.yml`, `Dockerfile`                 |
| 11   | Update health check to include PostgreSQL   | `app/api/routes/health.py`                         |
| 12   | Write tests                                 | `tests/`                                           |

---

## 10. Validation Rules

### Assets

- `name` is required, 1–255 characters.
- `asset_type` is required, 1–100 characters.
- `status` must be one of: `active`, `inactive`, `maintenance`, `decommissioned`.
- `parent_id` must reference an existing asset (or be `null`).
- Circular parent references must be rejected (validate the ancestor chain before setting `parent_id`).

### Sensors

- `name` is required, 1–255 characters.
- `sensor_type` is required, 1–100 characters.
- `status` must be one of: `active`, `inactive`, `faulty`.
- `asset_id` must reference an existing asset.

### Sensor Data

- `sensor_id` must reference an existing sensor.
- `value` is required, must be a numeric (float).
- `timestamp` is optional; defaults to server time (`now()`).
- Batch inserts are limited to 1000 readings per request.

### Faults

- `code` is required, 1–50 characters, unique per asset.
- `name` is required, 1–255 characters.
- `severity` must be one of: `low`, `medium`, `high`, `critical`.
- `status` must be one of: `open`, `investigating`, `resolved`, `closed`.
- `asset_id` must reference an existing asset.
- `resolved_at` can only be set when `status` is `resolved` or `closed`.
- Fault link self-references (`causing_fault_id == affected_fault_id`) are rejected.

---

## 11. Open Questions

| #   | Question                                            | Default Stance                      |
| --- | --------------------------------------------------- | ----------------------------------- |
| 1   | Should assets support soft-delete (e.g., `deleted_at`)? | No — hard delete with `ON DELETE CASCADE` for simplicity. |
| 2   | Should the asset tree have a maximum depth limit?   | No DB-level limit; validate in service if needed later. |
| 3   | Should fault links be directional (cause vs. effect)? | Yes — `link_type` field distinguishes direction. |
| 4   | Should sensor data have a retention / auto-purge policy? | Not yet. Add configurable TTL in a future milestone if needed. |
