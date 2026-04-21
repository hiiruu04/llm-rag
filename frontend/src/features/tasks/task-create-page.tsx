import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { useCreateTask } from "@/api/tasks";
import { useMaintenanceSchedules } from "@/api/maintenance";
import { useShifts } from "@/api/shifts";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().optional(),
  task_type: z.enum(["general", "inspection", "repair", "installation", "calibration"] as const),
  status: z.enum(["pending", "in_progress", "completed", "cancelled"] as const).optional(),
  estimated_duration_hours: z.number().min(0).optional(),
  doc_link: z.string().optional(),
  maintenance_schedule_id: z.string().min(1, "Maintenance schedule is required"),
  shift_id: z.string().optional(),
  assigned_to: z.string().max(255).optional(),
  action_type: z.enum(["safety", "preparation", "inspection", "repair", "verification", "documentation", "standard"] as const).optional(),
  sequence_order: z.number().int().min(0).optional(),
});

type Form = z.infer<typeof schema>;

export default function TaskCreatePage() {
  const navigate = useNavigate();
  const create = useCreateTask();
  const { data: schedulesData } = useMaintenanceSchedules({ per_page: 100 });
  const { data: shiftsData } = useShifts({ per_page: 100 });

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { status: "pending", action_type: "standard", sequence_order: 0 },
  });

  const onSubmit = (data: Form) => {
    create.mutate(data, {
      onSuccess: (res) => navigate(`/tasks/${res.data.id}`),
    });
  };

  return (
    <>
      <PageHeader title="Create Task" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit(onSubmit)} className="max-w-lg space-y-4">
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
              <option value="">Select type...</option>
              <option value="general">General</option>
              <option value="inspection">Inspection</option>
              <option value="repair">Repair</option>
              <option value="installation">Installation</option>
              <option value="calibration">Calibration</option>
            </select>
            {errors.task_type && <p className="mt-1 text-xs text-destructive">{errors.task_type.message}</p>}
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
        <div>
          <label className="mb-1 block text-sm font-medium">Maintenance Schedule *</label>
          <select {...register("maintenance_schedule_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
            <option value="">Select schedule...</option>
            {schedulesData?.data.map((s) => (
              <option key={s.id} value={s.id}>{s.title}</option>
            ))}
          </select>
          {errors.maintenance_schedule_id && <p className="mt-1 text-xs text-destructive">{errors.maintenance_schedule_id.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Shift</label>
            <select {...register("shift_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="">None</option>
              {shiftsData?.data.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Assigned To</label>
            <input {...register("assigned_to")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Action Type</label>
            <select {...register("action_type")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="standard">Standard</option>
              <option value="safety">Safety</option>
              <option value="preparation">Preparation</option>
              <option value="inspection">Inspection</option>
              <option value="repair">Repair</option>
              <option value="verification">Verification</option>
              <option value="documentation">Documentation</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Sequence Order</label>
            <input type="number" {...register("sequence_order", { valueAsNumber: true })} min={0} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
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
          <button type="submit" disabled={create.isPending} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {create.isPending ? "Creating..." : "Create Task"}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent">
            Cancel
          </button>
        </div>
        {create.isError && <p className="text-sm text-destructive">{create.error.message}</p>}
      </form>
    </>
  );
}
