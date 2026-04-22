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
import { useLocations, useDeleteLocation } from "@/api/locations";
import type { Location } from "@/types/cmms";

export default function LocationsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Location | null>(null);

  const { data, isLoading, isError, error, refetch } = useLocations({
    page,
    per_page: 10,
  });

  const deleteMutation = useDeleteLocation();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (l) => !search || l.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Locations" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Locations" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Locations"
        description="Manage locations and areas"
        actions={
          <Link
            to="/locations/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Location
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search locations..." />
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <>
          <DataTable<Location>
            data={filtered}
            keyExtractor={(l) => l.id}
            onRowClick={(l) => navigate(`/locations/${l.id}`)}
            columns={[
              { header: "Name", accessor: "name" },
              { header: "Type", accessor: (l) => l.location_type ?? "-" },
              { header: "Description", accessor: (l) => l.description ?? "-" },
              {
                header: "Actions",
                accessor: (l) => (
                  <button
                    onClick={(e) => { e.stopPropagation(); setDeleteTarget(l); }}
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
        <EmptyState title="No locations found" description="Create your first location to get started." action={
          <Link to="/locations/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Location</Link>
        } />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Location"
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
