import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useDownEvent, useDeleteDownEvent } from "@/api/down-events";

export default function DownEventDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: downEvent, isLoading, isError, error, refetch } = useDownEvent(id!);
  const deleteMutation = useDeleteDownEvent();

  if (isLoading) return <LoadingState />;
  if (isError || !downEvent) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(downEvent.id);
    setDeleteOpen(false);
    navigate("/down-events");
  };

  return (
    <>
      <PageHeader
        title={downEvent.description ?? "Down Event"}
        description={`Severity: ${downEvent.severity ?? "-"} | Status: ${downEvent.status ?? "-"}`}
        actions={
          <div className="flex gap-2">
            <Link to={`/down-events/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <DetailCard label="Description" value={downEvent.description ?? "-"} />
        <DetailCard label="Asset ID" value={downEvent.asset_id ?? "-"} />
        <DetailCard label="Severity" value={<StatusBadge value={downEvent.severity ?? "low"} />} />
        <DetailCard label="Status" value={<StatusBadge value={downEvent.status ?? "active"} />} />
        <DetailCard label="Downtime (mins)" value={downEvent.downtime_minutes?.toString() ?? "-"} />
        <DetailCard label="Created" value={downEvent.created_at ? format(new Date(downEvent.created_at), "PPpp") : "-"} />
        <DetailCard label="Updated" value={downEvent.updated_at ? format(new Date(downEvent.updated_at), "PPpp") : "-"} />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Down Event"
        description={`Are you sure you want to delete "${downEvent.description ?? "this down event"}"?`}
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
