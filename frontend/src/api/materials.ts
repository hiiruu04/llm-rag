import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Material, MaterialCreate, MaterialUpdate } from "@/types/cmms";

export function useMaterials(params?: { page?: number; per_page?: number; part_number?: string }) {
  return useQuery({
    queryKey: ["materials", params],
    queryFn: () => paginatedGet<Material>("/api/v1/materials", params),
  });
}

export function useMaterial(id: string) {
  return useQuery({
    queryKey: ["materials", id],
    queryFn: async () => {
      const res = await apiClient.get<Material>(`/api/v1/materials/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateMaterial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: MaterialCreate) => apiClient.post<Material>("/api/v1/materials", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["materials"] }),
  });
}

export function useUpdateMaterial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: MaterialUpdate }) =>
      apiClient.put<Material>(`/api/v1/materials/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["materials"] });
      qc.invalidateQueries({ queryKey: ["materials", vars.id] });
    },
  });
}

export function useDeleteMaterial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/materials/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["materials"] }),
  });
}
