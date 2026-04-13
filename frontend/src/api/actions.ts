import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Action, ActionCreate, ActionUpdate } from "@/types/cmms";

export function useActions(params?: { page?: number; per_page?: number; action_type?: string }) {
  return useQuery({
    queryKey: ["actions", params],
    queryFn: () => paginatedGet<Action>("/api/v1/actions", params),
  });
}

export function useAction(id: string) {
  return useQuery({
    queryKey: ["actions", id],
    queryFn: async () => {
      const res = await apiClient.get<Action>(`/api/v1/actions/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ActionCreate) => apiClient.post<Action>("/api/v1/actions", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["actions"] }),
  });
}

export function useUpdateAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ActionUpdate }) =>
      apiClient.put<Action>(`/api/v1/actions/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["actions"] });
      qc.invalidateQueries({ queryKey: ["actions", vars.id] });
    },
  });
}

export function useDeleteAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/actions/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["actions"] }),
  });
}
