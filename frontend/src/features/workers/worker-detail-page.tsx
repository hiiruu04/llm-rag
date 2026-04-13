import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, ArrowLeft } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { DataTable } from "@/components/common/data-table";
import { useWorker, useWorkerCompetences } from "@/api/workers";
import type { Worker } from "@/types/cmms";

export default function WorkerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: worker, isLoading, isError, error, refetch } = useWorker(id!);

  if (isLoading) return <LoadingState />;
  if (isError || !worker) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  return (
    <>
      <PageHeader
        title={worker.name}
        description={`Employee ID: ${worker.employee_id}`}
        actions={
          <div className="flex gap-2">
            <Link to={`/workers/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => navigate(-1)} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <ArrowLeft className="h-3.5 w-3.5" /> Back
            </button>
          </div>
        }
      />

      <WorkerDetails worker={worker} />
      <WorkerCompetencesSection workerId={id!} />
    </>
  );
}

function WorkerDetails({ worker }: { worker: Worker }) {
  return (
    <div className="mb-8 grid gap-4 sm:grid-cols-2">
      <DetailCard label="Name" value={worker.name} />
      <DetailCard label="Employee ID" value={worker.employee_id} />
      <DetailCard label="Email" value={worker.email ?? "-"} />
      <DetailCard label="Phone" value={worker.phone ?? "-"} />
      <DetailCard label="Status" value={<StatusBadge value={worker.status} />} />
      <DetailCard label="Created" value={worker.created_at ? format(new Date(worker.created_at), "PPpp") : "-"} />
      <DetailCard label="Updated" value={worker.updated_at ? format(new Date(worker.updated_at), "PPpp") : "-"} />
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

function WorkerCompetencesSection({ workerId }: { workerId: string }) {
  const { data, isLoading } = useWorkerCompetences(workerId);

  if (isLoading) return <LoadingState rows={3} />;

  const competences = data?.data ?? [];

  return (
    <div>
      <h3 className="mb-4 text-lg font-semibold">Competences</h3>
      {competences.length > 0 ? (
        <DataTable<{ id: string; name: string; category: string | null; level_name?: string }>
          data={competences}
          keyExtractor={(c) => c.id}
          columns={[
            { header: "Name", accessor: (c) => <Link to={`/competences/${c.id}`} className="hover:underline">{c.name}</Link> },
            { header: "Category", accessor: (c) => c.category ?? "-" },
          ]}
        />
      ) : (
        <p className="text-sm text-muted-foreground">No competences assigned to this worker.</p>
      )}
    </div>
  );
}
