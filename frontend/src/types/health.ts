export interface HealthData {
  status: string;
  qdrant_connected: boolean;
  openai_connected: boolean;
  postgres_connected: boolean;
  neo4j_connected: boolean;
  collection_info: Record<string, unknown> | null;
  graph_info: Record<string, unknown> | null;
}
