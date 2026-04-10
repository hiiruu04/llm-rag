import { Link } from "react-router-dom";
import { Server, AlertTriangle, Wrench, Activity, Plus, MessageSquare, FileText, Network } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { useHealth } from "@/api/health";
import { useAssets } from "@/api/assets";
import { useMaintenanceSchedules, useOverdueSchedules } from "@/api/maintenance";

export default function DashboardPage() {
  const { data: health, isLoading: healthLoading } = useHealth();
  const { data: assetsData } = useAssets({ per_page: 1 });
  const { data: maintenanceData } = useMaintenanceSchedules({ per_page: 1, status: "scheduled" });
  const { data: overdueData } = useOverdueSchedules({ per_page: 1 });

  return (
    <>
      <PageHeader title="Dashboard" description="CMMS Platform Overview" />

      {/* Health Status */}
      <div className="mb-6 rounded-lg border border-border p-4">
        <h2 className="mb-3 text-sm font-semibold">Service Status</h2>
        {healthLoading ? (
          <LoadingState rows={1} />
        ) : health ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <ServiceStatus label="PostgreSQL" connected={health.postgres_connected} />
            <ServiceStatus label="Qdrant" connected={health.qdrant_connected} />
            <ServiceStatus label="OpenAI" connected={health.openai_connected} />
            <ServiceStatus label="Neo4j" connected={health.neo4j_connected} />
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Unable to fetch health status</p>
        )}
      </div>

      {/* Metrics Cards */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          icon={Server}
          label="Total Assets"
          value={assetsData?.pagination?.total ?? 0}
          to="/assets"
        />
        <MetricCard
          icon={AlertTriangle}
          label="Active Faults"
          value="-"
          to="/faults"
        />
        <MetricCard
          icon={Wrench}
          label="Scheduled Maintenance"
          value={maintenanceData?.pagination?.total ?? 0}
          to="/maintenance"
        />
        <MetricCard
          icon={Activity}
          label="Overdue"
          value={overdueData?.pagination?.total ?? 0}
          to="/maintenance"
          variant={overdueData?.pagination?.total ? "warning" : "default"}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <QuickAction icon={Plus} label="New Asset" to="/assets/new" />
        <QuickAction icon={MessageSquare} label="AI Query" to="/query" />
        <QuickAction icon={FileText} label="Upload Document" to="/documents" />
        <QuickAction icon={Network} label="Graph Admin" to="/admin/graph" />
      </div>
    </>
  );
}

function ServiceStatus({ label, connected }: { label: string; connected: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
      <span className="text-sm">{label}</span>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, to, variant = "default" }: { icon: typeof Server; label: string; value: number | string; to: string; variant?: "default" | "warning" }) {
  return (
    <Link to={to} className="rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/50">
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${variant === "warning" ? "text-destructive" : "text-muted-foreground"}`} />
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
      </div>
      <p className={`mt-2 text-2xl font-bold ${variant === "warning" ? "text-destructive" : ""}`}>{value}</p>
    </Link>
  );
}

function QuickAction({ icon: Icon, label, to }: { icon: typeof Plus; label: string; to: string }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/50"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
        <Icon className="h-5 w-5" />
      </div>
      <span className="text-sm font-medium">{label}</span>
    </Link>
  );
}
