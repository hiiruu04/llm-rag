import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { format } from "date-fns";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/common/data-table";
import { PaginationControls } from "@/components/common/pagination";
import { LoadingState } from "@/components/common/loading-state";
import { DateRangePicker } from "@/components/common/date-range-picker";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useSensor } from "@/api/sensors";
import { useSensorData, useLatestSensorData, useCreateSensorData, useBatchInsertSensorData, useDeleteSensorData } from "@/api/sensor-data";
import type { SensorData } from "@/types/sensor-data";

export default function SensorDataPage() {
  const { id } = useParams<{ id: string }>();
  const [page, setPage] = useState(1);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [showBatch, setShowBatch] = useState(false);
  const [deleteRange, setDeleteRange] = useState(false);

  const { data: sensor } = useSensor(id!);
  const { data, isLoading } = useSensorData(id!, {
    page,
    per_page: 50,
    start_time: startTime || undefined,
    end_time: endTime || undefined,
  });
  const { data: latest } = useLatestSensorData(id!);
  const createMutation = useCreateSensorData();
  const batchMutation = useBatchInsertSensorData();
  const deleteMutation = useDeleteSensorData();

  const chartData = (data?.data ?? [])
    .slice()
    .reverse()
    .map((d: SensorData) => ({
      time: d.timestamp ? format(new Date(d.timestamp), "HH:mm") : "",
      value: d.value,
    }));

  if (isLoading) return <LoadingState />;

  return (
    <>
      <PageHeader
        title={sensor ? `${sensor.name} — Data` : "Sensor Data"}
        description={sensor?.sensor_type}
        actions={
          <Link to={`/sensors/${id}`} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Sensor
          </Link>
        }
      />

      {latest && (
        <div className="mb-6 rounded-lg border border-border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Latest Reading</p>
          <p className="mt-1 text-2xl font-bold">
            {latest.value} {sensor?.unit ?? ""}
          </p>
          <p className="text-xs text-muted-foreground">
            {latest.timestamp ? format(new Date(latest.timestamp), "PPpp") : "N/A"}
          </p>
        </div>
      )}

      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Time Range</label>
          <DateRangePicker start={startTime} end={endTime} onStartChange={setStartTime} onEndChange={setEndTime} />
        </div>
        <button onClick={() => setShowAdd(true)} className="flex items-center gap-1 rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground">
          <Plus className="h-3.5 w-3.5" /> Add Reading
        </button>
        <button onClick={() => setShowBatch(true)} className="rounded-md border border-border px-3 py-2 text-sm hover:bg-accent">
          Batch Import
        </button>
        <button onClick={() => setDeleteRange(true)} className="flex items-center gap-1 rounded-md border border-destructive px-3 py-2 text-sm text-destructive hover:bg-destructive/10">
          <Trash2 className="h-3.5 w-3.5" /> Delete Range
        </button>
      </div>

      {chartData.length > 1 && (
        <div className="mb-6 h-64 rounded-lg border border-border bg-card p-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="var(--color-muted-foreground)" />
              <YAxis tick={{ fontSize: 12 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{ background: "var(--color-card)", border: "1px solid var(--color-border)", borderRadius: 8 }}
              />
              <Line type="monotone" dataKey="value" stroke="var(--color-primary)" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <DataTable<SensorData>
        data={data?.data ?? []}
        keyExtractor={(d) => String(d.id)}
        columns={[
          { header: "ID", accessor: (d) => d.id },
          { header: "Timestamp", accessor: (d) => d.timestamp ? format(new Date(d.timestamp), "PPpp") : "-" },
          { header: "Value", accessor: (d) => `${d.value} ${sensor?.unit ?? ""}` },
        ]}
      />
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />

      {showAdd && (
        <ManualEntryDialog
          sensorId={id!}
          onSubmit={(v) => createMutation.mutate(v, { onSuccess: () => setShowAdd(false) })}
          onClose={() => setShowAdd(false)}
          loading={createMutation.isPending}
        />
      )}
      {showBatch && (
        <BatchImportDialog
          sensorId={id!}
          onSubmit={(v) => batchMutation.mutate(v, { onSuccess: () => setShowBatch(false) })}
          onClose={() => setShowBatch(false)}
          loading={batchMutation.isPending}
        />
      )}
      <ConfirmDialog
        open={deleteRange}
        title="Delete Readings"
        description="Delete all readings in the selected time range?"
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={() => {
          if (startTime && endTime) {
            deleteMutation.mutate({ sensorId: id!, start_time: startTime, end_time: endTime }, { onSuccess: () => setDeleteRange(false) });
          }
        }}
        onCancel={() => setDeleteRange(false)}
      />
    </>
  );
}

function ManualEntryDialog({ sensorId, onSubmit, onClose, loading }: { sensorId: string; onSubmit: (v: { sensorId: string; data: { value: number; timestamp?: string } }) => void; onClose: () => void; loading: boolean }) {
  const [value, setValue] = useState("");
  const [ts, setTs] = useState("");
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border border-border bg-card p-6">
        <h3 className="text-lg font-semibold">Add Reading</h3>
        <div className="mt-4 space-y-3">
          <input type="number" step="any" placeholder="Value" value={value} onChange={(e) => setValue(e.target.value)} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
          <input type="datetime-local" value={ts} onChange={(e) => setTs(e.target.value)} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" />
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-md border border-border px-4 py-2 text-sm">Cancel</button>
          <button
            onClick={() => onSubmit({ sensorId, data: { value: parseFloat(value), timestamp: ts ? new Date(ts).toISOString() : undefined } })}
            disabled={loading || !value}
            className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
          >
            {loading ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

function BatchImportDialog({ sensorId, onSubmit, onClose, loading }: { sensorId: string; onSubmit: (v: { sensorId: string; data: { readings: { value: number; timestamp?: string }[] } }) => void; onClose: () => void; loading: boolean }) {
  const [json, setJson] = useState("");
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg border border-border bg-card p-6">
        <h3 className="text-lg font-semibold">Batch Import</h3>
        <p className="mt-1 text-xs text-muted-foreground">Paste JSON array: [{"{ \"value\": 1.0, \"timestamp\": \"...\" }"}]</p>
        <textarea
          rows={8}
          value={json}
          onChange={(e) => setJson(e.target.value)}
          className="mt-3 w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-xs"
        />
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-md border border-border px-4 py-2 text-sm">Cancel</button>
          <button
            onClick={() => {
              try {
                const readings = JSON.parse(json);
                onSubmit({ sensorId, data: { readings } });
              } catch { /* invalid json */ }
            }}
            disabled={loading || !json}
            className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
          >
            {loading ? "Importing..." : "Import"}
          </button>
        </div>
      </div>
    </div>
  );
}
