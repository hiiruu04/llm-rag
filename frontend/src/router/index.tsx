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
const ScheduleEditPage = lazy(() => import("@/features/maintenance/schedule-edit-page"));
const DocumentsPage = lazy(() => import("@/features/documents/documents-page"));
const QueryPage = lazy(() => import("@/features/query/query-page"));
const GraphAdminPage = lazy(() => import("@/features/graph-admin/graph-admin-page"));
const HealthPage = lazy(() => import("@/features/health/health-page"));

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
    <Route path="/assets/:assetId/maintenance/new" element={<PageSuspense><ScheduleCreatePage /></PageSuspense>} />
    <Route path="/maintenance/:id/edit" element={<PageSuspense><ScheduleEditPage /></PageSuspense>} />
    <Route path="/documents" element={<PageSuspense><DocumentsPage /></PageSuspense>} />
    <Route path="/query" element={<PageSuspense><QueryPage /></PageSuspense>} />
    <Route path="/admin/graph" element={<PageSuspense><GraphAdminPage /></PageSuspense>} />
    <Route path="/health" element={<PageSuspense><HealthPage /></PageSuspense>} />
  </>
);
