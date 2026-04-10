import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useSchedule, useUpdateSchedule } from "@/api/maintenance";

const schema = z.object({
  title: z.string().min(1).max(255),
  description: z.string().optional(),
  maintenance_type: z.enum(["preventive", "corrective", "predictive"]),
  status: z.enum(["scheduled", "in_progress", "completed", "cancelled", "overdue"]),
  priority: z.enum(["low", "medium", "high", "critical"]),
  scheduled_date: z.string().min(1),
  recurrence: z.enum(["none", "daily", "weekly", "monthly", "quarterly", "yearly"]),
  assigned_to: z.string().optional(),
  estimated_duration_hours: z.string().optional(),
  notes: z.string().optional(),
});

type Form = z.infer<typeof schema>;

export default function ScheduleEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: schedule, isLoading } = useSchedule(id!);
  const update = useUpdateSchedule();

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: schedule ? {
      title: schedule.title,
      description: schedule.description ?? "",
      maintenance_type: schedule.maintenance_type,
      status: schedule.status,
      priority: schedule.priority,
      scheduled_date: schedule.scheduled_date ?? "",
      recurrence: schedule.recurrence,
      assigned_to: schedule.assigned_to ?? "",
      estimated_duration_hours: schedule.estimated_duration_hours?.toString() ?? "",
      notes: schedule.notes ?? "",
    } : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (!schedule) return <ErrorState message="Schedule not found" />;

  return (
    <>
      <PageHeader title="Edit Schedule" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit((data) => {
        const { estimated_duration_hours, ...rest } = data;
        update.mutate({
          id: id!,
          data: { ...rest, estimated_duration_hours: estimated_duration_hours ? parseFloat(estimated_duration_hours) : undefined },
        }, { onSuccess: () => navigate("/maintenance") });
      })} className="max-w-lg space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Title *</label>
          <input {...register("title")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.title && <p className="mt-1 text-xs text-destructive">{errors.title.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <textarea {...register("description")} rows={3} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Type</label>
            <select {...register("maintenance_type")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="preventive">Preventive</option>
              <option value="corrective">Corrective</option>
              <option value="predictive">Predictive</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Priority</label>
            <select {...register("priority")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Status</label>
            <select {...register("status")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Scheduled Date *</label>
            <input type="datetime-local" {...register("scheduled_date")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Recurrence</label>
            <select {...register("recurrence")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="none">None</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Assigned To</label>
            <input {...register("assigned_to")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Duration (hours)</label>
            <input type="number" step="0.5" {...register("estimated_duration_hours")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Notes</label>
          <textarea {...register("notes")} rows={2} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
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
