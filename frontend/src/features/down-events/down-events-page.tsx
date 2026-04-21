import { useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/common/data-table";
import { PaginationControls } from "@/components/common/pagination";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { EmptyState } from "@/components/common/empty-state";
import { StatusBadge } from "@/components/common/status-badge";
import { SearchInput } from "@/components/common/search-input";
import { FilterBar } from "@/components/common/filter-bar";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useDownEvents, useDeleteDownEvent } from "@/api/down-events";
import type { DownEvent } from "@/types/cmms";

export default function DownEventsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<DownEvent | null>(null);

  const { data, isLoading, isError, error, refetch } = useDownEvents({
    page,
    per_page: 20,
    severity: severityFilter || undefined,
    status: statusFilter || undefined,
  });

  const deleteMutation = useDeleteDownEvent();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (d) => !search || (d.fault_name ?? "").toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Down Events" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Down Events" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Down Events"
        description="Track equipment downtime events"
        actions={
          <Link
            to="/down-events/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Down Event
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search by fault name..." />
        <select
          value={severityFilter}
          onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="resolved">Resolved</option>
        </select>
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<DownEvent>
          data={filtered}
          keyExtractor={(d) => d.id}
          onRowClick={(d) => navigate(`/down-events/${d.id}`)}
          columns={[
            { header: "Fault", accessor: (d) => d.fault_name ?? "-" },
            { header: "Severity", accessor: (d) => <StatusBadge value={d.severity ?? "low"} /> },
            { header: "Status", accessor: (d) => <StatusBadge value={d.status ?? "active"} /> },
            { header: "Started", accessor: (d) => d.started_at ? new Date(d.started_at).toLocaleString() : "-" },
            { header: "Ended", accessor: (d) => d.ended_at ? new Date(d.ended_at).toLocaleString() : "-" },
            { header: "Downtime (mins)", accessor: (d) => d.downtime_minutes?.toString() ?? "-" },
            {
              header: "Actions",
              accessor: (d) => (
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(d); }}
                  className="text-xs text-destructive hover:underline"
                >
                  Delete
                </button>
              ),
            },
          ]}
        />
      ) : (
        <EmptyState title="No down events found" description="Create your first down event to get started." action={
          <Link to="/down-events/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Down Event</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Down Event"
        description={`Are you sure you want to delete this down event? This action cannot be undone.`}
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
