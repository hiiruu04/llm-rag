import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useCause, useDeleteCause } from "@/api/causes";

export default function CauseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: cause, isLoading, isError, error, refetch } = useCause(id!);
  const deleteMutation = useDeleteCause();

  if (isLoading) return <LoadingState />;
  if (isError || !cause) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(cause.id);
    setDeleteOpen(false);
    navigate("/causes");
  };

  return (
    <>
      <PageHeader
        title={cause.name}
        description={cause.category ?? "No category"}
        actions={
          <div className="flex gap-2">
            <Link to={`/causes/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <DetailCard label="Name" value={cause.name} />
        <DetailCard label="Category" value={cause.category ?? "-"} />
        <DetailCard label="Severity" value={<StatusBadge value={cause.severity ?? "low"} />} />
        <DetailCard label="Description" value={cause.description ?? "-"} />
        <DetailCard label="Created" value={cause.created_at ? format(new Date(cause.created_at), "PPpp") : "-"} />
        <DetailCard label="Updated" value={cause.updated_at ? format(new Date(cause.updated_at), "PPpp") : "-"} />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Cause"
        description={`Are you sure you want to delete "${cause.name}"?`}
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
