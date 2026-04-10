import { useParams, Link } from "react-router-dom";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { useSensor } from "@/api/sensors";

export default function SensorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: sensor, isLoading, isError, error, refetch } = useSensor(id!);

  if (isLoading) return <LoadingState />;
  if (isError || !sensor) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  return (
    <>
      <PageHeader
        title={sensor.name}
        description={`${sensor.sensor_type} sensor`}
        actions={
          <Link
            to={`/sensors/${id}/data`}
            className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
          >
            View Data
          </Link>
        }
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <DetailItem label="Name" value={sensor.name} />
        <DetailItem label="Type" value={sensor.sensor_type} />
        <DetailItem label="Unit" value={sensor.unit ?? "-"} />
        <DetailItem label="Status" value={<StatusBadge value={sensor.status} />} />
        <DetailItem label="Asset ID" value={<Link to={`/assets/${sensor.asset_id}`} className="text-primary hover:underline">{sensor.asset_id}</Link>} />
        <DetailItem label="Created" value={sensor.created_at ? format(new Date(sensor.created_at), "PPpp") : "-"} />
      </div>
    </>
  );
}

function DetailItem({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <div className="mt-1 text-sm">{value}</div>
    </div>
  );
}
