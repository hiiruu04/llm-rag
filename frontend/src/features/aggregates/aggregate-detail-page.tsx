import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useAggregate, useDeleteAggregate } from "@/api/aggregates";
import type { Aggregate } from "@/types/cmms";

export default function AggregateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: aggregate, isLoading, isError, error, refetch } = useAggregate(id!);
  const deleteMutation = useDeleteAggregate();

  if (isLoading) return <LoadingState />;
  if (isError || !aggregate) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(aggregate.id);
    setDeleteOpen(false);
    navigate("/aggregates");
  };

  return (
    <>
      <PageHeader
        title={aggregate.name}
        description="Aggregate"
        actions={
          <div className="flex gap-2">
            <Link to={`/aggregates/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <AggregateDetails aggregate={aggregate} />

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Aggregate"
        description={`Are you sure you want to delete "${aggregate.name}"?`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
      />
    </>
  );
}

function AggregateDetails({ aggregate }: { aggregate: Aggregate }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <DetailCard label="Name" value={aggregate.name} />
      <DetailCard label="Description" value={aggregate.description ?? "-"} />
      <DetailCard label="Created" value={aggregate.created_at ? format(new Date(aggregate.created_at), "PPpp") : "-"} />
      <DetailCard label="Updated" value={aggregate.updated_at ? format(new Date(aggregate.updated_at), "PPpp") : "-"} />
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
