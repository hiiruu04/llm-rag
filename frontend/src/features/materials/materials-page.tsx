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
import { useMaterials, useDeleteMaterial } from "@/api/materials";
import type { Material } from "@/types/cmms";

export default function MaterialsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [partNumberFilter, setPartNumberFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Material | null>(null);

  const { data, isLoading, isError, error, refetch } = useMaterials({
    page,
    per_page: 20,
    part_number: partNumberFilter || undefined,
  });

  const deleteMutation = useDeleteMaterial();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (m) => !search || m.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Materials" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Materials" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Materials"
        description="Manage spare parts and materials inventory"
        actions={
          <Link
            to="/materials/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Material
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search materials..." />
        <input
          value={partNumberFilter}
          onChange={(e) => { setPartNumberFilter(e.target.value); setPage(1); }}
          placeholder="Filter by part number..."
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        />
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<Material>
          data={filtered}
          keyExtractor={(m) => m.id}
          onRowClick={(m) => navigate(`/materials/${m.id}`)}
          columns={[
            { header: "Name", accessor: "name" },
            { header: "Part Number", accessor: (m) => m.part_number ?? "-" },
            { header: "Qty in Stock", accessor: (m) => m.quantity_in_stock?.toString() ?? "0" },
            { header: "Unit", accessor: (m) => m.unit ?? "-" },
            {
              header: "Actions",
              accessor: (m) => (
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(m); }}
                  className="text-xs text-destructive hover:underline"
                >
                  Delete
                </button>
              ),
            },
          ]}
        />
      ) : (
        <EmptyState title="No materials found" description="Create your first material to get started." action={
          <Link to="/materials/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Material</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Material"
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
