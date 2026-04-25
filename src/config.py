"""Centralized configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All app settings, validated at load time."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    groq_api_key: str = Field(..., description="Groq API key")
    groq_model: str = Field(default="llama-3.3-70b-versatile")

    # --- Vector Store ---
    vector_store: str = "pinecone"  # or "qdrant"
    pinecone_api_key: str
    pinecone_index_name: str = "recon-v1"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"


# Singleton instance — import this elsewhere
settings = Settings()