# CMMS Frontend UI Implementation Plan

## Overview
Build a full-featured React + TypeScript frontend for the LLM-RAG CMMS platform in a `frontend/` monorepo subdirectory. Uses Vite, Shadcn/ui + Tailwind, TanStack Query, Zustand, Recharts, and react-hook-form + Zod.

## Tech Stack
- **Build**: Vite with React + TypeScript template
- **UI**: Shadcn/ui + Tailwind CSS + Radix primitives
- **Routing**: React Router v6
- **Data Fetching**: TanStack Query v5 + Axios
- **State**: Zustand (theme, sidebar, query history)
- **Forms**: react-hook-form + Zod validation
- **Charts**: Recharts (sensor data time-series)
- **Icons**: Lucide React
- **Dates**: date-fns
- **File Upload**: react-dropzone
- **Markdown**: react-markdown + remark-gfm

## Directory Structure

```
frontend/
  index.html
  package.json
  vite.config.ts
  tailwind.config.ts
  postcss.config.js
  components.json                    # shadcn/ui config
  .env                               # VITE_API_BASE_URL=http://localhost:8000
  src/
    main.tsx
    App.tsx
    globals.css
    lib/
      api-client.ts                  # Axios + envelope unwrapping interceptor
      query-client.ts                # TanStack Query provider config
      utils.ts                       # cn() helper
    types/                           # TypeScript types mirroring backend schemas
      api.ts                         # ApiResponse<T>, Meta, Pagination
      asset.ts                       # Asset, AssetCreate, AssetUpdate, AssetTreeNode
      sensor.ts                      # Sensor, SensorCreate, SensorUpdate
      sensor-data.ts                 # SensorData, SensorDataCreate, BatchInsertResponse
      fault.ts                       # Fault, FaultCreate, FaultUpdate, FaultLinkCreate
      maintenance.ts                 # MaintenanceSchedule, ScheduleCreate, ScheduleUpdate
      document.ts                    # DocumentInfo
      health.ts                      # HealthData
      query.ts                       # QueryRequest, QueryData, Source, TokenUsage
      graph.ts                       # SyncStatusData, GraphInfoData
    api/                             # TanStack Query hooks per domain
      assets.ts
      sensors.ts
      sensor-data.ts
      faults.ts
      maintenance.ts
      documents.ts
      health.ts
      query.ts
      graph.ts
    stores/
      theme-store.ts                 # Dark/light toggle (localStorage persisted)
      sidebar-store.ts               # Sidebar collapsed state
      query-history-store.ts         # AI query history (localStorage, max 50)
    components/
      ui/                            # Shadcn/ui components (auto-generated)
      layout/
        app-layout.tsx               # Sidebar + Header + content
        sidebar.tsx                  # Navigation sidebar
        header.tsx                   # Top bar with breadcrumbs + theme toggle
        page-header.tsx              # Reusable page title + actions
      common/
        data-table.tsx               # Generic paginated table
        pagination.tsx               # Page controls
        confirm-dialog.tsx           # Delete/action confirmation
        loading-state.tsx            # Skeleton loader
        error-state.tsx              # Error + retry
        empty-state.tsx              # Empty data placeholder
        status-badge.tsx             # Color-coded badge for enums
        search-input.tsx             # Debounced search
        filter-bar.tsx               # Composable filter row
        date-range-picker.tsx        # Start/end date picker
        file-upload.tsx              # Drag-and-drop file area
    features/
      dashboard/                     # GET / (health, metrics, activity, quick actions)
      assets/                        # /assets, /assets/:id, /assets/new, /assets/:id/edit
      sensors/                       # /sensors/:id (detail page)
      sensor-data/                   # /sensors/:id/data (chart + CRUD)
      faults/                        # /faults, /faults/:id, create, edit, relationships
      maintenance/                   # /maintenance, create, edit, calendar view
      documents/                     # /documents (upload, list, delete)
      query/                         # /query (chat interface with mode selector)
      graph-admin/                   # /admin/graph (sync controls, stats)
      health/                        # /health (service status cards)
    router/
      index.tsx                      # Route definitions
```

## Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | DashboardPage | Health status, metrics, recent activity, quick actions |
| `/assets` | AssetsPage | Asset list (table + tree view toggle), filters, search |
| `/assets/new` | AssetCreatePage | Create asset form |
| `/assets/:id` | AssetDetailPage | Tabs: details, children, sensors, faults, maintenance |
| `/assets/:id/edit` | AssetEditPage | Edit asset form |
| `/sensors/:id` | SensorDetailPage | Sensor info |
| `/sensors/:id/data` | SensorDataPage | Time-series chart, data entry, batch import |
| `/faults` | FaultsPage | Global fault list with severity/status filters |
| `/faults/:id` | FaultDetailPage | Fault info + cause-effect relationship graph |
| `/assets/:assetId/faults/new` | FaultCreatePage | Create fault for an asset |
| `/faults/:id/edit` | FaultEditPage | Edit fault |
| `/maintenance` | MaintenancePage | Schedule list + calendar view, overdue banner |
| `/assets/:assetId/maintenance/new` | ScheduleCreatePage | Create schedule |
| `/maintenance/:id/edit` | ScheduleEditPage | Edit schedule |
| `/documents` | DocumentsPage | Upload + document list |
| `/query` | QueryPage | AI chat interface (auto/vector/graph/hybrid) |
| `/admin/graph` | GraphAdminPage | Neo4j sync controls + stats |
| `/health` | HealthPage | Detailed service health |

## API Client Design

The backend wraps all responses in `{ data, meta }`. The Axios response interceptor unwraps this automatically, attaching `meta` (including pagination) to response headers so TanStack Query hooks receive clean data.

Key helper:
```typescript
export async function paginatedGet<T>(url: string, params?: Record<string, any>) {
  const res = await apiClient.get(url, { params });
  return { data: res.data as T[], pagination: extractPagination(res) };
}
```

## Implementation Phases

### Phase 1: Project Scaffolding
- Initialize Vite project in `frontend/`
- Install all dependencies
- Configure Tailwind, path aliases (`@/`), tsconfig
- Initialize shadcn/ui, add base components
- Create `.env` with `VITE_API_BASE_URL`
- Create API client with envelope interceptor
- Create TanStack Query provider
- Create types (mirror all backend schemas)

### Phase 2: Layout & Shared Components
- `AppLayout` (sidebar + header + content)
- `Sidebar` with navigation sections (CMMS / AI / Admin)
- `Header` with breadcrumbs + theme toggle
- `DataTable`, `Pagination`, `ConfirmDialog`
- `StatusBadge`, `SearchInput`, `FilterBar`
- `LoadingState`, `ErrorState`, `EmptyState`
- `PageHeader`, `FileUpload`, `DateRangePicker`

### Phase 3: Asset Management
- API hooks (`useAssets`, `useAsset`, `useAssetTree`, etc.)
- Asset list page (table + tree view tabs, filters)
- Asset create/edit forms with Zod validation
- Asset detail page with tabs (details, children, sensors, faults, maintenance)
- Delete with confirmation dialog

### Phase 4: Sensors & Sensor Data
- API hooks for sensors and sensor data
- Sensor CRUD (dialogs within asset detail page)
- Sensor detail page
- Sensor data page: Recharts line chart, latest reading card
- Manual data entry form
- Batch import (JSON paste)
- Delete readings by time range

### Phase 5: Fault Management
- API hooks for faults + fault links
- Fault list page with severity/status filtering
- Fault create/edit forms
- Fault detail page with cause-effect tree visualization
- Link/unlink faults interface (add cause/effect relationships)

### Phase 6: Maintenance Schedules
- API hooks for maintenance
- Schedule list with overdue highlighting + overdue banner
- Schedule create/edit with recurrence selector
- Complete schedule action (generates next occurrence)
- Detect overdue button
- Calendar view

### Phase 7: Documents
- API hooks for documents
- Drag-and-drop file upload
- Document list with metadata
- Delete with confirmation

### Phase 8: Dashboard
- Health check integration (service status cards)
- Metrics cards (total assets, active faults, overdue maintenance, sensors)
- Recent activity feed
- Quick action cards linking to create pages

### Phase 9: AI Query Interface
- Query API hook (mutation)
- Chat-like interface with message list
- Mode selector (auto/vector/graph/hybrid)
- Markdown answer rendering
- Sources panel (document similarity scores)
- Graph sources + Cypher query display
- Token usage stats
- Query history sidebar (Zustand + localStorage)

### Phase 10: Graph Admin & Health
- Sync controls (full/incremental) with status display
- Neo4j database statistics
- Graph info panel
- Dedicated health page with per-service status cards

### Phase 11: Polish
- Responsive design pass
- Loading/error state audit across all pages
- Toast notifications for all mutations
- Dark mode verification

## Backend Gap Note

The faults API only has `GET /api/v1/assets/{asset_id}/faults` (per-asset). For a global `/faults` page, we need to either:
- Add a `GET /api/v1/faults` endpoint on the backend (recommended)
- Work around it client-side by fetching all assets then parallel-fetching faults (current implementation)

The current frontend implementation fetches all assets, then parallel-fetches faults for each asset using the apiClient, and merges them client-side.

## Verification

1. `cd frontend && npm run dev` -- Vite dev server starts on port 5173
2. Navigate to each route, verify pages render with loading states
3. With backend running (`docker compose up`), test:
   - Asset CRUD end-to-end
   - Sensor CRUD within asset detail
   - Sensor data chart + entry
   - Fault CRUD + relationship linking
   - Maintenance schedule creation + completion
   - Document upload + list
   - AI query with mode switching
   - Graph sync triggers
   - Health check display
4. `npm run build` -- production build succeeds with no TypeScript errors
