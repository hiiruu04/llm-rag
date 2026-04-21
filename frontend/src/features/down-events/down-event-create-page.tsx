import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { useCreateDownEvent } from "@/api/down-events";
import { useAssets } from "@/api/assets";
import { useFaults } from "@/api/faults";
import { useMaintenanceSchedules } from "@/api/maintenance";

const schema = z.object({
  asset_id: z.string().optional(),
  fault_id: z.string().min(1, "Fault is required"),
  maintenance_schedule_id: z.string().optional(),
  downtime_minutes: z.number().min(0, "Must be 0 or greater").optional(),
  severity: z.enum(["low", "medium", "high", "critical"]),
  status: z.enum(["active", "resolved"]),
});

type Form = z.infer<typeof schema>;

export default function DownEventCreatePage() {
  const navigate = useNavigate();
  const create = useCreateDownEvent();
  const { data: assetsData } = useAssets({ per_page: 100 });
  const { data: faultsData } = useFaults({ per_page: 100 });
  const { data: schedulesData } = useMaintenanceSchedules({ per_page: 100 });

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { severity: "low", status: "active" },
  });

  const onSubmit = (data: Form) => {
    create.mutate(data, {
      onSuccess: (res) => navigate(`/down-events/${res.data.id}`),
    });
  };

  return (
    <>
      <PageHeader title="Create Down Event" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit(onSubmit)} className="max-w-lg space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Asset</label>
            <select {...register("asset_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="">None</option>
              {assetsData?.data.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Fault *</label>
            <select {...register("fault_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="">Select fault...</option>
              {faultsData?.data.map((f) => (
                <option key={f.id} value={f.id}>{f.code} — {f.name}</option>
              ))}
            </select>
            {errors.fault_id && <p className="mt-1 text-xs text-destructive">{errors.fault_id.message}</p>}
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Maintenance Schedule</label>
          <select {...register("maintenance_schedule_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
            <option value="">None</option>
            {schedulesData?.data.map((s) => (
              <option key={s.id} value={s.id}>{s.title}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Downtime (minutes)</label>
          <input {...register("downtime_minutes", { valueAsNumber: true })} type="number" min={0} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.downtime_minutes && <p className="mt-1 text-xs text-destructive">{errors.downtime_minutes.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Severity</label>
            <select {...register("severity")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Status</label>
            <select {...register("status")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="active">Active</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
        <div className="flex gap-3 pt-4">
          <button type="submit" disabled={create.isPending} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {create.isPending ? "Creating..." : "Create Down Event"}
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
