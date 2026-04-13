import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useTask, useDeleteTask } from "@/api/tasks";

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: task, isLoading, isError, error, refetch } = useTask(id!);
  const deleteMutation = useDeleteTask();

  if (isLoading) return <LoadingState />;
  if (isError || !task) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(id!);
    setDeleteOpen(false);
    navigate("/tasks");
  };

  return (
    <>
      <PageHeader
        title={task.name}
        description={`${task.task_type} task`}
        actions={
          <div className="flex gap-2">
            <Link to={`/tasks/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => setDeleteOpen(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <DetailCard label="Name" value={task.name} />
        <DetailCard label="Type" value={task.task_type} />
        <DetailCard label="Status" value={<StatusBadge value={task.status} />} />
        <DetailCard label="Description" value={task.description ?? "-"} />
        <DetailCard label="Estimated Duration" value={task.estimated_duration_hours != null ? `${task.estimated_duration_hours} hours` : "-"} />
        <DetailCard label="Doc Link" value={task.doc_link ? <a href={task.doc_link} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{task.doc_link}</a> : "-"} />
        <DetailCard label="Created" value={task.created_at ? format(new Date(task.created_at), "PPpp") : "-"} />
        <DetailCard label="Updated" value={task.updated_at ? format(new Date(task.updated_at), "PPpp") : "-"} />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Task"
        description={`Are you sure you want to delete "${task.name}"? This action cannot be undone.`}
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
