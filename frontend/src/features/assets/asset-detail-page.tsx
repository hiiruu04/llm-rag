import { useState } from "react";
import { useParams, useNavigate, Link, useLocation } from "react-router-dom";
import { Edit, Trash2, Plus } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { DataTable } from "@/components/common/data-table";
import { PaginationControls } from "@/components/common/pagination";
import { useAsset, useAssetChildren, useDeleteAsset } from "@/api/assets";
import { useAssetSensors, useDeleteSensor } from "@/api/sensors";
import { useAssetFaults, useDeleteFault } from "@/api/faults";
import { useAssetSchedules, useDeleteSchedule } from "@/api/maintenance";
import type { Asset } from "@/types/asset";
import type { Sensor } from "@/types/sensor";
import type { Fault } from "@/types/fault";
import type { MaintenanceSchedule } from "@/types/maintenance";

const tabs = [
  { key: "details", label: "Details" },
  { key: "children", label: "Children" },
  { key: "sensors", label: "Sensors" },
  { key: "faults", label: "Faults" },
  { key: "maintenance", label: "Maintenance" },
];

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteType, setDeleteType] = useState<"asset" | "sensor" | "fault" | "schedule" | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);

  const { data: asset, isLoading, isError, error, refetch } = useAsset(id!);

  const deleteAsset = useDeleteAsset();
  const deleteSensor = useDeleteSensor();
  const deleteFault = useDeleteFault();
  const deleteSchedule = useDeleteSchedule();

  const hash = location.hash.replace("#", "");
  const currentTab = tabs.find((t) => t.key === hash)?.key ?? "details";

  if (isLoading) return <LoadingState />;
  if (isError || !asset) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  const handleDelete = () => {
    if (!deleteTarget || !deleteType) return;
    const mutators: Record<string, () => void> = {
      asset: () => deleteAsset.mutate(deleteTarget.id),
      sensor: () => deleteSensor.mutate({ id: deleteTarget.id, assetId: id! }),
      fault: () => deleteFault.mutate(deleteTarget.id),
      schedule: () => deleteSchedule.mutate(deleteTarget.id),
    };
    mutators[deleteType]();
    setDeleteOpen(false);
    if (deleteType === "asset") navigate("/assets");
  };

  return (
    <>
      <PageHeader
        title={asset.name}
        description={`${asset.asset_type} — ${asset.location ?? "No location"}`}
        actions={
          <div className="flex gap-2">
            <Link to={`/assets/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => { setDeleteType("asset"); setDeleteTarget({ id: asset.id, name: asset.name }); setDeleteOpen(true); }} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10">
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          </div>
        }
      />

      <div className="mb-6 flex gap-1 border-b border-border">
        {tabs.map((tab) => (
          <a
            key={tab.key}
            href={`#${tab.key}`}
            className={`px-4 py-2 text-sm ${currentTab === tab.key ? "border-b-2 border-primary font-medium" : "text-muted-foreground hover:text-foreground"}`}
          >
            {tab.label}
          </a>
        ))}
      </div>

      {currentTab === "details" && <AssetDetails asset={asset} />}
      {currentTab === "children" && <AssetChildren assetId={id!} />}
      {currentTab === "sensors" && <AssetSensorsTab assetId={id!} onDelete={(s) => { setDeleteType("sensor"); setDeleteTarget(s); setDeleteOpen(true); }} />}
      {currentTab === "faults" && <AssetFaultsTab assetId={id!} onDelete={(f) => { setDeleteType("fault"); setDeleteTarget(f); setDeleteOpen(true); }} />}
      {currentTab === "maintenance" && <AssetMaintenanceTab assetId={id!} onDelete={(s) => { setDeleteType("schedule"); setDeleteTarget(s); setDeleteOpen(true); }} />}

      <ConfirmDialog
        open={deleteOpen}
        title={`Delete ${deleteType}`}
        description={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
      />
    </>
  );
}

function AssetDetails({ asset }: { asset: Asset }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <DetailCard label="Name" value={asset.name} />
      <DetailCard label="Type" value={asset.asset_type} />
      <DetailCard label="Status" value={<StatusBadge value={asset.status} />} />
      <DetailCard label="Location" value={asset.location ?? "-"} />
      <DetailCard label="Description" value={asset.description ?? "-"} />
      <DetailCard label="Created" value={asset.created_at ? format(new Date(asset.created_at), "PPpp") : "-"} />
      <DetailCard label="Updated" value={asset.updated_at ? format(new Date(asset.updated_at), "PPpp") : "-"} />
    </div>
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

function AssetChildren({ assetId }: { assetId: string }) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAssetChildren(assetId, { page, per_page: 10 });
  if (isLoading) return <LoadingState rows={3} />;
  return (
    <>
      <DataTable<Asset>
        data={data?.data ?? []}
        keyExtractor={(a) => a.id}
        columns={[
          { header: "Name", accessor: "name" },
          { header: "Type", accessor: "asset_type" },
          { header: "Status", accessor: (a) => <StatusBadge value={a.status} /> },
        ]}
      />
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />
    </>
  );
}

function AssetSensorsTab({ assetId, onDelete }: { assetId: string; onDelete: (s: { id: string; name: string }) => void }) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAssetSensors(assetId, { page, per_page: 10 });
  if (isLoading) return <LoadingState rows={3} />;
  return (
    <>
      <DataTable<Sensor>
        data={data?.data ?? []}
        keyExtractor={(s) => s.id}
        columns={[
          { header: "Name", accessor: (s) => <Link to={`/sensors/${s.id}`} className="hover:underline">{s.name}</Link> },
          { header: "Type", accessor: "sensor_type" },
          { header: "Unit", accessor: (s) => s.unit ?? "-" },
          { header: "Status", accessor: (s) => <StatusBadge value={s.status} /> },
          {
            header: "", accessor: (s) => (
              <div className="flex gap-2">
                <Link to={`/sensors/${s.id}/data`} className="text-xs text-primary hover:underline">Data</Link>
                <button onClick={() => onDelete({ id: s.id, name: s.name })} className="text-xs text-destructive hover:underline">Delete</button>
              </div>
            ),
          },
        ]}
      />
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />
    </>
  );
}

function AssetFaultsTab({ assetId, onDelete }: { assetId: string; onDelete: (f: { id: string; name: string }) => void }) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAssetFaults(assetId, { page, per_page: 10 });
  if (isLoading) return <LoadingState rows={3} />;
  return (
    <>
      <div className="mb-4 flex justify-end">
        <Link to={`/assets/${assetId}/faults/new`} className="flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground">
          <Plus className="h-3.5 w-3.5" /> Report Fault
        </Link>
      </div>
      <DataTable<Fault>
        data={data?.data ?? []}
        keyExtractor={(f) => f.id}
        columns={[
          { header: "Code", accessor: "code" },
          { header: "Name", accessor: (f) => <Link to={`/faults/${f.id}`} className="hover:underline">{f.name}</Link> },
          { header: "Severity", accessor: (f) => <StatusBadge value={f.severity} /> },
          { header: "Status", accessor: (f) => <StatusBadge value={f.status} /> },
          {
            header: "", accessor: (f) => (
              <button onClick={() => onDelete({ id: f.id, name: f.name })} className="text-xs text-destructive hover:underline">Delete</button>
            ),
          },
        ]}
      />
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />
    </>
  );
}

function AssetMaintenanceTab({ assetId, onDelete }: { assetId: string; onDelete: (s: { id: string; name: string }) => void }) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAssetSchedules(assetId, { page, per_page: 10 });
  if (isLoading) return <LoadingState rows={3} />;
  return (
    <>
      <div className="mb-4 flex justify-end">
        <Link to={`/assets/${assetId}/maintenance/new`} className="flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground">
          <Plus className="h-3.5 w-3.5" /> Schedule
        </Link>
      </div>
      <DataTable<MaintenanceSchedule>
        data={data?.data ?? []}
        keyExtractor={(s) => s.id}
        columns={[
          { header: "Title", accessor: (s) => <Link to={`/maintenance/${s.id}/edit`} className="hover:underline">{s.title}</Link> },
          { header: "Type", accessor: (s) => <StatusBadge value={s.maintenance_type} /> },
          { header: "Priority", accessor: (s) => <StatusBadge value={s.priority} /> },
          { header: "Status", accessor: (s) => <StatusBadge value={s.status} /> },
          {
            header: "", accessor: (s) => (
              <button onClick={() => onDelete({ id: s.id, name: s.title })} className="text-xs text-destructive hover:underline">Delete</button>
            ),
          },
        ]}
      />
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />
    </>
  );
}
