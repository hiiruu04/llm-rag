import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useSystem, useDeleteSystem } from "@/api/systems";
import type { System } from "@/types/cmms";

export default function SystemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: system, isLoading, isError, error, refetch } = useSystem(id!);
  const deleteMutation = useDeleteSystem();

  if (isLoading) return <LoadingState />;
  if (isError || !system) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(system.id);
    setDeleteOpen(false);
    navigate("/systems");
  };

  return (
    <>
      <PageHeader
        title={system.name}
        description="System"
        actions={
          <div className="flex gap-2">
            <Link to={`/systems/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <SystemDetails system={system} />

      <ConfirmDialog
        open={deleteOpen}
        title="Delete System"
        description={`Are you sure you want to delete "${system.name}"?`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
      />
    </>
  );
}

function SystemDetails({ system }: { system: System }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <DetailCard label="Name" value={system.name} />
      <DetailCard label="Description" value={system.description ?? "-"} />
      <DetailCard label="Created" value={system.created_at ? format(new Date(system.created_at), "PPpp") : "-"} />
      <DetailCard label="Updated" value={system.updated_at ? format(new Date(system.updated_at), "PPpp") : "-"} />
    </div>
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
