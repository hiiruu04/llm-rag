import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useOrder, useUpdateOrder } from "@/api/orders";

const schema = z.object({
  order_number: z.string().optional(),
  title: z.string().min(1, "Title is required").max(255),
  description: z.string().optional(),
  order_type: z.enum(["maintenance", "repair", "inspection", "installation"]),
  status: z.enum(["open", "in_progress", "completed", "cancelled"]),
  priority: z.enum(["low", "medium", "high", "critical"]),
  requested_date: z.string().optional(),
});

type Form = z.infer<typeof schema>;

export default function OrderEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: order, isLoading } = useOrder(id!);
  const update = useUpdateOrder();

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: order ? {
      order_number: order.order_number ?? "",
      title: order.title,
      description: order.description ?? "",
      order_type: order.order_type ?? "maintenance",
      status: order.status ?? "open",
      priority: order.priority ?? "medium",
      requested_date: order.requested_date ? order.requested_date.split("T")[0] : "",
    } : undefined,
  });

  if (isLoading) return <LoadingState />;
  if (!order) return <ErrorState message="Order not found" />;

  return (
    <>
      <PageHeader title="Edit Order" actions={
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      } />
      <form onSubmit={handleSubmit((data) => update.mutate({ id: id!, data }, { onSuccess: () => navigate(`/orders/${id}`) }))} className="max-w-lg space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Order Number</label>
          <input {...register("order_number")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
        </div>
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
            <select {...register("order_type")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="maintenance">Maintenance</option>
              <option value="repair">Repair</option>
              <option value="inspection">Inspection</option>
              <option value="installation">Installation</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Status</label>
            <select {...register("status")} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
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
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Requested Date</label>
          <input {...register("requested_date")} type="date" className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
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
