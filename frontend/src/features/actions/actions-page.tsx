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
import { useActions, useDeleteAction } from "@/api/actions";
import type { Action } from "@/types/cmms";

export default function ActionsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [actionTypeFilter, setActionTypeFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Action | null>(null);

  const { data, isLoading, isError, error, refetch } = useActions({
    page,
    per_page: 20,
    action_type: actionTypeFilter || undefined,
  });

  const deleteMutation = useDeleteAction();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (a) => !search || a.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Actions" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Actions" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Actions"
        description="Manage task actions and procedures"
        actions={
          <Link
            to="/actions/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Action
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search actions..." />
        <select
          value={actionTypeFilter}
          onChange={(e) => { setActionTypeFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All types</option>
          <option value="check">Check</option>
          <option value="measure">Measure</option>
          <option value="replace">Replace</option>
          <option value="adjust">Adjust</option>
          <option value="clean">Clean</option>
          <option value="inspect">Inspect</option>
          <option value="test">Test</option>
        </select>
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <>
          <DataTable<Action>
            data={filtered}
            keyExtractor={(a) => a.id}
            onRowClick={(a) => navigate(`/actions/${a.id}`)}
            columns={[
              { header: "Name", accessor: "name" },
              { header: "Type", accessor: (a) => a.action_type ?? "-" },
              { header: "Sequence Order", accessor: (a) => a.sequence_order ?? "-" },
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
          <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />
        </>
      ) : (
        <EmptyState title="No actions found" description="Create your first action to get started." action={
          <Link to="/actions/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Action</Link>
        } />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Action"
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
