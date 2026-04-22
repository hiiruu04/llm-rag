import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { format } from "date-fns";
import { AlertTriangle, CheckCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/common/data-table";
import { PaginationControls } from "@/components/common/pagination";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { FilterBar } from "@/components/common/filter-bar";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useMaintenanceSchedules, useOverdueSchedules, useDeleteSchedule, useCompleteSchedule, useDetectOverdue } from "@/api/maintenance";
import type { MaintenanceSchedule } from "@/types/maintenance";

export default function MaintenancePage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [completeTarget, setCompleteTarget] = useState<MaintenanceSchedule | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<MaintenanceSchedule | null>(null);

  const { data, isLoading, isError, error, refetch } = useMaintenanceSchedules({
    page,
    per_page: 10,
    status: statusFilter || undefined,
    maintenance_type: typeFilter || undefined,
  });
  const { data: overdue } = useOverdueSchedules({ per_page: 5 });
  const deleteMutation = useDeleteSchedule();
  const completeMutation = useCompleteSchedule();
  const detectOverdue = useDetectOverdue();

  if (isLoading) return <><PageHeader title="Maintenance" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Maintenance" /><ErrorState message={error?.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Maintenance"
        description="Manage maintenance schedules"
        actions={
          <div className="flex gap-2">
            <button onClick={() => detectOverdue.mutate()} className="rounded-md border border-border px-3 py-2 text-sm hover:bg-accent">
              Detect Overdue
            </button>
          </div>
        }
      />

      {overdue && overdue.data.length > 0 && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3">
          <AlertTriangle className="h-4 w-4 text-destructive" />
          <span className="text-sm font-medium text-destructive">
            {overdue.data.length} overdue schedule{overdue.data.length > 1 ? "s" : ""}
          </span>
        </div>
      )}

      <FilterBar>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
          <option value="">All statuses</option>
          <option value="scheduled">Scheduled</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="overdue">Overdue</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
          <option value="">All types</option>
          <option value="preventive">Preventive</option>
          <option value="corrective">Corrective</option>
          <option value="predictive">Predictive</option>
        </select>
      </FilterBar>

      <DataTable<MaintenanceSchedule>
        data={data?.data ?? []}
        keyExtractor={(s) => s.id}
        onRowClick={(s) => navigate(`/maintenance/${s.id}`)}
        columns={[
          { header: "Title", accessor: "title" },
          { header: "Type", accessor: (s) => <StatusBadge value={s.maintenance_type} /> },
          { header: "Priority", accessor: (s) => <StatusBadge value={s.priority} /> },
          { header: "Status", accessor: (s) => <StatusBadge value={s.status} /> },
          { header: "Scheduled", accessor: (s) => s.scheduled_date ? format(new Date(s.scheduled_date), "PP") : "-" },
          {
            header: "Actions",
            accessor: (s) => (
              <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                {s.status !== "completed" && (
                  <button onClick={() => setCompleteTarget(s)} className="flex items-center gap-1 text-xs text-primary hover:underline">
                    <CheckCircle className="h-3.5 w-3.5" /> Complete
                  </button>
                )}
                <button onClick={() => setDeleteTarget(s)} className="text-xs text-destructive hover:underline">Delete</button>
              </div>
            ),
          },
        ]}
      />
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!completeTarget}
        title="Complete Schedule"
        description={`Mark "${completeTarget?.title}" as completed?`}
        confirmLabel="Complete"
        onConfirm={() => {
          if (completeTarget) completeMutation.mutate(completeTarget.id);
          setCompleteTarget(null);
        }}
        onCancel={() => setCompleteTarget(null)}
      />
      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Schedule"
        description={`Delete "${deleteTarget?.title}"?`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={() => {
          if (deleteTarget) deleteMutation.mutate(deleteTarget.id);
          setDeleteTarget(null);
        }}
        onCancel={() => setDeleteTarget(null)}
      />
    </>
  );
}
