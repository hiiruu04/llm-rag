export type AssetStatus = "active" | "inactive" | "maintenance" | "decommissioned";

export interface Asset {
  id: string;
  name: string;
  description: string | null;
  asset_type: string;
  parent_id: string | null;
  status: AssetStatus;
  location: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface AssetCreate {
  name: string;
  description?: string;
  asset_type: string;
  parent_id?: string;
  status?: AssetStatus;
  location?: string;
}

export interface AssetUpdate {
  name?: string;
  description?: string;
  asset_type?: string;
  parent_id?: string;
  status?: AssetStatus;
  location?: string;
}

export interface AssetTreeNode {
  id: string;
  name: string;
  asset_type: string;
  status: AssetStatus;
  children: AssetTreeNode[];
}
