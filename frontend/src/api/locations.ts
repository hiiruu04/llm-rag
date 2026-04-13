import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Location, LocationCreate, LocationUpdate, LocationTreeNode } from "@/types/cmms";

export function useLocations(params?: {
  page?: number;
  per_page?: number;
  location_type?: string;
  parent_id?: string;
}) {
  return useQuery({
    queryKey: ["locations", params],
    queryFn: () => paginatedGet<Location>("/api/v1/locations", params),
  });
}

export function useLocation(id: string) {
  return useQuery({
    queryKey: ["locations", id],
    queryFn: async () => {
      const res = await apiClient.get<Location>(`/api/v1/locations/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useLocationTree() {
  return useQuery({
    queryKey: ["locations", "tree"],
    queryFn: async () => {
      const res = await apiClient.get<LocationTreeNode[]>("/api/v1/locations/tree");
      return res.data;
    },
  });
}

export function useLocationChildren(id: string, params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["locations", id, "children", params],
    queryFn: () => paginatedGet<Location>(`/api/v1/locations/${id}/children`, params),
    enabled: !!id,
  });
}

export function useCreateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: LocationCreate) => apiClient.post<Location>("/api/v1/locations", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["locations"] }),
  });
}

export function useUpdateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: LocationUpdate }) =>
      apiClient.put<Location>(`/api/v1/locations/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["locations"] });
      qc.invalidateQueries({ queryKey: ["locations", vars.id] });
    },
  });
}

export function useDeleteLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/locations/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["locations"] }),
  });
}
