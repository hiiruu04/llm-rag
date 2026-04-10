import { RefreshCw, ArrowRightLeft } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useSyncStatus, useGraphInfo, useFullSync, useIncrementalSync } from "@/api/graph";

export default function GraphAdminPage() {
  const { data: status, isLoading: statusLoading, refetch: refetchStatus } = useSyncStatus();
  const { data: info, isLoading: infoLoading } = useGraphInfo();
  const fullSync = useFullSync();
  const incrementalSync = useIncrementalSync();

  const isLoading = statusLoading || infoLoading;

  return (
    <>
      <PageHeader title="Graph Admin" description="Neo4j graph database management" />

      {/* Sync Controls */}
      <div className="mb-6 rounded-lg border border-border p-4">
        <h2 className="mb-4 text-sm font-semibold">Sync Controls</h2>
        <div className="flex gap-3">
          <button
            onClick={() => fullSync.mutate(undefined, { onSuccess: () => refetchStatus() })}
            disabled={fullSync.isPending || status?.sync_in_progress}
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${fullSync.isPending ? "animate-spin" : ""}`} />
            Full Sync
          </button>
          <button
            onClick={() => incrementalSync.mutate(undefined, { onSuccess: () => refetchStatus() })}
            disabled={incrementalSync.isPending || status?.sync_in_progress}
            className="flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm hover:bg-accent disabled:opacity-50"
          >
            <ArrowRightLeft className={`h-4 w-4 ${incrementalSync.isPending ? "animate-spin" : ""}`} />
            Incremental Sync
          </button>
        </div>
        {(fullSync.isError || incrementalSync.isError) && (
          <p className="mt-2 text-sm text-destructive">{fullSync.error?.message || incrementalSync.error?.message}</p>
        )}
        {(fullSync.isSuccess || incrementalSync.isSuccess) && (
          <p className="mt-2 text-sm text-green-600">Sync completed successfully</p>
        )}
      </div>

      {/* Sync Status */}
      <div className="mb-6 rounded-lg border border-border p-4">
        <h2 className="mb-4 text-sm font-semibold">Sync Status</h2>
        {isLoading ? (
          <LoadingState rows={2} />
        ) : status ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Synced" value={status.synced ? "Yes" : "No"} />
            <StatCard label="In Progress" value={status.sync_in_progress ? "Yes" : "No"} />
            <StatCard label="Last Full Sync" value={status.last_full_sync ? format(new Date(status.last_full_sync), "PPpp") : "Never"} />
            <StatCard label="Last Incremental" value={status.last_incremental_sync ? format(new Date(status.last_incremental_sync), "PPpp") : "Never"} />
          </div>
        ) : (
          <ErrorState message="Unable to fetch sync status" />
        )}
      </div>

      {/* Graph Info */}
      <div className="rounded-lg border border-border p-4">
        <h2 className="mb-4 text-sm font-semibold">Graph Database Statistics</h2>
        {isLoading ? (
          <LoadingState rows={2} />
        ) : info ? (
          <>
            <div className="mb-4 flex items-center gap-2">
              <div className={`h-2.5 w-2.5 rounded-full ${info.connected ? "bg-green-500" : "bg-red-500"}`} />
              <span className="text-sm">{info.connected ? "Connected" : "Disconnected"}</span>
              {info.error && <span className="text-xs text-destructive">({info.error})</span>}
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <StatCard label="Assets" value={info.total_assets ?? 0} />
              <StatCard label="Sensors" value={info.total_sensors ?? 0} />
              <StatCard label="Faults" value={info.total_faults ?? 0} />
              <StatCard label="Schedules" value={info.total_maintenanceschedules ?? 0} />
              <StatCard label="Summaries" value={info.total_sensorsummaries ?? 0} />
            </div>
          </>
        ) : (
          <ErrorState message="Unable to fetch graph info" />
        )}
      </div>
    </>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md bg-muted/50 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </div>
  );
}
