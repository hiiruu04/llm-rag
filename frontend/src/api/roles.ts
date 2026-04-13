import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Role, RoleCreate, RoleUpdate } from "@/types/cmms";

export function useRoles(params?: { page?: number; per_page?: number; name?: string }) {
  return useQuery({
    queryKey: ["roles", params],
    queryFn: () => paginatedGet<Role>("/api/v1/roles", params),
  });
}

export function useRole(id: string) {
  return useQuery({
    queryKey: ["roles", id],
    queryFn: async () => {
      const res = await apiClient.get<Role>(`/api/v1/roles/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: RoleCreate) => apiClient.post<Role>("/api/v1/roles", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useUpdateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RoleUpdate }) =>
      apiClient.put<Role>(`/api/v1/roles/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["roles"] });
      qc.invalidateQueries({ queryKey: ["roles", vars.id] });
    },
  });
}

export function useDeleteRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/roles/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  });
}
