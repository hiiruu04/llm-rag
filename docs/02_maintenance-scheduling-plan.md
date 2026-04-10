# Maintenance Scheduling Service - Implementation Plan

## Overview

Add a maintenance scheduling service to the CMMS application, enabling CRUD for scheduled maintenance tasks linked to assets (and optionally to faults for corrective maintenance). Includes overdue detection and recurring schedule generation.

## Files to Create

### 1. `app/models/maintenance_schedule.py` — SQLAlchemy Model

**Table:** `maintenance_schedules`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK, `gen_random_uuid()` |
| `asset_id` | UUID | FK → `assets.id` (CASCADE) |
| `fault_id` | UUID | FK → `faults.id` (SET NULL), nullable |
| `title` | String(255) | NOT NULL |
| `description` | Text | nullable |
| `maintenance_type` | String(20) | NOT NULL, default `"preventive"` |
| `status` | String(20) | NOT NULL, default `"scheduled"` |
| `priority` | String(20) | NOT NULL, default `"medium"` |
| `scheduled_date` | DateTime(tz) | NOT NULL |
| `completed_date` | DateTime(tz) | nullable |
| `assigned_to` | String(255) | nullable |
| `recurrence` | String(20) | NOT NULL, default `"none"` |
| `estimated_duration_hours` | Float | nullable |
| `notes` | Text | nullable |
| `created_at` | DateTime(tz) | NOT NULL, `now()` |
| `updated_at` | DateTime(tz) | NOT NULL, `now()`, `onupdate=now()` |

Relationships: `asset` (back_populates), `fault`. Includes `to_dict()` method.

### 2. `app/services/maintenance_schedule_service.py` — Service Layer

Functions (all async, following `fault_service.py` patterns):

- `create_schedule(db, asset_id, data)` → `MaintenanceSchedule`
- `get_schedule(db, schedule_id)` → `Optional[MaintenanceSchedule]`
- `list_schedules(db, asset_id?, status?, maintenance_type?, priority?, page, per_page)` → `tuple[list, int]`
- `update_schedule(db, schedule, data)` → `MaintenanceSchedule`
- `delete_schedule(db, schedule)` → `None`
- `mark_completed(db, schedule)` → `MaintenanceSchedule` — sets status + completed_date
- `detect_and_mark_overdue(db)` → `list[MaintenanceSchedule]` — bulk UPDATE ... RETURNING
- `get_overdue_schedules(db, page, per_page)` → `tuple[list, int]`
- `generate_next_recurrence(db, schedule)` → `Optional[MaintenanceSchedule]` — creates next occurrence for recurring tasks

Recurrence intervals: daily=1d, weekly=7d, monthly=30d, quarterly=90d, yearly=365d.

### 3. `app/api/routes/maintenance_schedules.py` — API Routes

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/assets/{asset_id}/maintenance-schedules` | Create schedule for asset |
| GET | `/api/v1/assets/{asset_id}/maintenance-schedules` | List schedules for asset (filters: status, type, priority) |
| GET | `/api/v1/maintenance-schedules` | List all schedules (with filters) |
| GET | `/api/v1/maintenance-schedules/overdue` | List overdue schedules (paginated) |
| POST | `/api/v1/maintenance-schedules/detect-overdue` | Bulk detect & mark overdue |
| GET | `/api/v1/maintenance-schedules/{schedule_id}` | Get single schedule |
| PUT | `/api/v1/maintenance-schedules/{schedule_id}` | Update schedule |
| DELETE | `/api/v1/maintenance-schedules/{schedule_id}` | Delete schedule |
| POST | `/api/v1/maintenance-schedules/{schedule_id}/complete` | Mark complete (+ auto-generate next recurrence) |

**Route ordering note:** Static paths (`/overdue`, `/detect-overdue`) must be defined before `/{schedule_id}` to avoid path collision.

### 4. `alembic/versions/002_maintenance_schedules.py` — Migration

Creates `maintenance_schedules` table + 3 indexes:
- `ix_maintenance_schedules_asset_id` on `asset_id`
- `ix_maintenance_schedules_status` on `status`
- `ix_maintenance_schedules_scheduled_date` on `scheduled_date`

`down_revision = "001_initial_cmms"`

## Files to Modify

### 5. `app/models/schemas.py` — Add Pydantic Schemas (append after line 152)

New Literal types:
- `MaintenanceType = Literal["preventive", "corrective", "predictive"]`
- `MaintenanceStatus = Literal["scheduled", "in_progress", "completed", "cancelled", "overdue"]`
- `MaintenancePriority = Literal["low", "medium", "high", "critical"]`
- `MaintenanceRecurrence = Literal["none", "daily", "weekly", "monthly", "quarterly", "yearly"]`

New schemas:
- `MaintenanceScheduleCreate` — title, description, maintenance_type, priority, scheduled_date, fault_id (optional), assigned_to, recurrence, estimated_duration_hours, notes
- `MaintenanceScheduleUpdate` — all fields Optional
- `MaintenanceScheduleResponse` — full model with id, asset_id, timestamps

### 6. `app/models/__init__.py` — Add `MaintenanceSchedule` import and export

### 7. `app/models/asset.py` — Add `maintenance_schedules` relationship (line 25, after `faults`)

### 8. `app/main.py` — Import and register `maintenance_schedules` router (lines 7, 40)

### 9. `alembic/env.py` — Ensure `MaintenanceSchedule` is imported for metadata awareness

## Implementation Order

1. `app/models/maintenance_schedule.py` (new model)
2. `app/models/__init__.py` (register model)
3. `app/models/asset.py` (add relationship)
4. `app/models/schemas.py` (add schemas)
5. `app/services/maintenance_schedule_service.py` (service layer)
6. `app/api/routes/maintenance_schedules.py` (API routes)
7. `app/main.py` (register router)
8. `alembic/versions/002_maintenance_schedules.py` (migration)
9. `alembic/env.py` (update imports)

## Verification

1. Run `alembic upgrade head` to apply the migration
2. Start the app with `uvicorn app.main:app --reload`
3. Verify via Swagger UI at `/docs` that all 9 endpoints appear under the "maintenance-schedules" tag
4. Test the full flow:
   - Create an asset → Create a maintenance schedule for it
   - List schedules with filters
   - Update a schedule status
   - Complete a recurring schedule → verify next occurrence is created
   - Call detect-overdue → verify past-due schedules are marked
   - Delete a schedule
