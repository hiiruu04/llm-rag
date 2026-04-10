import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { SyncStatusData, SyncResultData, GraphInfoData } from "@/types/graph";

export function useSyncStatus() {
  return useQuery({
    queryKey: ["graph", "sync-status"],
    queryFn: async () => {
      const res = await apiClient.get<SyncStatusData>("/api/v1/admin/graph/sync/status");
      return res.data;
    },
  });
}

export function useGraphInfo() {
  return useQuery({
    queryKey: ["graph", "info"],
    queryFn: async () => {
      const res = await apiClient.get<GraphInfoData>("/api/v1/graph/info");
      return res.data;
    },
  });
}

export function useFullSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<SyncResultData>("/api/v1/admin/graph/sync/full"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["graph"] }),
  });
}

export function useIncrementalSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<SyncResultData>("/api/v1/admin/graph/sync/incremental"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["graph"] }),
  });
}
