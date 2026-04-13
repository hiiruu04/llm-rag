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
import { useOrders, useDeleteOrder } from "@/api/orders";
import type { Order } from "@/types/cmms";

export default function OrdersPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [orderTypeFilter, setOrderTypeFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Order | null>(null);

  const { data, isLoading, isError, error, refetch } = useOrders({
    page,
    per_page: 20,
    status: statusFilter || undefined,
    order_type: orderTypeFilter || undefined,
    priority: priorityFilter || undefined,
  });

  const deleteMutation = useDeleteOrder();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (o) => !search || o.title.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Orders" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Orders" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Orders"
        description="Manage work orders and requests"
        actions={
          <Link
            to="/orders/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Order
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search by title..." />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          value={orderTypeFilter}
          onChange={(e) => { setOrderTypeFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All types</option>
          <option value="maintenance">Maintenance</option>
          <option value="repair">Repair</option>
          <option value="inspection">Inspection</option>
          <option value="installation">Installation</option>
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All priorities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <DataTable<Order>
          data={filtered}
          keyExtractor={(o) => o.id}
          onRowClick={(o) => navigate(`/orders/${o.id}`)}
          columns={[
            { header: "Order #", accessor: (o) => o.order_number ?? "-" },
            { header: "Title", accessor: "title" },
            { header: "Type", accessor: (o) => o.order_type ?? "-" },
            { header: "Status", accessor: (o) => <StatusBadge value={o.status ?? "open"} /> },
            { header: "Priority", accessor: (o) => <StatusBadge value={o.priority ?? "low"} /> },
            {
              header: "Actions",
              accessor: (o) => (
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(o); }}
                  className="text-xs text-destructive hover:underline"
                >
                  Delete
                </button>
              ),
            },
          ]}
        />
      ) : (
        <EmptyState title="No orders found" description="Create your first order to get started." action={
          <Link to="/orders/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Order</Link>
        } />
      )}
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Order"
        description={`Are you sure you want to delete "${deleteTarget?.title}"? This action cannot be undone.`}
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
