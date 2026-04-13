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
import { useCauses, useDeleteCause } from "@/api/causes";
import type { Cause } from "@/types/cmms";

export default function CausesPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Cause | null>(null);

  const { data, isLoading, isError, error, refetch } = useCauses({
    page,
    per_page: 20,
    severity: severityFilter || undefined,
    category: categoryFilter || undefined,
  });

  const deleteMutation = useDeleteCause();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (c) => !search || c.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Causes" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Causes" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Causes"
        description="Manage failure and incident causes"
        actions={
          <Link
            to="/causes/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Cause
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search causes..." />
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
          value={categoryFilter}
          onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All categories</option>
          <option value="mechanical">Mechanical</option>
          <option value="electrical">Electrical</option>
          <option value="operational">Operational</option>
          <option value="environmental">Environmental</option>
          <option value="human">Human</option>
        </select>
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<Cause>
          data={filtered}
          keyExtractor={(c) => c.id}
          onRowClick={(c) => navigate(`/causes/${c.id}`)}
          columns={[
            { header: "Name", accessor: "name" },
            { header: "Category", accessor: (c) => c.category ?? "-" },
            { header: "Severity", accessor: (c) => <StatusBadge value={c.severity ?? "low"} /> },
            {
              header: "Actions",
              accessor: (c) => (
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(c); }}
                  className="text-xs text-destructive hover:underline"
                >
                  Delete
                </button>
              ),
            },
          ]}
        />
      ) : (
        <EmptyState title="No causes found" description="Create your first cause to get started." action={
          <Link to="/causes/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Cause</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Cause"
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
