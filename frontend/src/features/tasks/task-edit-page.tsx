import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useTask, useUpdateTask } from "@/api/tasks";

const schema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  task_type: z.enum(["general", "inspection", "repair", "installation", "calibration"] as const),
  status: z.enum(["pending", "in_progress", "completed", "cancelled"] as const),
  estimated_duration_hours: z.coerce.number().min(0).optional(),
  doc_link: z.string().optional(),
});

type Form = z.infer<typeof schema>;

export default function TaskEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: task, isLoading } = useTask(id!);
  const update = useUpdateTask();

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: task ? {
      name: task.name,
      description: task.description ?? "",
      task_type: task.task_type,
      status: task.status,
      estimated_duration_hours: task.estimated_duration_hours ?? 0,
      doc_link: task.doc_link ?? "",
    } : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (!task) return <ErrorState message="Task not found" />;

  return (
    <>
      <PageHeader title="Edit Task" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit((data) => update.mutate({ id: id!, data }, { onSuccess: () => navigate(`/tasks/${id}`) }))} className="max-w-lg space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Name *</label>
          <input {...register("name")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <textarea {...register("description")} rows={3} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Task Type *</label>
            <select {...register("task_type")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="general">General</option>
              <option value="inspection">Inspection</option>
              <option value="repair">Repair</option>
              <option value="installation">Installation</option>
              <option value="calibration">Calibration</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Status</label>
            <select {...register("status")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Estimated Duration (hours)</label>
            <input type="number" step="0.5" {...register("estimated_duration_hours", { valueAsNumber: true })} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Doc Link</label>
            <input {...register("doc_link")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
        </div>
        <div className="flex gap-3 pt-4">
          <button type="submit" disabled={update.isPending} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {update.isPending ? "Saving..." : "Save Changes"}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent">Cancel</button>
        </div>
        {update.isError && <p className="text-sm text-destructive">{update.error.message}</p>}
      </form>
    </>
  );
}
