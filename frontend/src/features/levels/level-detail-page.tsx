import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useLevel, useDeleteLevel } from "@/api/levels";

export default function LevelDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: level, isLoading, isError, error, refetch } = useLevel(id!);
  const deleteMutation = useDeleteLevel();

  if (isLoading) return <LoadingState />;
  if (isError || !level) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(id!);
    setDeleteOpen(false);
    navigate("/levels");
  };

  return (
    <>
      <PageHeader
        title={level.name}
        description={`Rank: ${level.rank}`}
        actions={
          <div className="flex gap-2">
            <Link to={`/levels/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <DetailCard label="Name" value={level.name} />
        <DetailCard label="Rank" value={level.rank} />
        <DetailCard label="Description" value={level.description ?? "-"} />
        <DetailCard label="Created" value={level.created_at ? format(new Date(level.created_at), "PPpp") : "-"} />
        <DetailCard label="Updated" value={level.updated_at ? format(new Date(level.updated_at), "PPpp") : "-"} />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Level"
        description={`Are you sure you want to delete "${level.name}"? This action cannot be undone.`}
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
