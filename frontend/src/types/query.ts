export type QueryMode = "auto" | "vector" | "graph" | "graphrag" | "hybrid" | "agent";

export type AgentType = "scheduling" | "competency" | "analyzer" | "recommender";

export interface QueryRequest {
  question: string;
  mode?: QueryMode;
  session_id?: string;
}

export interface AgentQueryRequest {
  question: string;
  agent_type?: AgentType;
  session_id?: string;
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

export interface GraphEntity {
  name: string;
  entity_type: string;
  description: string;
}

export interface CMMSReference {
  entity_name: string;
  cmms_label: string;
  cmms_name: string;
  cmms_pg_id: number;
}

export interface QueryData {
  answer: string;
  sources: Source[];
  model_used: string | null;
  tokens_used: TokenUsage | null;
  graph_sources: Record<string, unknown>[] | null;
  cypher_used: string | null;
  mode_used: string | null;
  graph_entities: GraphEntity[] | null;
  cmms_references: CMMSReference[] | null;
  agent_used: string | null;
  session_id: string | null;
}