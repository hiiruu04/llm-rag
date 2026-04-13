import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useCause, useUpdateCause } from "@/api/causes";

const schema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  category: z.string().optional(),
  severity: z.enum(["low", "medium", "high", "critical"]).optional(),
});

type Form = z.infer<typeof schema>;

export default function CauseEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: cause, isLoading } = useCause(id!);
  const update = useUpdateCause();

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: cause ? {
      name: cause.name,
      description: cause.description ?? "",
      category: cause.category ?? "",
      severity: cause.severity ?? "low",
    } : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (!cause) return <ErrorState message="Cause not found" />;

  return (
    <>
      <PageHeader title="Edit Cause" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit((data) => update.mutate({ id: id!, data }, { onSuccess: () => navigate(`/causes/${id}`) }))} className="max-w-lg space-y-4">
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
            <label className="mb-1 block text-sm font-medium">Category</label>
            <input {...register("category")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Severity</label>
            <select {...register("severity")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
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
