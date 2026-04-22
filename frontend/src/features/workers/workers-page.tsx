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
import { useWorkers, useDeleteWorker } from "@/api/workers";
import type { Worker } from "@/types/cmms";

export default function WorkersPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Worker | null>(null);

  const { data, isLoading, isError, error, refetch } = useWorkers({
    page,
    per_page: 10,
    status: statusFilter || undefined,
  });

  const deleteMutation = useDeleteWorker();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (w) => !search || w.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Workers" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Workers" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Workers"
        description="Manage your workforce"
        actions={
          <Link
            to="/workers/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Worker
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search workers..." />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="on_leave">On Leave</option>
        </select>
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<Worker>
          data={filtered}
          keyExtractor={(w) => w.id}
          onRowClick={(w) => navigate(`/workers/${w.id}`)}
          columns={[
            { header: "Name", accessor: "name" },
            { header: "Employee ID", accessor: "employee_id" },
            { header: "Email", accessor: (w) => w.email ?? "-" },
            { header: "Status", accessor: (w) => <StatusBadge value={w.status} /> },
            {
              header: "Actions",
              accessor: (w) => (
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(w); }}
                  className="text-xs text-destructive hover:underline"
                >
                  Delete
                </button>
              ),
            },
          ]}
        />
      ) : (
        <EmptyState title="No workers found" description="Create your first worker to get started." action={
          <Link to="/workers/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Worker</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Worker"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
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
