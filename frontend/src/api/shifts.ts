import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Shift, ShiftCreate, ShiftUpdate } from "@/types/cmms";

export function useShifts(params?: { page?: number; per_page?: number; name?: string }) {
  return useQuery({
    queryKey: ["shifts", params],
    queryFn: () => paginatedGet<Shift>("/api/v1/shifts", params),
  });
}

export function useShift(id: string) {
  return useQuery({
    queryKey: ["shifts", id],
    queryFn: async () => {
      const res = await apiClient.get<Shift>(`/api/v1/shifts/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateShift() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ShiftCreate) => apiClient.post<Shift>("/api/v1/shifts", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shifts"] }),
  });
}

export function useUpdateShift() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ShiftUpdate }) =>
      apiClient.put<Shift>(`/api/v1/shifts/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["shifts"] });
      qc.invalidateQueries({ queryKey: ["shifts", vars.id] });
    },
  });
}

export function useDeleteShift() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/shifts/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shifts"] }),
  });
}
