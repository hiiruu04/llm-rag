import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useAction, useUpdateAction } from "@/api/actions";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().optional(),
  action_type: z.string().max(100).optional(),
  sequence_order: z.coerce.number().int().min(0).optional(),
});

type Form = z.infer<typeof schema>;

export default function ActionEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: action, isLoading, isError, error } = useAction(id!);
  const update = useUpdateAction();

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: action
      ? {
          name: action.name,
          description: action.description ?? "",
          action_type: action.action_type ?? "",
          sequence_order: action.sequence_order ?? 0,
        }
      : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (isError || !action) return <ErrorState message={error?.message} />;

  const onSubmit = (data: Form) => {
    update.mutate(
      { id: id!, data },
      { onSuccess: () => navigate(`/actions/${id}`) },
    );
  };

  return (
    <>
      <PageHeader title="Edit Action" actions={
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
            <label className="mb-1 block text-sm font-medium">Action Type</label>
            <input {...register("action_type")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Sequence Order</label>
            <input {...register("sequence_order")} type="number" className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
        </div>
        <div className="flex gap-3 pt-4">
          <button type="submit" disabled={update.isPending} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {update.isPending ? "Saving..." : "Save Changes"}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent">
            Cancel
          </button>
        </div>
        {update.isError && <p className="text-sm text-destructive">{update.error.message}</p>}
      </form>
    </>
  );
}
