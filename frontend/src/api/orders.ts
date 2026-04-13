import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, paginatedGet } from "@/lib/api-client";
import type { Order, OrderCreate, OrderUpdate } from "@/types/cmms";

export function useOrders(params?: {
  page?: number;
  per_page?: number;
  status?: string;
  order_type?: string;
  priority?: string;
}) {
  return useQuery({
    queryKey: ["orders", params],
    queryFn: () => paginatedGet<Order>("/api/v1/orders", params),
  });
}

export function useOrder(id: string) {
  return useQuery({
    queryKey: ["orders", id],
    queryFn: async () => {
      const res = await apiClient.get<Order>(`/api/v1/orders/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: OrderCreate) => apiClient.post<Order>("/api/v1/orders", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["orders"] }),
  });
}

export function useUpdateOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: OrderUpdate }) =>
      apiClient.put<Order>(`/api/v1/orders/${id}`, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["orders", vars.id] });
    },
  });
}

export function useDeleteOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/orders/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["orders"] }),
  });
}
