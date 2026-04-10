import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Asset, AssetCreate, AssetUpdate, AssetTreeNode } from "@/types/asset";

export function useAssets(params?: {
  page?: number;
  per_page?: number;
  status?: string;
  asset_type?: string;
  parent_id?: string;
}) {
  return useQuery({
    queryKey: ["assets", params],
    queryFn: () => paginatedGet<Asset>("/api/v1/assets", params),
  });
}

export function useAsset(id: string) {
  return useQuery({
    queryKey: ["assets", id],
    queryFn: async () => {
      const res = await apiClient.get<Asset>(`/api/v1/assets/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useAssetTree() {
  return useQuery({
    queryKey: ["assets", "tree"],
    queryFn: async () => {
      const res = await apiClient.get<AssetTreeNode[]>("/api/v1/assets/tree");
      return res.data;
    },
  });
}

export function useAssetChildren(id: string, params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["assets", id, "children", params],
    queryFn: () => paginatedGet<Asset>(`/api/v1/assets/${id}/children`, params),
    enabled: !!id,
  });
}

export function useCreateAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AssetCreate) => apiClient.post<Asset>("/api/v1/assets", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assets"] }),
  });
}

export function useUpdateAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AssetUpdate }) =>
      apiClient.put<Asset>(`/api/v1/assets/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["assets"] });
      qc.invalidateQueries({ queryKey: ["assets", vars.id] });
    },
  });
}

export function useDeleteAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/assets/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assets"] }),
  });
}
