import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Sensor, SensorCreate, SensorUpdate } from "@/types/sensor";

export function useAssetSensors(assetId: string, params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["assets", assetId, "sensors", params],
    queryFn: () => paginatedGet<Sensor>(`/api/v1/assets/${assetId}/sensors`, params),
    enabled: !!assetId,
  });
}

export function useSensor(id: string) {
  return useQuery({
    queryKey: ["sensors", id],
    queryFn: async () => {
      const res = await apiClient.get<Sensor>(`/api/v1/sensors/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateSensor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ assetId, data }: { assetId: string; data: SensorCreate }) =>
      apiClient.post<Sensor>(`/api/v1/assets/${assetId}/sensors`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sensors"] }),
  });
}

export function useUpdateSensor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SensorUpdate }) =>
      apiClient.put<Sensor>(`/api/v1/sensors/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sensors"] }),
  });
}

export function useDeleteSensor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: string; assetId: string }) =>
      apiClient.delete(`/api/v1/sensors/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sensors"] }),
  });
}
