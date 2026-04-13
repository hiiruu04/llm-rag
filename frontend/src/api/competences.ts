import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Competence, CompetenceCreate, CompetenceUpdate } from "@/types/cmms";

export function useCompetences(params?: { page?: number; per_page?: number; category?: string }) {
  return useQuery({
    queryKey: ["competences", params],
    queryFn: () => paginatedGet<Competence>("/api/v1/competences", params),
  });
}

export function useCompetence(id: string) {
  return useQuery({
    queryKey: ["competences", id],
    queryFn: async () => {
      const res = await apiClient.get<Competence>(`/api/v1/competences/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateCompetence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CompetenceCreate) => apiClient.post<Competence>("/api/v1/competences", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["competences"] }),
  });
}

export function useUpdateCompetence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CompetenceUpdate }) =>
      apiClient.put<Competence>(`/api/v1/competences/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["competences"] });
      qc.invalidateQueries({ queryKey: ["competences", vars.id] });
    },
  });
}

export function useDeleteCompetence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/competences/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["competences"] }),
  });
}
