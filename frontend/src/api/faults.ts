import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Fault, FaultCreate, FaultUpdate, FaultLinkCreate } from "@/types/fault";

export function useFaults(params?: { page?: number; per_page?: number; severity?: string; status?: string }) {
  return useQuery({
    queryKey: ["faults", params],
    queryFn: () => paginatedGet<Fault>("/api/v1/faults", params),
  });
}

export function useAssetFaults(assetId: string, params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["assets", assetId, "faults", params],
    queryFn: () => paginatedGet<Fault>(`/api/v1/assets/${assetId}/faults`, params),
    enabled: !!assetId,
  });
}

export function useFault(id: string) {
  return useQuery({
    queryKey: ["faults", id],
    queryFn: async () => {
      const res = await apiClient.get<Fault>(`/api/v1/faults/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useFaultCauses(id: string) {
  return useQuery({
    queryKey: ["faults", id, "causes"],
    queryFn: async () => {
      const res = await apiClient.get<Fault[]>(`/api/v1/faults/${id}/causes`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useFaultEffects(id: string) {
  return useQuery({
    queryKey: ["faults", id, "effects"],
    queryFn: async () => {
      const res = await apiClient.get<Fault[]>(`/api/v1/faults/${id}/effects`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateFault() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ assetId, data }: { assetId: string; data: FaultCreate }) =>
      apiClient.post<Fault>(`/api/v1/assets/${assetId}/faults`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["faults"] }),
  });
}

export function useUpdateFault() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: FaultUpdate }) =>
      apiClient.put<Fault>(`/api/v1/faults/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["faults"] });
      qc.invalidateQueries({ queryKey: ["faults", vars.id] });
    },
  });
}

export function useDeleteFault() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/faults/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["faults"] }),
  });
}

export function useLinkFault() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ faultId, data }: { faultId: string; data: FaultLinkCreate }) =>
      apiClient.post(`/api/v1/faults/${faultId}/links`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["faults", vars.faultId] });
    },
  });
}

export function useUnlinkFault() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ faultId, linkedId }: { faultId: string; linkedId: string }) =>
      apiClient.delete(`/api/v1/faults/${faultId}/links/${linkedId}`),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["faults", vars.faultId] });
    },
  });
}
