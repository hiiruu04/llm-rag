import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ChatSession, ChatSessionDetail, ChatSessionCreate, ChatSessionUpdate } from "@/types/chat";

export function useChatSessions(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["chat-sessions", page, perPage],
    queryFn: async () => {
      const res = await apiClient.get<{ data: ChatSession[]; meta: { pagination?: { total: number } } }>(
        "/api/v1/chats",
        { params: { page, per_page: perPage } },
      );
      return {
        sessions: res.data.data ?? res.data as unknown as ChatSession[],
        total: res.data.meta?.pagination?.total ?? 0,
      };
    },
  });
}

export function useChatSession(sessionId: string | null) {
  return useQuery({
    queryKey: ["chat-session", sessionId],
    queryFn: async () => {
      if (!sessionId) return null;
      const res = await apiClient.get<ChatSessionDetail>(`/api/v1/chats/${sessionId}`);
      return res.data;
    },
    enabled: !!sessionId,
  });
}

export function useCreateChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ChatSessionCreate) => {
      const res = await apiClient.post<ChatSession>("/api/v1/chats", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
  });
}

export function useUpdateChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sessionId, data }: { sessionId: string; data: ChatSessionUpdate }) => {
      const res = await apiClient.patch<ChatSession>(`/api/v1/chats/${sessionId}`, data);
      return res.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      queryClient.invalidateQueries({ queryKey: ["chat-session", variables.sessionId] });
    },
  });
}

export function useDeleteChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) => {
      await apiClient.delete(`/api/v1/chats/${sessionId}`);
      return sessionId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
  });
}

export function useChatMessages(sessionId: string | null, limit = 50, offset = 0) {
  return useQuery({
    queryKey: ["chat-messages", sessionId, limit, offset],
    queryFn: async () => {
      if (!sessionId) return { messages: [], total: 0 };
      const res = await apiClient.get<{ data: import("@/types/chat").ChatMessage[]; meta: { pagination?: { total: number } } }>(
        `/api/v1/chats/${sessionId}/messages`,
        { params: { limit, offset } },
      );
      return {
        messages: res.data.data ?? res.data as unknown as import("@/types/chat").ChatMessage[],
        total: res.data.meta?.pagination?.total ?? 0,
      };
    },
    enabled: !!sessionId,
  });
}