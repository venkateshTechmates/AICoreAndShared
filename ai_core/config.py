"""
Configuration Management — Multi-source configuration with priority merging.

Precedence: defaults → YAML → .env → env vars → runtime overrides
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_SENTINEL = object()


class LibConfig(BaseModel):
    """Centralised configuration for AI Core."""

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072

    vector_db: str = "qdrant"
    vector_db_url: str = "http://localhost:6333"
    vector_db_api_key: str | None = None
    vector_db_collection: str = "default"

    chunking_strategy: str = "semantic"
    chunk_size: int = 512
    chunk_overlap: int = 50

    search_strategy: str = "hybrid"
    search_top_k: int = 10

    cache_enabled: bool = True
    cache_ttl: int = 3600

    log_level: str = "INFO"
    tracing_enabled: bool = False
    tracing_provider: str | None = None

    api_keys: dict[str, str] = Field(default_factory=dict)

    _extra: dict[str, Any] = {}

    # ── Factory Methods ──────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> LibConfig:
        """Build config from environment variables with AI_CORE_ prefix."""
        mapping: dict[str, str] = {}
        prefix = "AI_CORE_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                field = key[len(prefix):].lower()
                mapping[field] = value
        return cls(**{k: v for k, v in mapping.items() if k in cls.model_fields})

    @classmethod
    def from_yaml(cls, path: str | Path) -> LibConfig:
        """Load config from a YAML file."""
        import yaml  # type: ignore[import-untyped]

        data = Path(path).read_text(encoding="utf-8")
        parsed: dict[str, Any] = yaml.safe_load(data) or {}
        flat = cls._flatten(parsed)
        return cls(**{k: v for k, v in flat.items() if k in cls.model_fields})

    @classmethod
    def from_vault(cls, secret_path: str, *, url: str | None = None, token: str | None = None) -> LibConfig:
        """Load config from HashiCorp Vault KV store."""
        import hvac  # type: ignore[import-untyped]

        client = hvac.Client(
            url=url or os.environ.get("VAULT_ADDR", "http://localhost:8200"),
            token=token or os.environ.get("VAULT_TOKEN", ""),
        )
        secret = client.secrets.kv.v2.read_secret_version(path=secret_path)
        data: dict[str, Any] = secret["data"]["data"]
        return cls(**{k: v for k, v in data.items() if k in cls.model_fields})

    @classmethod
    def from_aws_secrets(cls, secret_name: str, *, region: str = "us-east-1") -> LibConfig:
        """Load config from AWS Secrets Manager."""
        import json

        import boto3  # type: ignore[import-untyped]

        client = boto3.client("secretsmanager", region_name=region)
        resp = client.get_secret_value(SecretId=secret_name)
        data: dict[str, Any] = json.loads(resp["SecretString"])
        return cls(**{k: v for k, v in data.items() if k in cls.model_fields})

    # ── Instance Methods ─────────────────────────────────────────────────

    def override(self, **kwargs: Any) -> LibConfig:
        """Return a copy with the given overrides applied."""
        return self.model_copy(update=kwargs)

    def get(self, key: str, default: Any = _SENTINEL) -> Any:
        """Get a config value by key name."""
        if key in self.model_fields:
            return getattr(self, key)
        if default is not _SENTINEL:
            return default
        raise KeyError(f"Unknown config key: {key}")

    # ── Internal ─────────────────────────────────────────────────────────

    @staticmethod
    def _flatten(d: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(LibConfig._flatten(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
