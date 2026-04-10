export type QueryMode = "auto" | "vector" | "graph" | "hybrid";

export interface QueryRequest {
  question: string;
  mode?: QueryMode;
}

export interface Source {
  document_id: string;
  filename: string;
  chunk_index: number;
  similarity_score: number;
  preview_text: string;
}

export interface TokenUsage {
  prompt: number;
  completion: number;
  total: number;
}

export interface QueryData {
  answer: string;
  sources: Source[];
  model_used: string | null;
  tokens_used: TokenUsage | null;
  graph_sources: Record<string, unknown>[] | null;
  cypher_used: string | null;
  mode_used: string | null;
}
