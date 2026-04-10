import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { SensorData, SensorDataCreate, SensorDataBatchCreate, BatchInsertResponse, DeletedCountResponse } from "@/types/sensor-data";

export function useSensorData(
  sensorId: string,
  params?: { page?: number; per_page?: number; start_time?: string; end_time?: string },
) {
  return useQuery({
    queryKey: ["sensors", sensorId, "data", params],
    queryFn: () => paginatedGet<SensorData>(`/api/v1/sensors/${sensorId}/data`, params),
    enabled: !!sensorId,
  });
}

export function useLatestSensorData(sensorId: string) {
  return useQuery({
    queryKey: ["sensors", sensorId, "data", "latest"],
    queryFn: async () => {
      const res = await apiClient.get<SensorData>(`/api/v1/sensors/${sensorId}/data/latest`);
      return res.data;
    },
    enabled: !!sensorId,
  });
}

export function useCreateSensorData() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sensorId, data }: { sensorId: string; data: SensorDataCreate }) =>
      apiClient.post(`/api/v1/sensors/${sensorId}/data`, data),
    onSuccess: (_res, vars) => qc.invalidateQueries({ queryKey: ["sensors", vars.sensorId, "data"] }),
  });
}

export function useBatchInsertSensorData() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sensorId, data }: { sensorId: string; data: SensorDataBatchCreate }) =>
      apiClient.post<BatchInsertResponse>(`/api/v1/sensors/${sensorId}/data/batch`, data),
    onSuccess: (_res, vars) => qc.invalidateQueries({ queryKey: ["sensors", vars.sensorId, "data"] }),
  });
}

export function useDeleteSensorData() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sensorId, start_time, end_time }: { sensorId: string; start_time: string; end_time: string }) =>
      apiClient.delete<DeletedCountResponse>(`/api/v1/sensors/${sensorId}/data`, { params: { start_time, end_time } }),
    onSuccess: (_res, vars) => qc.invalidateQueries({ queryKey: ["sensors", vars.sensorId, "data"] }),
  });
}
