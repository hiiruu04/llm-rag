import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useOrder, useDeleteOrder } from "@/api/orders";

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: order, isLoading, isError, error, refetch } = useOrder(id!);
  const deleteMutation = useDeleteOrder();

  if (isLoading) return <LoadingState />;
  if (isError || !order) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(order.id);
    setDeleteOpen(false);
    navigate("/orders");
  };

  return (
    <>
      <PageHeader
        title={order.title}
        description={`Order ${order.order_number ?? id}`}
        actions={
          <div className="flex gap-2">
            <Link to={`/orders/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <DetailCard label="Order Number" value={order.order_number ?? "-"} />
        <DetailCard label="Title" value={order.title} />
        <DetailCard label="Description" value={order.description ?? "-"} />
        <DetailCard label="Type" value={order.order_type ?? "-"} />
        <DetailCard label="Status" value={<StatusBadge value={order.status ?? "open"} />} />
        <DetailCard label="Priority" value={<StatusBadge value={order.priority ?? "low"} />} />
        <DetailCard label="Requested Date" value={order.requested_date ? format(new Date(order.requested_date), "PPpp") : "-"} />
        <DetailCard label="Created" value={order.created_at ? format(new Date(order.created_at), "PPpp") : "-"} />
        <DetailCard label="Updated" value={order.updated_at ? format(new Date(order.updated_at), "PPpp") : "-"} />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Order"
        description={`Are you sure you want to delete "${order.title}"?`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
      />
    </>
  );
}

function DetailCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <div className="mt-1 text-sm">{value}</div>
    </div>
  );
}
