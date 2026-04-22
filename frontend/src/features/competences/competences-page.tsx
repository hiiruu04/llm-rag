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
import { useCompetences, useDeleteCompetence } from "@/api/competences";
import type { Competence } from "@/types/cmms";

export default function CompetencesPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Competence | null>(null);

  const { data, isLoading, isError, error, refetch } = useCompetences({
    page,
    per_page: 10,
    category: categoryFilter || undefined,
  });

  const deleteMutation = useDeleteCompetence();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (c) => !search || c.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Competences" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Competences" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Competences"
        description="Manage skills and competences"
        actions={
          <Link
            to="/competences/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Competence
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search competences..." />
        <select
          value={categoryFilter}
          onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All categories</option>
          <option value="technical">Technical</option>
          <option value="safety">Safety</option>
          <option value="certification">Certification</option>
          <option value="soft_skill">Soft Skill</option>
        </select>
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<Competence>
          data={filtered}
          keyExtractor={(c) => c.id}
          onRowClick={(c) => navigate(`/competences/${c.id}`)}
          columns={[
            { header: "Name", accessor: "name" },
            { header: "Category", accessor: (c) => c.category ?? "-" },
            { header: "Description", accessor: (c) => c.description ?? "-" },
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
        <EmptyState title="No competences found" description="Create your first competence to get started." action={
          <Link to="/competences/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Competence</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Competence"
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
