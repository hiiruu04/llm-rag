import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { HealthData } from "@/types/health";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await apiClient.get<HealthData>("/api/v1/health");
      return res.data;
    },
    refetchInterval: 30_000,
  });
}
