import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useLocation, useDeleteLocation } from "@/api/locations";

export default function LocationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: location, isLoading, isError, error, refetch } = useLocation(id!);
  const deleteMutation = useDeleteLocation();

  if (isLoading) return <LoadingState />;
  if (isError || !location) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(id!);
    setDeleteOpen(false);
    navigate("/locations");
  };

  return (
    <>
      <PageHeader
        title={location.name}
        description={location.location_type ?? undefined}
        actions={
          <div className="flex gap-2">
            <Link to={`/locations/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <DetailCard label="Name" value={location.name} />
        <DetailCard label="Type" value={location.location_type ?? "-"} />
        <DetailCard label="Description" value={location.description ?? "-"} />
        <DetailCard label="Parent ID" value={location.parent_id ?? "-"} />
        <DetailCard label="Created" value={location.created_at ? format(new Date(location.created_at), "PPpp") : "-"} />
        <DetailCard label="Updated" value={location.updated_at ? format(new Date(location.updated_at), "PPpp") : "-"} />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Location"
        description={`Are you sure you want to delete "${location.name}"? This action cannot be undone.`}
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
