import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { MaintenanceSchedule, ScheduleCreate, ScheduleUpdate } from "@/types/maintenance";

export function useMaintenanceSchedules(params?: {
  page?: number;
  per_page?: number;
  asset_id?: string;
  status?: string;
  maintenance_type?: string;
  priority?: string;
}) {
  return useQuery({
    queryKey: ["maintenance", params],
    queryFn: () => paginatedGet<MaintenanceSchedule>("/api/v1/maintenance-schedules", params),
  });
}

export function useAssetSchedules(assetId: string, params?: { page?: number; per_page?: number; status?: string }) {
  return useQuery({
    queryKey: ["assets", assetId, "maintenance", params],
    queryFn: () => paginatedGet<MaintenanceSchedule>(`/api/v1/assets/${assetId}/maintenance-schedules`, params),
    enabled: !!assetId,
  });
}

export function useSchedule(id: string) {
  return useQuery({
    queryKey: ["maintenance", id],
    queryFn: async () => {
      const res = await apiClient.get<MaintenanceSchedule>(`/api/v1/maintenance-schedules/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useOverdueSchedules(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["maintenance", "overdue", params],
    queryFn: () => paginatedGet<MaintenanceSchedule>("/api/v1/maintenance-schedules/overdue", params),
  });
}

export function useCreateSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ assetId, data }: { assetId: string; data: ScheduleCreate }) =>
      apiClient.post<MaintenanceSchedule>(`/api/v1/assets/${assetId}/maintenance-schedules`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["maintenance"] }),
  });
}

export function useUpdateSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ScheduleUpdate }) =>
      apiClient.put<MaintenanceSchedule>(`/api/v1/maintenance-schedules/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["maintenance"] });
      qc.invalidateQueries({ queryKey: ["maintenance", vars.id] });
    },
  });
}

export function useDeleteSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/maintenance-schedules/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["maintenance"] }),
  });
}

export function useCompleteSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.post(`/api/v1/maintenance-schedules/${id}/complete`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["maintenance"] }),
  });
}

export function useDetectOverdue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post("/api/v1/maintenance-schedules/detect-overdue"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["maintenance"] }),
  });
}
