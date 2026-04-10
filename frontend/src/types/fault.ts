export type FaultSeverity = "low" | "medium" | "high" | "critical";
export type FaultStatus = "open" | "investigating" | "resolved" | "closed";
export type FaultLinkType = "cause" | "effect";

export interface Fault {
  id: string;
  asset_id: string;
  code: string;
  name: string;
  description: string | null;
  severity: FaultSeverity;
  status: FaultStatus;
  detected_at: string | null;
  resolved_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface FaultCreate {
  code: string;
  name: string;
  description?: string;
  severity?: FaultSeverity;
  status?: FaultStatus;
  detected_at?: string;
  resolved_at?: string;
}

export interface FaultUpdate {
  code?: string;
  name?: string;
  description?: string;
  severity?: FaultSeverity;
  status?: FaultStatus;
  detected_at?: string;
  resolved_at?: string;
}

export interface FaultLinkCreate {
  linked_fault_id: string;
  link_type: FaultLinkType;
}
