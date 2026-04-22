export interface ChatSession {
  id: string;
  title: string | null;
  mode: string;
  message_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata_: Record<string, unknown> | null;
  created_at: string | null;
}

export interface ChatSessionDetail {
  id: string;
  title: string | null;
  mode: string;
  messages: ChatMessage[];
  created_at: string | null;
  updated_at: string | null;
}

export interface ChatSessionCreate {
  title?: string;
  mode?: "auto" | "vector" | "graph" | "graphrag" | "hybrid" | "agent";
}

export interface ChatSessionUpdate {
  title?: string;
}