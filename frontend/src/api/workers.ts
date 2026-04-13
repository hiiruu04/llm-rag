import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Worker, WorkerCreate, WorkerUpdate } from "@/types/cmms";

export function useWorkers(params?: {
  page?: number;
  per_page?: number;
  status?: string;
  employee_id?: string;
}) {
  return useQuery({
    queryKey: ["workers", params],
    queryFn: () => paginatedGet<Worker>("/api/v1/workers", params),
  });
}

export function useWorker(id: string) {
  return useQuery({
    queryKey: ["workers", id],
    queryFn: async () => {
      const res = await apiClient.get<Worker>(`/api/v1/workers/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useWorkerCompetences(id: string) {
  return useQuery({
    queryKey: ["workers", id, "competences"],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/workers/${id}/competences`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateWorker() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkerCreate) => apiClient.post<Worker>("/api/v1/workers", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workers"] }),
  });
}

export function useUpdateWorker() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkerUpdate }) =>
      apiClient.put<Worker>(`/api/v1/workers/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["workers"] });
      qc.invalidateQueries({ queryKey: ["workers", vars.id] });
    },
  });
}

export function useDeleteWorker() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/workers/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workers"] }),
  });
}
