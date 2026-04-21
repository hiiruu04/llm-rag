import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, ArrowLeft } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { DataTable } from "@/components/common/data-table";
import { useRole } from "@/api/roles";
import type { Role, LevelBrief } from "@/types/cmms";

export default function RoleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: role, isLoading, isError, error, refetch } = useRole(id!);

  if (isLoading) return <LoadingState />;
  if (isError || !role) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  return (
    <>
      <PageHeader
        title={role.name}
        description="Role details"
        actions={
          <div className="flex gap-2">
            <Link to={`/roles/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => navigate(-1)} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <ArrowLeft className="h-3.5 w-3.5" /> Back
            </button>
          </div>
        }
      />

      <RoleDetails role={role} />
      {role.levels && role.levels.length > 0 && <RoleLevelsSection levels={role.levels} />}
    </>
  );
}

function RoleDetails({ role }: { role: Role }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <DetailCard label="Name" value={role.name} />
      <DetailCard label="Description" value={role.description ?? "-"} />
      <DetailCard label="Levels" value={role.level_count ?? 0} />
      <DetailCard label="Created" value={role.created_at ? format(new Date(role.created_at), "PPpp") : "-"} />
      <DetailCard label="Updated" value={role.updated_at ? format(new Date(role.updated_at), "PPpp") : "-"} />
    </div>
  );
}

function RoleLevelsSection({ levels }: { levels: LevelBrief[] }) {
  return (
    <div className="mt-8">
      <h3 className="mb-4 text-lg font-semibold">Levels</h3>
      <DataTable<LevelBrief>
        data={levels}
        keyExtractor={(l) => l.id}
        onRowClick={(l) => window.location.href = `/levels/${l.id}`}
        columns={[
          { header: "Name", accessor: (l) => (
            <Link to={`/levels/${l.id}`} className="hover:underline" onClick={(e) => e.stopPropagation()}>{l.name}</Link>
          )},
          { header: "Rank", accessor: (l) => l.rank },
          { header: "Description", accessor: (l) => l.description ?? "-" },
        ]}
      />
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
