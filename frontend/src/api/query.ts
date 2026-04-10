import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { QueryRequest, QueryData } from "@/types/query";

export function useQueryRAG() {
  return useMutation({
    mutationFn: async (req: QueryRequest) => {
      const res = await apiClient.post<QueryData>("/api/v1/query", req);
      return res.data;
    },
  });
}

export function useGraphQuery() {
  return useMutation({
    mutationFn: async (req: QueryRequest) => {
      const res = await apiClient.post<QueryData>("/api/v1/query/graph", req);
      return res.data;
    },
  });
}

export function useHybridQuery() {
  return useMutation({
    mutationFn: async (req: QueryRequest) => {
      const res = await apiClient.post<QueryData>("/api/v1/query/hybrid", req);
      return res.data;
    },
  });
}
