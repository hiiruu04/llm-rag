import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useDownEvent, useUpdateDownEvent } from "@/api/down-events";
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

export default function DownEventEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: downEvent, isLoading } = useDownEvent(id!);
  const { data: assetsData } = useAssets({ per_page: 100 });
  const { data: faultsData } = useFaults({ per_page: 100 });
  const { data: schedulesData } = useMaintenanceSchedules({ per_page: 100 });
  const update = useUpdateDownEvent();

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: downEvent ? {
      asset_id: downEvent.asset_id ?? "",
      fault_id: downEvent.fault_id ?? "",
      maintenance_schedule_id: downEvent.maintenance_schedule_id ?? "",
      downtime_minutes: downEvent.downtime_minutes ?? 0,
      severity: downEvent.severity ?? "low",
      status: downEvent.status ?? "active",
    } : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (!downEvent) return <ErrorState message="Down event not found" />;

  return (
    <>
      <PageHeader title="Edit Down Event" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit((data) => update.mutate({ id: id!, data }, { onSuccess: () => navigate(`/down-events/${id}`) }))} className="max-w-lg space-y-4">
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
