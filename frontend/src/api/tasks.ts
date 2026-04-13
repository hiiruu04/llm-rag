import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Task, TaskCreate, TaskUpdate, TaskCompetenceAdd, TaskMaterialAdd } from "@/types/cmms";

export function useTasks(params?: {
  page?: number;
  per_page?: number;
  status?: string;
  task_type?: string;
}) {
  return useQuery({
    queryKey: ["tasks", params],
    queryFn: () => paginatedGet<Task>("/api/v1/tasks", params),
  });
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ["tasks", id],
    queryFn: async () => {
      const res = await apiClient.get<Task>(`/api/v1/tasks/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) => apiClient.post<Task>("/api/v1/tasks", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskUpdate }) =>
      apiClient.put<Task>(`/api/v1/tasks/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["tasks", vars.id] });
    },
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/tasks/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useAddTaskCompetence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskCompetenceAdd }) =>
      apiClient.post(`/api/v1/tasks/${id}/competences`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["tasks", vars.id] });
    },
  });
}

export function useAddTaskMaterial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskMaterialAdd }) =>
      apiClient.post(`/api/v1/tasks/${id}/materials`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["tasks", vars.id] });
    },
  });
}
