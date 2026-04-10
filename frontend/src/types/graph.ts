export interface SyncStatusData {
  synced: boolean;
  sync_in_progress: boolean;
  last_full_sync: string | null;
  last_incremental_sync: string | null;
  total_assets: number | null;
  total_sensors: number | null;
  total_faults: number | null;
  total_schedules: number | null;
}

export interface SyncResultData {
  status: string;
  records_processed: number;
  error: string | null;
  counts: Record<string, number> | null;
}

export interface GraphInfoData {
  connected: boolean;
  error: string | null;
  total_assets: number | null;
  total_sensors: number | null;
  total_faults: number | null;
  total_maintenanceschedules: number | null;
  total_sensorsummaries: number | null;
  last_full_sync: string | null;
  last_incremental_sync: string | null;
  sync_in_progress: boolean | null;
}
