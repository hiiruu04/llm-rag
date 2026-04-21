import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { QueryData, QueryRequest, AgentQueryRequest } from "@/types/query";

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

export function useGraphRAGQuery() {
  return useMutation({
    mutationFn: async (req: QueryRequest) => {
      const res = await apiClient.post<QueryData>("/api/v1/query/graphrag", req);
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

export function useAgentQuery() {
  return useMutation({
    mutationFn: async (req: AgentQueryRequest) => {
      const res = await apiClient.post<QueryData>("/api/v1/query/agent", req);
      return res.data;
    },
  });
}