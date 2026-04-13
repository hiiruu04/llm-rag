import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { System, SystemCreate, SystemUpdate } from "@/types/cmms";

export function useSystems(params?: { page?: number; per_page?: number; name?: string }) {
  return useQuery({
    queryKey: ["systems", params],
    queryFn: () => paginatedGet<System>("/api/v1/systems", params),
  });
}

export function useSystem(id: string) {
  return useQuery({
    queryKey: ["systems", id],
    queryFn: async () => {
      const res = await apiClient.get<System>(`/api/v1/systems/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateSystem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SystemCreate) => apiClient.post<System>("/api/v1/systems", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["systems"] }),
  });
}

export function useUpdateSystem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SystemUpdate }) =>
      apiClient.put<System>(`/api/v1/systems/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["systems"] });
      qc.invalidateQueries({ queryKey: ["systems", vars.id] });
    },
  });
}

export function useDeleteSystem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/systems/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["systems"] }),
  });
}
