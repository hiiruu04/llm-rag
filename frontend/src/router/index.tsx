/* eslint-disable react-refresh/only-export-components */
import { Route } from "react-router-dom";
import { lazy, Suspense } from "react";

const DashboardPage = lazy(() => import("@/features/dashboard/dashboard-page"));
const AssetsPage = lazy(() => import("@/features/assets/assets-page"));
const AssetCreatePage = lazy(() => import("@/features/assets/asset-create-page"));
const AssetDetailPage = lazy(() => import("@/features/assets/asset-detail-page"));
const AssetEditPage = lazy(() => import("@/features/assets/asset-edit-page"));
const SensorDetailPage = lazy(() => import("@/features/sensors/sensor-detail-page"));
const SensorDataPage = lazy(() => import("@/features/sensor-data/sensor-data-page"));
const FaultsPage = lazy(() => import("@/features/faults/faults-page"));
const FaultDetailPage = lazy(() => import("@/features/faults/fault-detail-page"));
const FaultCreatePage = lazy(() => import("@/features/faults/fault-create-page"));
const FaultEditPage = lazy(() => import("@/features/faults/fault-edit-page"));
const MaintenancePage = lazy(() => import("@/features/maintenance/maintenance-page"));
const ScheduleCreatePage = lazy(() => import("@/features/maintenance/schedule-create-page"));
const ScheduleDetailPage = lazy(() => import("@/features/maintenance/schedule-detail-page"));
const ScheduleEditPage = lazy(() => import("@/features/maintenance/schedule-edit-page"));
const DocumentsPage = lazy(() => import("@/features/documents/documents-page"));
const QueryPage = lazy(() => import("@/features/query/query-page"));
const GraphAdminPage = lazy(() => import("@/features/graph-admin/graph-admin-page"));
const HealthPage = lazy(() => import("@/features/health/health-page"));
const WorkersPage = lazy(() => import("@/features/workers/workers-page"));
const WorkerDetailPage = lazy(() => import("@/features/workers/worker-detail-page"));
const WorkerCreatePage = lazy(() => import("@/features/workers/worker-create-page"));
const WorkerEditPage = lazy(() => import("@/features/workers/worker-edit-page"));
const RolesPage = lazy(() => import("@/features/roles/roles-page"));
const RoleDetailPage = lazy(() => import("@/features/roles/role-detail-page"));
const RoleCreatePage = lazy(() => import("@/features/roles/role-create-page"));
const RoleEditPage = lazy(() => import("@/features/roles/role-edit-page"));
const CompetencesPage = lazy(() => import("@/features/competences/competences-page"));
const CompetenceDetailPage = lazy(() => import("@/features/competences/competence-detail-page"));
const CompetenceCreatePage = lazy(() => import("@/features/competences/competence-create-page"));
const CompetenceEditPage = lazy(() => import("@/features/competences/competence-edit-page"));
const LevelsPage = lazy(() => import("@/features/levels/levels-page"));
const LevelDetailPage = lazy(() => import("@/features/levels/level-detail-page"));
const LevelCreatePage = lazy(() => import("@/features/levels/level-create-page"));
const LevelEditPage = lazy(() => import("@/features/levels/level-edit-page"));
const TasksPage = lazy(() => import("@/features/tasks/tasks-page"));
const TaskDetailPage = lazy(() => import("@/features/tasks/task-detail-page"));
const TaskCreatePage = lazy(() => import("@/features/tasks/task-create-page"));
const TaskEditPage = lazy(() => import("@/features/tasks/task-edit-page"));
const CausesPage = lazy(() => import("@/features/causes/causes-page"));
const CauseDetailPage = lazy(() => import("@/features/causes/cause-detail-page"));
const CauseCreatePage = lazy(() => import("@/features/causes/cause-create-page"));
const CauseEditPage = lazy(() => import("@/features/causes/cause-edit-page"));
const MaterialsPage = lazy(() => import("@/features/materials/materials-page"));
const MaterialDetailPage = lazy(() => import("@/features/materials/material-detail-page"));
const MaterialCreatePage = lazy(() => import("@/features/materials/material-create-page"));
const MaterialEditPage = lazy(() => import("@/features/materials/material-edit-page"));
const ShiftsPage = lazy(() => import("@/features/shifts/shifts-page"));
const ShiftDetailPage = lazy(() => import("@/features/shifts/shift-detail-page"));
const ShiftCreatePage = lazy(() => import("@/features/shifts/shift-create-page"));
const ShiftEditPage = lazy(() => import("@/features/shifts/shift-edit-page"));
const DownEventsPage = lazy(() => import("@/features/down-events/down-events-page"));
const DownEventDetailPage = lazy(() => import("@/features/down-events/down-event-detail-page"));
const DownEventCreatePage = lazy(() => import("@/features/down-events/down-event-create-page"));
const DownEventEditPage = lazy(() => import("@/features/down-events/down-event-edit-page"));
const OrdersPage = lazy(() => import("@/features/orders/orders-page"));
const OrderDetailPage = lazy(() => import("@/features/orders/order-detail-page"));
const OrderCreatePage = lazy(() => import("@/features/orders/order-create-page"));
const OrderEditPage = lazy(() => import("@/features/orders/order-edit-page"));
const LocationsPage = lazy(() => import("@/features/locations/locations-page"));
const LocationDetailPage = lazy(() => import("@/features/locations/location-detail-page"));
const LocationCreatePage = lazy(() => import("@/features/locations/location-create-page"));
const LocationEditPage = lazy(() => import("@/features/locations/location-edit-page"));
const SystemsPage = lazy(() => import("@/features/systems/systems-page"));
const SystemDetailPage = lazy(() => import("@/features/systems/system-detail-page"));
const SystemCreatePage = lazy(() => import("@/features/systems/system-create-page"));
const SystemEditPage = lazy(() => import("@/features/systems/system-edit-page"));
const AggregatesPage = lazy(() => import("@/features/aggregates/aggregates-page"));
const AggregateDetailPage = lazy(() => import("@/features/aggregates/aggregate-detail-page"));
const AggregateCreatePage = lazy(() => import("@/features/aggregates/aggregate-create-page"));
const AggregateEditPage = lazy(() => import("@/features/aggregates/aggregate-edit-page"));

function PageSuspense({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="flex h-[50vh] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        </div>
      }
    >
      {children}
    </Suspense>
  );
}

export const router = (
  <>
    <Route path="/" element={<PageSuspense><DashboardPage /></PageSuspense>} />
    <Route path="/assets" element={<PageSuspense><AssetsPage /></PageSuspense>} />
    <Route path="/assets/new" element={<PageSuspense><AssetCreatePage /></PageSuspense>} />
    <Route path="/assets/:id" element={<PageSuspense><AssetDetailPage /></PageSuspense>} />
    <Route path="/assets/:id/edit" element={<PageSuspense><AssetEditPage /></PageSuspense>} />
    <Route path="/sensors/:id" element={<PageSuspense><SensorDetailPage /></PageSuspense>} />
    <Route path="/sensors/:id/data" element={<PageSuspense><SensorDataPage /></PageSuspense>} />
    <Route path="/faults" element={<PageSuspense><FaultsPage /></PageSuspense>} />
    <Route path="/faults/:id" element={<PageSuspense><FaultDetailPage /></PageSuspense>} />
    <Route path="/assets/:assetId/faults/new" element={<PageSuspense><FaultCreatePage /></PageSuspense>} />
    <Route path="/faults/:id/edit" element={<PageSuspense><FaultEditPage /></PageSuspense>} />
    <Route path="/maintenance" element={<PageSuspense><MaintenancePage /></PageSuspense>} />
    <Route path="/maintenance/:id" element={<PageSuspense><ScheduleDetailPage /></PageSuspense>} />
    <Route path="/assets/:assetId/maintenance/new" element={<PageSuspense><ScheduleCreatePage /></PageSuspense>} />
    <Route path="/maintenance/:id/edit" element={<PageSuspense><ScheduleEditPage /></PageSuspense>} />
    <Route path="/documents" element={<PageSuspense><DocumentsPage /></PageSuspense>} />
    <Route path="/query" element={<PageSuspense><QueryPage /></PageSuspense>} />
    <Route path="/admin/graph" element={<PageSuspense><GraphAdminPage /></PageSuspense>} />
    <Route path="/health" element={<PageSuspense><HealthPage /></PageSuspense>} />
    {/* Workers */}
    <Route path="/workers" element={<PageSuspense><WorkersPage /></PageSuspense>} />
    <Route path="/workers/new" element={<PageSuspense><WorkerCreatePage /></PageSuspense>} />
    <Route path="/workers/:id" element={<PageSuspense><WorkerDetailPage /></PageSuspense>} />
    <Route path="/workers/:id/edit" element={<PageSuspense><WorkerEditPage /></PageSuspense>} />
    {/* Roles */}
    <Route path="/roles" element={<PageSuspense><RolesPage /></PageSuspense>} />
    <Route path="/roles/new" element={<PageSuspense><RoleCreatePage /></PageSuspense>} />
    <Route path="/roles/:id" element={<PageSuspense><RoleDetailPage /></PageSuspense>} />
    <Route path="/roles/:id/edit" element={<PageSuspense><RoleEditPage /></PageSuspense>} />
    {/* Competences */}
    <Route path="/competences" element={<PageSuspense><CompetencesPage /></PageSuspense>} />
    <Route path="/competences/new" element={<PageSuspense><CompetenceCreatePage /></PageSuspense>} />
    <Route path="/competences/:id" element={<PageSuspense><CompetenceDetailPage /></PageSuspense>} />
    <Route path="/competences/:id/edit" element={<PageSuspense><CompetenceEditPage /></PageSuspense>} />
    {/* Levels */}
    <Route path="/levels" element={<PageSuspense><LevelsPage /></PageSuspense>} />
    <Route path="/levels/new" element={<PageSuspense><LevelCreatePage /></PageSuspense>} />
    <Route path="/levels/:id" element={<PageSuspense><LevelDetailPage /></PageSuspense>} />
    <Route path="/levels/:id/edit" element={<PageSuspense><LevelEditPage /></PageSuspense>} />
    {/* Tasks */}
    <Route path="/tasks" element={<PageSuspense><TasksPage /></PageSuspense>} />
    <Route path="/tasks/new" element={<PageSuspense><TaskCreatePage /></PageSuspense>} />
    <Route path="/tasks/:id" element={<PageSuspense><TaskDetailPage /></PageSuspense>} />
    <Route path="/tasks/:id/edit" element={<PageSuspense><TaskEditPage /></PageSuspense>} />
    {/* Causes */}
    <Route path="/causes" element={<PageSuspense><CausesPage /></PageSuspense>} />
    <Route path="/causes/new" element={<PageSuspense><CauseCreatePage /></PageSuspense>} />
    <Route path="/causes/:id" element={<PageSuspense><CauseDetailPage /></PageSuspense>} />
    <Route path="/causes/:id/edit" element={<PageSuspense><CauseEditPage /></PageSuspense>} />
    {/* Materials */}
    <Route path="/materials" element={<PageSuspense><MaterialsPage /></PageSuspense>} />
    <Route path="/materials/new" element={<PageSuspense><MaterialCreatePage /></PageSuspense>} />
    <Route path="/materials/:id" element={<PageSuspense><MaterialDetailPage /></PageSuspense>} />
    <Route path="/materials/:id/edit" element={<PageSuspense><MaterialEditPage /></PageSuspense>} />
    {/* Shifts */}
    <Route path="/shifts" element={<PageSuspense><ShiftsPage /></PageSuspense>} />
    <Route path="/shifts/new" element={<PageSuspense><ShiftCreatePage /></PageSuspense>} />
    <Route path="/shifts/:id" element={<PageSuspense><ShiftDetailPage /></PageSuspense>} />
    <Route path="/shifts/:id/edit" element={<PageSuspense><ShiftEditPage /></PageSuspense>} />
    {/* Down Events */}
    <Route path="/down-events" element={<PageSuspense><DownEventsPage /></PageSuspense>} />
    <Route path="/down-events/new" element={<PageSuspense><DownEventCreatePage /></PageSuspense>} />
    <Route path="/down-events/:id" element={<PageSuspense><DownEventDetailPage /></PageSuspense>} />
    <Route path="/down-events/:id/edit" element={<PageSuspense><DownEventEditPage /></PageSuspense>} />
    {/* Orders */}
    <Route path="/orders" element={<PageSuspense><OrdersPage /></PageSuspense>} />
    <Route path="/orders/new" element={<PageSuspense><OrderCreatePage /></PageSuspense>} />
    <Route path="/orders/:id" element={<PageSuspense><OrderDetailPage /></PageSuspense>} />
    <Route path="/orders/:id/edit" element={<PageSuspense><OrderEditPage /></PageSuspense>} />
    {/* Locations */}
    <Route path="/locations" element={<PageSuspense><LocationsPage /></PageSuspense>} />
    <Route path="/locations/new" element={<PageSuspense><LocationCreatePage /></PageSuspense>} />
    <Route path="/locations/:id" element={<PageSuspense><LocationDetailPage /></PageSuspense>} />
    <Route path="/locations/:id/edit" element={<PageSuspense><LocationEditPage /></PageSuspense>} />
    {/* Systems */}
    <Route path="/systems" element={<PageSuspense><SystemsPage /></PageSuspense>} />
    <Route path="/systems/new" element={<PageSuspense><SystemCreatePage /></PageSuspense>} />
    <Route path="/systems/:id" element={<PageSuspense><SystemDetailPage /></PageSuspense>} />
    <Route path="/systems/:id/edit" element={<PageSuspense><SystemEditPage /></PageSuspense>} />
    {/* Aggregates */}
    <Route path="/aggregates" element={<PageSuspense><AggregatesPage /></PageSuspense>} />
    <Route path="/aggregates/new" element={<PageSuspense><AggregateCreatePage /></PageSuspense>} />
    <Route path="/aggregates/:id" element={<PageSuspense><AggregateDetailPage /></PageSuspense>} />
    <Route path="/aggregates/:id/edit" element={<PageSuspense><AggregateEditPage /></PageSuspense>} />
  </>
);
