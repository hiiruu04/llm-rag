import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useWorker, useUpdateWorker } from "@/api/workers";
import { useLevels } from "@/api/levels";
import type { Level } from "@/types/cmms";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  employee_id: z.string().min(1, "Employee ID is required").max(100),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  phone: z.string().max(50).optional(),
  status: z.enum(["active", "inactive", "on_leave"]),
  level_id: z.string().optional(),
});

type Form = z.infer<typeof schema>;

export default function WorkerEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: worker, isLoading } = useWorker(id!);
  const { data: levelsData } = useLevels({ per_page: 100 });
  const update = useUpdateWorker();

  const groupedLevels = useMemo(() => {
    const levels = levelsData?.data ?? [];
    const groups: Record<string, { role_id: string | null; levels: Level[] }> = {};
    for (const level of levels) {
      const key = level.role_name ?? "Unassigned";
      if (!groups[key]) groups[key] = { role_id: level.role_id, levels: [] };
      groups[key].levels.push(level);
    }
    for (const g of Object.values(groups)) {
      g.levels.sort((a, b) => a.rank - b.rank);
    }
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  }, [levelsData?.data]);

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: worker ? {
      name: worker.name,
      employee_id: worker.employee_id,
      email: worker.email ?? "",
      phone: worker.phone ?? "",
      status: worker.status,
      level_id: worker.level_id ?? "",
    } : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (!worker) return <ErrorState message="Worker not found" />;

  return (
    <>
      <PageHeader title="Edit Worker" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit((data) => update.mutate({ id: id!, data }, { onSuccess: () => navigate(`/workers/${id}`) }))} className="max-w-lg space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Name *</label>
          <input {...register("name")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Employee ID *</label>
          <input {...register("employee_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.employee_id && <p className="mt-1 text-xs text-destructive">{errors.employee_id.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Email</label>
          <input {...register("email")} type="email" className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.email && <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Phone</label>
          <input {...register("phone")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.phone && <p className="mt-1 text-xs text-destructive">{errors.phone.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Status</label>
          <select {...register("status")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="on_leave">On Leave</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Level</label>
          <select {...register("level_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
            <option value="">None</option>
            {groupedLevels.map(([roleName, group]) => (
              <optgroup key={roleName} label={roleName}>
                {group.levels.map((l) => (
                  <option key={l.id} value={l.id}>{l.name} (Rank {l.rank})</option>
                ))}
              </optgroup>
            ))}
          </select>
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
