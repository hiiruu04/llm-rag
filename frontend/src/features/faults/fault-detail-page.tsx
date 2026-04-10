import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { format } from "date-fns";
import { ArrowLeft, Edit, Unlink, Link2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { useFault, useFaultCauses, useFaultEffects, useUnlinkFault, useLinkFault } from "@/api/faults";

export default function FaultDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: fault, isLoading, isError, error, refetch } = useFault(id!);
  const { data: causes } = useFaultCauses(id!);
  const { data: effects } = useFaultEffects(id!);
  const unlink = useUnlinkFault();

  if (isLoading) return <LoadingState />;
  if (isError || !fault) return <ErrorState message={error?.message} onRetry={() => refetch()} />;

  return (
    <>
      <PageHeader
        title={`[${fault.code}] ${fault.name}`}
        description={fault.description ?? undefined}
        actions={
          <div className="flex gap-2">
            <Link to={`/faults/${id}/edit`} className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
              <Edit className="h-3.5 w-3.5" /> Edit
            </Link>
            <Link to={`/assets/${fault.asset_id}`} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-4 w-4" /> Asset
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <DetailItem label="Code" value={fault.code} />
        <DetailItem label="Severity" value={<StatusBadge value={fault.severity} />} />
        <DetailItem label="Status" value={<StatusBadge value={fault.status} />} />
        <DetailItem label="Detected" value={fault.detected_at ? format(new Date(fault.detected_at), "PPpp") : "-"} />
        <DetailItem label="Resolved" value={fault.resolved_at ? format(new Date(fault.resolved_at), "PPpp") : "-"} />
        <DetailItem label="Asset" value={<Link to={`/assets/${fault.asset_id}`} className="text-primary hover:underline">View Asset</Link>} />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <RelationshipList title="Causes" items={causes} faultId={id!} unlink={unlink} />
        <RelationshipList title="Effects" items={effects} faultId={id!} unlink={unlink} />
      </div>

      <LinkFaultForm faultId={id!} />
    </>
  );
}

function RelationshipList({ title, items, faultId, unlink }: { title: string; items: { id: string; code: string; name: string; severity: string; status: string }[] | undefined; faultId: string; unlink: ReturnType<typeof useUnlinkFault> }) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold">{title} ({items?.length ?? 0})</h3>
      {(items?.length ?? 0) > 0 ? (
        <div className="space-y-2">
          {items!.map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-lg border border-border p-3">
              <div>
                <Link to={`/faults/${item.id}`} className="text-sm font-medium hover:underline">[{item.code}] {item.name}</Link>
                <div className="mt-1 flex gap-2"><StatusBadge value={item.severity} /><StatusBadge value={item.status} /></div>
              </div>
              <button onClick={() => unlink.mutate({ faultId, linkedId: item.id })} className="text-muted-foreground hover:text-destructive">
                <Unlink className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No {title.toLowerCase()} linked</p>
      )}
    </div>
  );
}

function LinkFaultForm({ faultId }: { faultId: string }) {
  const [linkedId, setLinkedId] = useState("");
  const [linkType, setLinkType] = useState<"cause" | "effect">("cause");
  const linkFault = useLinkFault();

  return (
    <div className="mt-8 rounded-lg border border-border p-4">
      <h3 className="mb-3 text-sm font-semibold">Link Fault</h3>
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="mb-1 block text-xs text-muted-foreground">Fault ID</label>
          <input
            value={linkedId}
            onChange={(e) => setLinkedId(e.target.value)}
            placeholder="UUID of fault to link"
            className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Type</label>
          <select value={linkType} onChange={(e) => setLinkType(e.target.value as "cause" | "effect")} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
            <option value="cause">Cause</option>
            <option value="effect">Effect</option>
          </select>
        </div>
        <button
          onClick={() => linkFault.mutate({ faultId, data: { linked_fault_id: linkedId, link_type: linkType } })}
          disabled={!linkedId || linkFault.isPending}
          className="flex items-center gap-1 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
        >
          <Link2 className="h-3.5 w-3.5" /> Link
        </button>
      </div>
    </div>
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
