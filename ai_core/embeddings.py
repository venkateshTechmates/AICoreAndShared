"""
Embedding Abstraction — Unified interface for embedding models.

Supports: OpenAI, Cohere, HuggingFace, Bedrock, Vertex AI, BGE, Jina
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from ai_core.schemas import EmbeddingConfig, EmbeddingProvider


class BaseEmbedding(ABC):
    """Abstract base for all embedding providers."""

    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

    async def embed_batch(
        self,
        texts: list[str],
        *,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """Embed multiple texts with automatic batching."""
        results: list[list[float]] = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]
            batch_results = await self._embed_batch_impl(batch)
            results.extend(batch_results)
        return results

    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]

    async def embed_documents(
        self,
        documents: list[dict[str, Any]],
        *,
        text_key: str = "text",
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        """Embed documents and return them with their vectors attached."""
        texts = [doc[text_key] for doc in documents]
        vectors = await self.embed_batch(texts)
        enriched: list[dict[str, Any]] = []
        for doc, vec in zip(documents, vectors):
            entry: dict[str, Any] = {"vector": vec}
            if include_metadata:
                entry.update(doc)
            else:
                entry["text"] = doc[text_key]
            enriched.append(entry)
        return enriched


# ── Implementations ──────────────────────────────────────────────────────────


class OpenAIEmbedding(BaseEmbedding):
    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        import openai  # type: ignore[import-untyped]

        self._client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.embeddings.create(
            model=self.config.model,
            input=text,
            dimensions=self.config.dimensions,
        )
        return resp.data[0].embedding

    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(
            model=self.config.model,
            input=texts,
            dimensions=self.config.dimensions,
        )
        return [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]


class CohereEmbedding(BaseEmbedding):
    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        import cohere  # type: ignore[import-untyped]

        self._client = cohere.AsyncClientV2(api_key=config.api_key)

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.embed(
            texts=[text],
            model=self.config.model,
            input_type="search_document",
            embedding_types=["float"],
        )
        return list(resp.embeddings.float_[0])

    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embed(
            texts=texts,
            model=self.config.model,
            input_type="search_document",
            embedding_types=["float"],
        )
        return [list(e) for e in resp.embeddings.float_]


class HuggingFaceEmbedding(BaseEmbedding):
    """Local Sentence Transformers embedding."""

    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

        self._model = SentenceTransformer(config.model)

    async def embed(self, text: str) -> list[float]:
        import asyncio

        loop = asyncio.get_event_loop()
        vec = await loop.run_in_executor(None, self._model.encode, text)
        return vec.tolist()

    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]:
        import asyncio

        loop = asyncio.get_event_loop()
        vecs = await loop.run_in_executor(None, self._model.encode, texts)
        return vecs.tolist()


class BedrockEmbedding(BaseEmbedding):
    """AWS Bedrock embedding (Titan, Cohere on AWS)."""

    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        import boto3  # type: ignore[import-untyped]

        self._client = boto3.client(
            "bedrock-runtime",
            region_name=config.base_url or "us-east-1",
        )

    async def embed(self, text: str) -> list[float]:
        import asyncio
        import json

        body = json.dumps({"inputText": text})

        def _invoke() -> list[float]:
            resp = self._client.invoke_model(
                modelId=self.config.model,
                body=body,
                contentType="application/json",
            )
            result = json.loads(resp["body"].read())
            return result.get("embedding", [])

        return await asyncio.get_event_loop().run_in_executor(None, _invoke)

    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class VertexAIEmbedding(BaseEmbedding):
    """Google Vertex AI / GenAI text embeddings."""

    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)

    async def embed(self, text: str) -> list[float]:
        import asyncio

        def _invoke() -> list[float]:
            import google.generativeai as genai  # type: ignore[import-untyped]

            genai.configure(api_key=self.config.api_key)
            result = genai.embed_content(
                model=self.config.model,
                content=text,
            )
            return list(result["embedding"])

        return await asyncio.get_event_loop().run_in_executor(None, _invoke)

    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]:
        import asyncio

        def _invoke() -> list[list[float]]:
            import google.generativeai as genai  # type: ignore[import-untyped]

            genai.configure(api_key=self.config.api_key)
            result = genai.embed_content(
                model=self.config.model,
                content=texts,
            )
            return [list(e) for e in result["embedding"]]

        return await asyncio.get_event_loop().run_in_executor(None, _invoke)


class BGEEmbedding(BaseEmbedding):
    """BGE (BAAI General Embedding) using Sentence Transformers locally."""

    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

        self._model = SentenceTransformer(config.model or "BAAI/bge-large-en-v1.5")

    async def embed(self, text: str) -> list[float]:
        import asyncio

        vec = await asyncio.get_event_loop().run_in_executor(
            None, self._model.encode, text
        )
        return vec.tolist()

    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]:
        import asyncio

        vecs = await asyncio.get_event_loop().run_in_executor(
            None, self._model.encode, texts
        )
        return vecs.tolist()


class JinaEmbedding(BaseEmbedding):
    """Jina AI embedding API — high-quality multilingual embeddings."""

    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        self._api_key = config.api_key or ""
        self._model = config.model or "jina-embeddings-v3"
        self._base_url = config.base_url or "https://api.jina.ai/v1"

    async def embed(self, text: str) -> list[float]:
        result = await self._embed_batch_impl([text])
        return result[0]

    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]:
        import httpx

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": texts,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]


# ── Factory ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, type[BaseEmbedding]] = {
    "openai": OpenAIEmbedding,
    "azure": OpenAIEmbedding,
    "cohere": CohereEmbedding,
    "huggingface": HuggingFaceEmbedding,
    "bedrock": BedrockEmbedding,
    "vertex_ai": VertexAIEmbedding,
    "bge": BGEEmbedding,
    "jina": JinaEmbedding,
}


class EmbeddingFactory:
    """Create embedding instances by provider name."""

    @staticmethod
    def create(
        provider: str,
        model: str,
        config: EmbeddingConfig | None = None,
    ) -> BaseEmbedding:
        if config is None:
            config = EmbeddingConfig(provider=EmbeddingProvider(provider), model=model)
        else:
            config = config.model_copy(update={"model": model})
        cls = _REGISTRY.get(provider.lower())
        if cls is None:
            raise ValueError(f"Unsupported embedding provider: {provider}")
        return cls(config)

    @staticmethod
    def register(provider: str, cls: type[BaseEmbedding]) -> None:
        _REGISTRY[provider.lower()] = cls
