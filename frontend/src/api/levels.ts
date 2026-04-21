import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Competence, Level, LevelCreate, LevelUpdate } from "@/types/cmms";

export function useLevels(params?: { page?: number; per_page?: number; name?: string; role_id?: string }) {
  return useQuery({
    queryKey: ["levels", params],
    queryFn: () => paginatedGet<Level>("/api/v1/levels", params),
  });
}

export function useLevel(id: string) {
  return useQuery({
    queryKey: ["levels", id],
    queryFn: async () => {
      const res = await apiClient.get<Level>(`/api/v1/levels/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useLevelCompetences(id: string) {
  return useQuery({
    queryKey: ["levels", id, "competences"],
    queryFn: async () => {
      const res = await apiClient.get<Competence[]>(`/api/v1/levels/${id}/competences`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateLevel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: LevelCreate) => apiClient.post<Level>("/api/v1/levels", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["levels"] }),
  });
}

export function useUpdateLevel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: LevelUpdate }) =>
      apiClient.put<Level>(`/api/v1/levels/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["levels"] });
      qc.invalidateQueries({ queryKey: ["levels", vars.id] });
    },
  });
}

export function useDeleteLevel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/levels/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["levels"] }),
  });
}
