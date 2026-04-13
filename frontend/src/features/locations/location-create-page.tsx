import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { useCreateLocation, useLocations } from "@/api/locations";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().optional(),
  location_type: z.string().max(100).optional(),
  parent_id: z.string().optional(),
});

type Form = z.infer<typeof schema>;

export default function LocationCreatePage() {
  const navigate = useNavigate();
  const create = useCreateLocation();
  const { data: locationsData } = useLocations({ per_page: 100 });

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
  });

  const onSubmit = (data: Form) => {
    create.mutate(data, {
      onSuccess: (res) => navigate(`/locations/${res.data.id}`),
    });
  };

  return (
    <>
      <PageHeader title="Create Location" actions={
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
        <div>
          <label className="mb-1 block text-sm font-medium">Location Type</label>
          <input {...register("location_type")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Parent Location</label>
          <select {...register("parent_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
            <option value="">None (top-level)</option>
            {locationsData?.data.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
        <div className="flex gap-3 pt-4">
          <button type="submit" disabled={create.isPending} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {create.isPending ? "Creating..." : "Create Location"}
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
