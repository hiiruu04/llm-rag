import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useHealth } from "@/api/health";

export default function HealthPage() {
  const { data: health, isLoading, isError, error, refetch } = useHealth();

  if (isLoading) return <><PageHeader title="Health" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Health" /><ErrorState message={error?.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader title="Health" description="Service health status" />

      {health ? (
        <div className="space-y-6">
          <div className="rounded-lg border border-border p-4">
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${health.status === "healthy" ? "bg-green-500" : "bg-red-500"}`} />
              <span className="text-lg font-semibold capitalize">{health.status}</span>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <ServiceCard name="PostgreSQL" connected={health.postgres_connected} />
            <ServiceCard name="Qdrant Vector DB" connected={health.qdrant_connected} />
            <ServiceCard name="OpenAI API" connected={health.openai_connected} />
            <ServiceCard name="Neo4j Graph DB" connected={health.neo4j_connected} />
          </div>

          {health.collection_info && (
            <div className="rounded-lg border border-border p-4">
              <h3 className="mb-3 text-sm font-semibold">Qdrant Collection</h3>
              <pre className="overflow-x-auto rounded bg-muted p-3 text-xs">{JSON.stringify(health.collection_info, null, 2)}</pre>
            </div>
          )}

          {health.graph_info && (
            <div className="rounded-lg border border-border p-4">
              <h3 className="mb-3 text-sm font-semibold">Graph Info</h3>
              <pre className="overflow-x-auto rounded bg-muted p-3 text-xs">{JSON.stringify(health.graph_info, null, 2)}</pre>
            </div>
          )}
        </div>
      ) : (
        <ErrorState message="No health data available" />
      )}
    </>
  );
}

function ServiceCard({ name, connected }: { name: string; connected: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border p-4">
      <span className="text-sm font-medium">{name}</span>
      <div className="flex items-center gap-2">
        <div className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
        <span className="text-xs text-muted-foreground">{connected ? "Connected" : "Disconnected"}</span>
      </div>
    </div>
  );
}
