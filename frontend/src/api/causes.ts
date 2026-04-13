import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Cause, CauseCreate, CauseUpdate } from "@/types/cmms";

export function useCauses(params?: {
  page?: number;
  per_page?: number;
  category?: string;
  severity?: string;
}) {
  return useQuery({
    queryKey: ["causes", params],
    queryFn: () => paginatedGet<Cause>("/api/v1/causes", params),
  });
}

export function useCause(id: string) {
  return useQuery({
    queryKey: ["causes", id],
    queryFn: async () => {
      const res = await apiClient.get<Cause>(`/api/v1/causes/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateCause() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CauseCreate) => apiClient.post<Cause>("/api/v1/causes", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["causes"] }),
  });
}

export function useUpdateCause() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CauseUpdate }) =>
      apiClient.put<Cause>(`/api/v1/causes/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["causes"] });
      qc.invalidateQueries({ queryKey: ["causes", vars.id] });
    },
  });
}

export function useDeleteCause() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/causes/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["causes"] }),
  });
}
