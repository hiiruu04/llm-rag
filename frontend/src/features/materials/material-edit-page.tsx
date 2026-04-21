import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useMaterial, useUpdateMaterial } from "@/api/materials";
import { useOrders } from "@/api/orders";

const schema = z.object({
  name: z.string().min(1).max(255),
  part_number: z.string().optional(),
  description: z.string().optional(),
  quantity_in_stock: z.number().min(0).optional(),
  unit: z.string().optional(),
  order_id: z.string().optional(),
});

type Form = z.infer<typeof schema>;

export default function MaterialEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: material, isLoading } = useMaterial(id!);
  const update = useUpdateMaterial();
  const { data: ordersData } = useOrders({ per_page: 100 });
  const orders = ordersData?.data ?? [];

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: material ? {
      name: material.name,
      part_number: material.part_number ?? "",
      description: material.description ?? "",
      quantity_in_stock: material.quantity_in_stock ?? 0,
      unit: material.unit ?? "",
      order_id: material.order_id ?? "",
    } : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (!material) return <ErrorState message="Material not found" />;

  return (
    <>
      <PageHeader title="Edit Material" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit((data) => update.mutate({ id: id!, data }, { onSuccess: () => navigate(`/materials/${id}`) }))} className="max-w-lg space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Name *</label>
          <input {...register("name")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Part Number</label>
          <input {...register("part_number")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <textarea {...register("description")} rows={3} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Quantity in Stock</label>
            <input type="number" {...register("quantity_in_stock", { valueAsNumber: true })} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
            {errors.quantity_in_stock && <p className="mt-1 text-xs text-destructive">{errors.quantity_in_stock.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Unit</label>
            <input {...register("unit")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Order</label>
          <select {...register("order_id")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
            <option value="">None</option>
            {orders.map((o) => (
              <option key={o.id} value={o.id}>{o.order_number ?? o.id} - {o.title}</option>
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
