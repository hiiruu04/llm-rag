import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/common/data-table";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { EmptyState } from "@/components/common/empty-state";
import { StatusBadge } from "@/components/common/status-badge";
import { FilterBar } from "@/components/common/filter-bar";
import { useAssets } from "@/api/assets";
import { apiClient } from "@/lib/api-client";
import type { Fault } from "@/types/fault";

export default function FaultsPage() {
  const navigate = useNavigate();
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { data: assetsData, isLoading: assetsLoading } = useAssets({ per_page: 100 });
  const [allFaults, setAllFaults] = useState<Fault[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!assetsData?.data) return;
    let cancelled = false;
    Promise.all(
      assetsData.data.map(async (asset) => {
        try {
          const res = await apiClient.get<Fault[]>(`/api/v1/assets/${asset.id}/faults`, { params: { page: 1, per_page: 100 } });
          return res.data;
        } catch {
          return [];
        }
      }),
    )
      .then((results) => {
        if (!cancelled) setAllFaults(results.flat());
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load faults");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [assetsData]);

  const filtered = allFaults.filter((f) => {
    if (severityFilter && f.severity !== severityFilter) return false;
    if (statusFilter && f.status !== statusFilter) return false;
    return true;
  });

  if (assetsLoading || loading) return <><PageHeader title="Faults" /><LoadingState /></>;
  if (error) return <><PageHeader title="Faults" /><ErrorState message={error} /></>;

  return (
    <>
      <PageHeader title="Faults" description="All faults across assets" />
      <FilterBar>
        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
          <option value="">All severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </FilterBar>

      {filtered.length > 0 ? (
        <DataTable<Fault>
          data={filtered}
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
      ) : (
        <EmptyState title="No faults found" description="No faults match the current filters." />
      )}
    </>
  );
}
