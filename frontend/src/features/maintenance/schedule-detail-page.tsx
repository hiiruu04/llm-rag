import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, Trash2, AlertTriangle, ExternalLink } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useScheduleDetail, useDeleteSchedule } from "@/api/maintenance";

const recurrenceLabels: Record<string, string> = {
  none: "None",
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
  quarterly: "Quarterly",
  yearly: "Yearly",
};

export default function ScheduleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: schedule, isLoading, isError, error, refetch } = useScheduleDetail(id!);
  const deleteMutation = useDeleteSchedule();

  if (isLoading) return <LoadingState />;
  if (isError || !schedule) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    deleteMutation.mutate(schedule.id);
    setDeleteOpen(false);
    navigate("/maintenance");
  };

  return (
    <>
      <PageHeader
        title={schedule.title}
        description={`${schedule.maintenance_type} maintenance \u00B7 ${schedule.priority} priority`}
        actions={
          <div className="flex gap-2">
            <Link
              to={`/maintenance/${id}/edit`}
              className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"
            >
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button
              onClick={() => setDeleteOpen(true)}
              className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      {/* Schedule Info */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <DetailCard label="Title" value={schedule.title} />
        <DetailCard label="Type" value={<StatusBadge value={schedule.maintenance_type} />} />
        <DetailCard label="Priority" value={<StatusBadge value={schedule.priority} />} />
        <DetailCard label="Status" value={<StatusBadge value={schedule.status} />} />
        <DetailCard label="Scheduled Date" value={schedule.scheduled_date ? format(new Date(schedule.scheduled_date), "PPpp") : "-"} />
        <DetailCard
          label="Completed Date"
          value={schedule.completed_date ? format(new Date(schedule.completed_date), "PPpp") : "-"}
        />
        <DetailCard label="Recurrence" value={recurrenceLabels[schedule.recurrence] ?? schedule.recurrence} />
        <DetailCard
          label="Est. Duration"
          value={schedule.estimated_duration_hours != null ? `${schedule.estimated_duration_hours}h` : "-"}
        />
        <DetailCard label="Asset" value={
          schedule.asset
            ? <Link to={`/assets/${schedule.asset_id}`} className="text-primary hover:underline">{schedule.asset.name}</Link>
            : "-"
        } />
      </div>

      {schedule.description && (
        <div className="mt-4 rounded-lg border border-border p-4">
          <p className="text-xs font-medium text-muted-foreground mb-1">Description</p>
          <p className="text-sm whitespace-pre-wrap">{schedule.description}</p>
        </div>
      )}

      {schedule.notes && (
        <div className="mt-4 rounded-lg border border-border p-4">
          <p className="text-xs font-medium text-muted-foreground mb-1">Notes</p>
          <p className="text-sm whitespace-pre-wrap">{schedule.notes}</p>
        </div>
      )}

      {/* Down Events */}
      <div className="mt-6">
        <h2 className="mb-3 text-lg font-semibold">
          Down Events ({schedule.down_events.length})
        </h2>
        {schedule.down_events.length === 0 ? (
          <EmptyCard message="No down events linked to this schedule" />
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-2 text-left font-medium">Severity</th>
                  <th className="px-4 py-2 text-left font-medium">Status</th>
                  <th className="px-4 py-2 text-left font-medium">Started</th>
                  <th className="px-4 py-2 text-left font-medium">Downtime</th>
                  <th className="px-4 py-2 text-left font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {schedule.down_events.map((de) => (
                  <tr key={de.id} className="border-b border-border last:border-0 hover:bg-accent/50">
                    <td className="px-4 py-2"><StatusBadge value={de.severity ?? "low"} /></td>
                    <td className="px-4 py-2"><StatusBadge value={de.status ?? "active"} /></td>
                    <td className="px-4 py-2">{de.started_at ? format(new Date(de.started_at), "PP") : "-"}</td>
                    <td className="px-4 py-2">{de.downtime_minutes != null ? `${de.downtime_minutes} min` : "-"}</td>
                    <td className="px-4 py-2">
                      <Link to={`/down-events/${de.id}`} className="text-primary hover:underline">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Tasks */}
      <div className="mt-6">
        <h2 className="mb-3 text-lg font-semibold">
          Tasks ({schedule.tasks.length})
        </h2>
        {schedule.tasks.length === 0 ? (
          <EmptyCard message="No tasks linked to this schedule" />
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-2 text-left font-medium">Title</th>
                  <th className="px-4 py-2 text-left font-medium">Priority</th>
                  <th className="px-4 py-2 text-left font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {schedule.tasks.map((task) => (
                  <tr key={task.id} className="border-b border-border last:border-0 hover:bg-accent/50">
                    <td className="px-4 py-2">{task.title}</td>
                    <td className="px-4 py-2"><StatusBadge value={task.priority ?? "medium"} /></td>
                    <td className="px-4 py-2"><StatusBadge value={task.status ?? "pending"} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Order */}
      <div className="mt-6">
        {schedule.order ? (
          <>
            <h2 className="mb-3 text-lg font-semibold">Linked Order</h2>
            <div className="rounded-lg border border-border p-4">
              <div className="grid gap-2 sm:grid-cols-2">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Order Number</p>
                  <p className="text-sm">{schedule.order.order_number ?? "-"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Description</p>
                  <p className="text-sm">{schedule.order.description ?? "-"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Status</p>
                  <p className="text-sm"><StatusBadge value={schedule.order.status ?? "-"} /></p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Priority</p>
                  <p className="text-sm"><StatusBadge value={schedule.order.priority ?? "-"} /></p>
                </div>
              </div>
            </div>
          </>
        ) : (
          <>
            <h2 className="mb-3 text-lg font-semibold">Linked Order</h2>
            <EmptyCard message="No order linked to this schedule" />
          </>
        )}
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Schedule"
        description={`Are you sure you want to delete "${schedule.title}"?`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
      />
    </>
  );
}

function DetailCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <div className="mt-1 text-sm">{value}</div>
    </div>
  );
}

function EmptyCard({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-border border-dashed p-4 text-muted-foreground">
      <AlertTriangle className="h-4 w-4" />
      <p className="text-sm">{message}</p>
    </div>
  );
}