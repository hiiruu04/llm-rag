import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { DownEvent, DownEventCreate, DownEventUpdate, DownEventStatistics } from "@/types/cmms";

export function useDownEvents(params?: {
  page?: number;
  per_page?: number;
  severity?: string;
  status?: string;
  asset_id?: string;
}) {
  return useQuery({
    queryKey: ["down-events", params],
    queryFn: () => paginatedGet<DownEvent>("/api/v1/down-events", params),
  });
}

export function useDownEvent(id: string) {
  return useQuery({
    queryKey: ["down-events", id],
    queryFn: async () => {
      const res = await apiClient.get<DownEvent>(`/api/v1/down-events/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useDownEventStatistics() {
  return useQuery({
    queryKey: ["down-events", "statistics"],
    queryFn: async () => {
      const res = await apiClient.get<DownEventStatistics>("/api/v1/down-events/statistics");
      return res.data;
    },
  });
}

export function useCreateDownEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: DownEventCreate) => apiClient.post<DownEvent>("/api/v1/down-events", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["down-events"] }),
  });
}

export function useUpdateDownEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DownEventUpdate }) =>
      apiClient.put<DownEvent>(`/api/v1/down-events/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["down-events"] });
      qc.invalidateQueries({ queryKey: ["down-events", vars.id] });
    },
  });
}

export function useDeleteDownEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/down-events/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["down-events"] }),
  });
}
