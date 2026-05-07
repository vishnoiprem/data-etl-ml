"""Centralized settings via pydantic-settings.

Reads from .env and environment. All knobs in one place; nothing hardcoded.
"""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Mode
    AI_ENGINEERING_MODE: str = "LOCAL"

    # AWS
    AWS_REGION: str = "us-east-1"
    OPENSEARCH_ENDPOINT: str = ""
    OPENSEARCH_INDEX: str = "chunks_v1"
    BEDROCK_EMBEDDING_MODEL: str = "amazon.titan-embed-text-v2:0"
    BEDROCK_GENERATION_MODEL: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    BEDROCK_RERANK_MODEL: str = "cohere.rerank-v3-5:0"

    # Local
    LOCAL_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LOCAL_RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # RAG knobs
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    RETRIEVE_TOP_K: int = 50
    RERANK_TOP_K: int = 5
    REFUSAL_SCORE_THRESHOLD: float = 0.05

    # Paths
    DATA_DIR: Path = PROJECT_ROOT / "data"
    SAMPLE_DATA_DIR: Path = PROJECT_ROOT / "sample_data" / "docs"
    INDEX_DIR: Path = PROJECT_ROOT / "data" / "index"

    @property
    def is_aws(self) -> bool:
        return self.AI_ENGINEERING_MODE.upper() == "AWS"


settings = Settings()
settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
