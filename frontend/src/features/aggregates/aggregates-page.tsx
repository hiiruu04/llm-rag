import { useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/common/data-table";
import { PaginationControls } from "@/components/common/pagination";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { EmptyState } from "@/components/common/empty-state";
import { SearchInput } from "@/components/common/search-input";
import { FilterBar } from "@/components/common/filter-bar";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useAggregates, useDeleteAggregate } from "@/api/aggregates";
import type { Aggregate } from "@/types/cmms";

export default function AggregatesPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Aggregate | null>(null);

  const { data, isLoading, isError, error, refetch } = useAggregates({
    page,
    per_page: 10,
  });

  const deleteMutation = useDeleteAggregate();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (a) => !search || a.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Aggregates" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Aggregates" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Aggregates"
        description="Manage your aggregates"
        actions={
          <Link
            to="/aggregates/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Aggregate
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search aggregates..." />
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<Aggregate>
          data={filtered}
          keyExtractor={(a) => a.id}
          onRowClick={(a) => navigate(`/aggregates/${a.id}`)}
          columns={[
            { header: "Name", accessor: "name" },
            { header: "Description", accessor: (a) => a.description ?? "-" },
            {
              header: "Actions",
              accessor: (a) => (
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(a); }}
                  className="text-xs text-destructive hover:underline"
                >
                  Delete
                </button>
              ),
            },
          ]}
        />
      ) : (
        <EmptyState title="No aggregates found" description="Create your first aggregate to get started." action={
          <Link to="/aggregates/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Aggregate</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Aggregate"
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
