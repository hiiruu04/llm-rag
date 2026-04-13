import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Aggregate, AggregateCreate, AggregateUpdate } from "@/types/cmms";

export function useAggregates(params?: { page?: number; per_page?: number; name?: string }) {
  return useQuery({
    queryKey: ["aggregates", params],
    queryFn: () => paginatedGet<Aggregate>("/api/v1/aggregates", params),
  });
}

export function useAggregate(id: string) {
  return useQuery({
    queryKey: ["aggregates", id],
    queryFn: async () => {
      const res = await apiClient.get<Aggregate>(`/api/v1/aggregates/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateAggregate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AggregateCreate) => apiClient.post<Aggregate>("/api/v1/aggregates", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aggregates"] }),
  });
}

export function useUpdateAggregate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AggregateUpdate }) =>
      apiClient.put<Aggregate>(`/api/v1/aggregates/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["aggregates"] });
      qc.invalidateQueries({ queryKey: ["aggregates", vars.id] });
    },
  });
}

export function useDeleteAggregate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/aggregates/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aggregates"] }),
  });
}
