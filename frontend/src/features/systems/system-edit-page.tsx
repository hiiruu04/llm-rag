import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useSystem, useUpdateSystem } from "@/api/systems";

const schema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
});

type Form = z.infer<typeof schema>;

export default function SystemEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: system, isLoading } = useSystem(id!);
  const update = useUpdateSystem();

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: system ? {
      name: system.name,
      description: system.description ?? "",
    } : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (!system) return <ErrorState message="System not found" />;

  return (
    <>
      <PageHeader title="Edit System" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit((data) => update.mutate({ id: id!, data }, { onSuccess: () => navigate(`/systems/${id}`) }))} className="max-w-lg space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Name *</label>
          <input {...register("name")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <textarea {...register("description")} rows={3} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
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
