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
import { useSystems, useDeleteSystem } from "@/api/systems";
import type { System } from "@/types/cmms";

export default function SystemsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<System | null>(null);

  const { data, isLoading, isError, error, refetch } = useSystems({
    page,
    per_page: 20,
  });

  const deleteMutation = useDeleteSystem();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (s) => !search || s.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Systems" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Systems" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Systems"
        description="Manage your systems"
        actions={
          <Link
            to="/systems/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New System
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search systems..." />
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<System>
          data={filtered}
          keyExtractor={(s) => s.id}
          onRowClick={(s) => navigate(`/systems/${s.id}`)}
          columns={[
            { header: "Name", accessor: "name" },
            { header: "Description", accessor: (s) => s.description ?? "-" },
            {
              header: "Actions",
              accessor: (s) => (
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(s); }}
                  className="text-xs text-destructive hover:underline"
                >
                  Delete
                </button>
              ),
            },
          ]}
        />
      ) : (
        <EmptyState title="No systems found" description="Create your first system to get started." action={
          <Link to="/systems/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create System</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete System"
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
