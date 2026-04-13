import { useParams, useNavigate, Link } from "react-router-dom";
import { Edit, ArrowLeft } from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useCompetence } from "@/api/competences";
import type { Competence } from "@/types/cmms";

export default function CompetenceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: competence, isLoading, isError, error, refetch } = useCompetence(id!);

  if (isLoading) return <LoadingState />;
  if (isError || !competence) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  return (
    <>
      <PageHeader
        title={competence.name}
        description="Competence details"
        actions={
          <div className="flex gap-2">
            <Link to={`/competences/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <button onClick={() => navigate(-1)} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <ArrowLeft className="h-3.5 w-3.5" /> Back
            </button>
          </div>
        }
      />

      <CompetenceDetails competence={competence} />
    </>
  );
}

function CompetenceDetails({ competence }: { competence: Competence }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <DetailCard label="Name" value={competence.name} />
      <DetailCard label="Category" value={competence.category ?? "-"} />
      <DetailCard label="Description" value={competence.description ?? "-"} />
      <DetailCard label="Created" value={competence.created_at ? format(new Date(competence.created_at), "PPpp") : "-"} />
      <DetailCard label="Updated" value={competence.updated_at ? format(new Date(competence.updated_at), "PPpp") : "-"} />
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
