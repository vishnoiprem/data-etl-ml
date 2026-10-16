"""Env-driven settings (pydantic-settings BaseSettings).

All secrets, hosts, and tunable limits live here. The `.env` file is read
at startup; missing keys fall back to safe dev defaults. Production
deploys MUST override `api_keys` and `postgres_url`.

Env vars are prefixed with `APEX_` to avoid collisions with other tools
in the process tree. Example: `APEX_API_KEYS=key1,key2`.

The auth layer reads `settings.api_keys_list`; the audit queue reads
`settings.audit_queue_max`; the retriever reads `settings.max_query_chars`
via the FastAPI dep tree.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Loaded once at startup, cached for the process."""

    model_config = SettingsConfigDict(
        env_prefix="APEX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Auth ---
    # Comma-separated. Empty = no keys configured = all requests 403.
    api_keys: str = ""

    # --- Infra endpoints ---
    qdrant_url: str = "http://localhost:6333"
    es_url: str = "http://localhost:9200"
    # Empty = JSONL fallback for the eval store (dev / single-node).
    # Set `postgresql+psycopg://user:pass@host:5432/apex` for prod.
    postgres_url: str = ""
    model_gateway_url: str = ""
    model_gateway_key: str = ""

    # --- Web ---
    # Allowed CORS origin for the Next.js frontend. NEVER use `*` here.
    frontend_origin: str = "http://localhost:3000"

    # --- Tunables ---
    # Bounded queue for the audit log writer. If full, requests drop with
    # a counter (we never block the request path on disk I/O).
    audit_queue_max: int = 10_000
    # Hard cap on `/query` body length. 10 MB queries are a 403 risk.
    max_query_chars: int = 2_000
    # Readiness probe timeout per dependency. K8s uses 1s; we want margin.
    readyz_timeout_ms: int = 500

    @property
    def api_keys_list(self) -> list[str]:
        """Parse the comma-separated `api_keys` env into a list of trimmed keys."""
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """FastAPI dep. Cached so we read `.env` once per process."""
    return Settings()
