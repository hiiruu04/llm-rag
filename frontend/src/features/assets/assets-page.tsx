import { useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Plus, TreePine, List } from "lucide-react";
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
import { useAssets, useAssetTree, useDeleteAsset } from "@/api/assets";
import type { Asset, AssetTreeNode } from "@/types/asset";

export default function AssetsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [view, setView] = useState<"table" | "tree">("table");
  const [deleteTarget, setDeleteTarget] = useState<Asset | null>(null);

  const { data, isLoading, isError, error, refetch } = useAssets({
    page,
    per_page: 10,
    status: statusFilter || undefined,
  });

  const { data: tree } = useAssetTree();
  const deleteMutation = useDeleteAsset();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (a) => !search || a.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Assets" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Assets" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Assets"
        description="Manage your equipment and facilities"
        actions={
          <Link
            to="/assets/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Asset
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search assets..." />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="maintenance">Maintenance</option>
          <option value="decommissioned">Decommissioned</option>
        </select>
        <div className="ml-auto flex gap-1 rounded-md border border-border p-0.5">
          <button
            onClick={() => setView("table")}
            className={`flex items-center gap-1 rounded px-2 py-1 text-xs ${view === "table" ? "bg-accent" : ""}`}
          >
            <List className="h-3.5 w-3.5" /> Table
          </button>
          <button
            onClick={() => setView("tree")}
            className={`flex items-center gap-1 rounded px-2 py-1 text-xs ${view === "tree" ? "bg-accent" : ""}`}
          >
            <TreePine className="h-3.5 w-3.5" /> Tree
          </button>
        </div>
      </FilterBar>

      {view === "table" ? (
        <>
          {filtered && filtered.length > 0 ? (
            <DataTable<Asset>
              data={filtered}
              keyExtractor={(a) => a.id}
              onRowClick={(a) => navigate(`/assets/${a.id}`)}
              columns={[
                { header: "Name", accessor: "name" },
                { header: "Type", accessor: "asset_type" },
                { header: "Status", accessor: (a) => <StatusBadge value={a.status} /> },
                { header: "Location", accessor: (a) => a.location ?? "-" },
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
            <EmptyState title="No assets found" description="Create your first asset to get started." action={
              <Link to="/assets/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Asset</Link>
            } />
          )}
          <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />
        </>
      ) : (
        <div className="rounded-lg border border-border p-4">
          {tree && tree.length > 0 ? (
            tree.map((node) => <TreeNode key={node.id} node={node} />)
          ) : (
            <EmptyState title="No assets in tree" />
          )}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Asset"
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

function TreeNode({ node, depth = 0 }: { node: AssetTreeNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 1);
  return (
    <div style={{ paddingLeft: depth * 20 }}>
      <div
        className="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-muted/50"
        onClick={() => setExpanded(!expanded)}
      >
        {node.children.length > 0 ? (
          <span className="text-xs text-muted-foreground">{expanded ? "▼" : "▶"}</span>
        ) : (
          <span className="w-3" />
        )}
        <Link to={`/assets/${node.id}`} className="text-sm hover:underline" onClick={(e) => e.stopPropagation()}>
          {node.name}
        </Link>
        <span className="text-xs text-muted-foreground">{node.asset_type}</span>
        <StatusBadge value={node.status} />
      </div>
      {expanded && node.children.map((child) => <TreeNode key={child.id} node={child} depth={depth + 1} />)}
    </div>
  );
}
