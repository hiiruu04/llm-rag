import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/common/data-table";
import { PaginationControls } from "@/components/common/pagination";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { FilterBar } from "@/components/common/filter-bar";
import { useFaults } from "@/api/faults";
import type { Fault } from "@/types/fault";

export default function FaultsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading, isError, error, refetch } = useFaults({
    page,
    per_page: 10,
    severity: severityFilter || undefined,
    status: statusFilter || undefined,
  });

  if (isLoading) return <><PageHeader title="Faults" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Faults" /><ErrorState message={error?.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader title="Faults" description="All faults across assets" />

      <FilterBar>
        <select value={severityFilter} onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
          <option value="">All severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </FilterBar>

      <DataTable<Fault>
        data={data?.data ?? []}
        keyExtractor={(f) => f.id}
        onRowClick={(f) => navigate(`/faults/${f.id}`)}
        columns={[
          { header: "Code", accessor: "code" },
          { header: "Name", accessor: "name" },
          { header: "Severity", accessor: (f) => <StatusBadge value={f.severity} /> },
          { header: "Status", accessor: (f) => <StatusBadge value={f.status} /> },
          {
            header: "Asset",
            accessor: (f) => <Link to={`/assets/${f.asset_id}`} className="text-primary hover:underline" onClick={(e) => e.stopPropagation()}>{f.asset_id.slice(0, 8)}...</Link>,
          },
          {
            header: "Detected",
            accessor: (f) => f.detected_at ? new Date(f.detected_at).toLocaleDateString() : "-",
          },
        ]}
      />
      <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />
    </>
  );
}