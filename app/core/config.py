from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    openai_api_key: str
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


settings = Settings()
