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
import { useShifts, useDeleteShift } from "@/api/shifts";
import type { Shift } from "@/types/cmms";

export default function ShiftsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Shift | null>(null);

  const { data, isLoading, isError, error, refetch } = useShifts({
    page,
    per_page: 20,
  });

  const deleteMutation = useDeleteShift();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (s) => !search || s.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Shifts" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Shifts" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Shifts"
        description="Manage work shifts and schedules"
        actions={
          <Link
            to="/shifts/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Shift
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search shifts..." />
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<Shift>
          data={filtered}
          keyExtractor={(s) => s.id}
          onRowClick={(s) => navigate(`/shifts/${s.id}`)}
          columns={[
            { header: "Name", accessor: "name" },
            { header: "Start Time", accessor: (s) => s.start_time ?? "-" },
            { header: "End Time", accessor: (s) => s.end_time ?? "-" },
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
        <EmptyState title="No shifts found" description="Create your first shift to get started." action={
          <Link to="/shifts/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Shift</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Shift"
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
