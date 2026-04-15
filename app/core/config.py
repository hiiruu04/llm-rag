from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    openai_api_key: str
    openai_base_url: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "documents"
    qdrant_vector_size: int = 1536

    chunk_size: int = 512
    chunk_overlap: int = 50
    max_file_size_mb: int = 10

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    default_top_k: int = 5
    similarity_threshold: float = 0.7

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "llm_rag"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password123"
    neo4j_database: str = "neo4j"

    # MCP Server
    mcp_server_enabled: bool = True
    mcp_api_key: str = ""

    # MCP Client
    mcp_client_enabled: bool = False
    mcp_client_servers: str = "[]"  # JSON array of {name, url, api_key?}

    # GraphRAG
    graphrag_enabled: bool = True
    graphrag_max_entities_per_chunk: int = 20
    graphrag_neighborhood_hops: int = 2

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return self.database_url


settings = Settings()
