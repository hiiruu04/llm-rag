import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useMaterial, useDeleteMaterial } from "@/api/materials";

export default function MaterialDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: material, isLoading, isError, error, refetch } = useMaterial(id!);
  const deleteMutation = useDeleteMaterial();

  if (isLoading) return <LoadingState />;
  if (isError || !material) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(material.id);
    setDeleteOpen(false);
    navigate("/materials");
  };

  return (
    <>
      <PageHeader
        title={material.name}
        description={material.part_number ?? "No part number"}
        actions={
          <div className="flex gap-2">
            <Link to={`/materials/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <DetailCard label="Name" value={material.name} />
        <DetailCard label="Part Number" value={material.part_number ?? "-"} />
        <DetailCard label="Quantity in Stock" value={material.quantity_in_stock?.toString() ?? "0"} />
        <DetailCard label="Unit" value={material.unit ?? "-"} />
        <DetailCard label="Description" value={material.description ?? "-"} />
        <DetailCard label="Created" value={material.created_at ? format(new Date(material.created_at), "PPpp") : "-"} />
        <DetailCard label="Updated" value={material.updated_at ? format(new Date(material.updated_at), "PPpp") : "-"} />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Material"
        description={`Are you sure you want to delete "${material.name}"?`}
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
