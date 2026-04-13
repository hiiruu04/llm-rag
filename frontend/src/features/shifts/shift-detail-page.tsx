import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useShift, useDeleteShift } from "@/api/shifts";

export default function ShiftDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: shift, isLoading, isError, error, refetch } = useShift(id!);
  const deleteMutation = useDeleteShift();

  if (isLoading) return <LoadingState />;
  if (isError || !shift) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(shift.id);
    setDeleteOpen(false);
    navigate("/shifts");
  };

  return (
    <>
      <PageHeader
        title={shift.name}
        description="Shift details"
        actions={
          <div className="flex gap-2">
            <Link to={`/shifts/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <DetailCard label="Name" value={shift.name} />
        <DetailCard label="Start Time" value={shift.start_time ?? "-"} />
        <DetailCard label="End Time" value={shift.end_time ?? "-"} />
        <DetailCard label="Description" value={shift.description ?? "-"} />
        <DetailCard label="Created" value={shift.created_at ? format(new Date(shift.created_at), "PPpp") : "-"} />
        <DetailCard label="Updated" value={shift.updated_at ? format(new Date(shift.updated_at), "PPpp") : "-"} />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Shift"
        description={`Are you sure you want to delete "${shift.name}"?`}
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
