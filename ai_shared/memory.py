"""
Memory & State Management — 6 memory types for conversational and long-term storage.

Types: buffer, summary, vector, redis, postgres, entity
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
from typing import Any


class BaseMemory(ABC):
    """Abstract base for all memory implementations."""

    @abstractmethod
    async def add(self, role: str, content: str, **kwargs: Any) -> None:
        ...

    @abstractmethod
    async def get(self, **kwargs: Any) -> list[dict[str, str]]:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...

    async def search(self, query: str, *, top_k: int = 5) -> list[dict[str, Any]]:
        """Semantic search over memory (override in vector-backed memories)."""
        return []


class ConversationBufferMemory(BaseMemory):
    """Full conversation history with optional turn limit."""

    def __init__(self, *, max_turns: int | None = None, return_messages: bool = True) -> None:
        self.max_turns = max_turns
        self.return_messages = return_messages
        self._history: deque[dict[str, str]] = deque(maxlen=max_turns * 2 if max_turns else None)

    async def add(self, role: str, content: str, **kwargs: Any) -> None:
        self._history.append({"role": role, "content": content})

    async def get(self, **kwargs: Any) -> list[dict[str, str]]:
        return list(self._history)

    async def clear(self) -> None:
        self._history.clear()


class ConversationSummaryMemory(BaseMemory):
    """LLM-compressed conversation memory."""

    def __init__(self, llm: Any = None, *, max_summary_tokens: int = 500) -> None:
        self.llm = llm
        self.max_summary_tokens = max_summary_tokens
        self._summary: str = ""
        self._buffer: list[dict[str, str]] = []

    async def add(self, role: str, content: str, **kwargs: Any) -> None:
        self._buffer.append({"role": role, "content": content})
        if len(self._buffer) >= 10 and self.llm:
            await self._compress()

    async def _compress(self) -> None:
        if not self.llm:
            return
        history_text = "\n".join(f"{m['role']}: {m['content']}" for m in self._buffer)
        resp = await self.llm.generate(
            f"Summarize this conversation in under {self.max_summary_tokens} tokens:\n\n"
            f"Previous summary: {self._summary}\n\nRecent:\n{history_text}"
        )
        self._summary = resp.text
        self._buffer.clear()

    async def get(self, **kwargs: Any) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if self._summary:
            messages.append({"role": "system", "content": f"Conversation summary: {self._summary}"})
        messages.extend(self._buffer)
        return messages

    async def clear(self) -> None:
        self._summary = ""
        self._buffer.clear()


class VectorMemory(BaseMemory):
    """Semantic long-term memory backed by a vector store."""

    def __init__(
        self,
        store: Any,
        embedder: Any,
        *,
        top_k: int = 5,
        relevance_threshold: float = 0.7,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.top_k = top_k
        self.relevance_threshold = relevance_threshold
        self._recent: list[dict[str, str]] = []

    async def add(self, role: str, content: str, **kwargs: Any) -> None:
        from ai_core.schemas import VectorDocument

        vector = await self.embedder.embed(content)
        doc = VectorDocument(
            vector=vector,
            text=content,
            metadata={"role": role, "timestamp": datetime.utcnow().isoformat()},
        )
        await self.store.upsert([doc])
        self._recent.append({"role": role, "content": content})

    async def get(self, **kwargs: Any) -> list[dict[str, str]]:
        return self._recent[-10:]

    async def search(self, query: str, *, top_k: int | None = None) -> list[dict[str, Any]]:
        from ai_core.schemas import SearchQuery

        vector = await self.embedder.embed(query)
        results = await self.store.search(
            SearchQuery(
                query=query,
                query_vector=vector,
                top_k=top_k or self.top_k,
                score_threshold=self.relevance_threshold,
            )
        )
        return [{"text": r.text, "score": r.score, "metadata": r.metadata} for r in results]

    async def clear(self) -> None:
        self._recent.clear()


class RedisMemory(BaseMemory):
    """Distributed memory using Redis."""

    def __init__(
        self,
        *,
        url: str = "redis://localhost:6379",
        ttl_seconds: int = 3600,
        key_prefix: str = "ai_memory",
    ) -> None:
        self.url = url
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import redis  # type: ignore[import-untyped]

            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client

    async def add(self, role: str, content: str, **kwargs: Any) -> None:
        import json

        client = self._get_client()
        key = f"{self.key_prefix}:history"
        entry = json.dumps({"role": role, "content": content, "ts": datetime.utcnow().isoformat()})
        client.rpush(key, entry)
        client.expire(key, self.ttl_seconds)

    async def get(self, **kwargs: Any) -> list[dict[str, str]]:
        import json

        client = self._get_client()
        key = f"{self.key_prefix}:history"
        items = client.lrange(key, 0, -1) or []
        return [json.loads(item) for item in items]

    async def clear(self) -> None:
        client = self._get_client()
        client.delete(f"{self.key_prefix}:history")


class PostgresMemory(BaseMemory):
    """Durable queryable memory using PostgreSQL."""

    def __init__(
        self,
        connection_string: str,
        *,
        table_name: str = "ai_memory",
    ) -> None:
        self.connection_string = connection_string
        self.table_name = table_name

    async def _get_pool(self) -> Any:
        import asyncpg  # type: ignore[import-untyped]

        return await asyncpg.create_pool(self.connection_string, min_size=1, max_size=5)

    async def add(self, role: str, content: str, **kwargs: Any) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO {self.table_name} (role, content, created_at) VALUES ($1, $2, $3)",
                role,
                content,
                datetime.utcnow(),
            )

    async def get(self, **kwargs: Any) -> list[dict[str, str]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT role, content FROM {self.table_name} ORDER BY created_at"
            )
            return [{"role": r["role"], "content": r["content"]} for r in rows]

    async def clear(self) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.table_name}")


class EntityMemory(BaseMemory):
    """Track named entities across conversation turns."""

    def __init__(self, llm: Any = None) -> None:
        self.llm = llm
        self._entities: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, str]] = []

    async def add(self, role: str, content: str, **kwargs: Any) -> None:
        self._history.append({"role": role, "content": content})
        # Simple entity extraction via keyword matching
        words = content.split()
        for word in words:
            if word[0:1].isupper() and len(word) > 2 and word.isalpha():
                if word not in self._entities:
                    self._entities[word] = {"mentions": 0, "contexts": []}
                self._entities[word]["mentions"] += 1
                self._entities[word]["contexts"].append(content[:100])

    async def get(self, **kwargs: Any) -> list[dict[str, str]]:
        messages = list(self._history[-10:])
        if self._entities:
            entity_summary = "; ".join(
                f"{name} (mentioned {info['mentions']}x)"
                for name, info in self._entities.items()
            )
            messages.insert(0, {"role": "system", "content": f"Known entities: {entity_summary}"})
        return messages

    async def clear(self) -> None:
        self._entities.clear()
        self._history.clear()

    def get_entities(self) -> dict[str, dict[str, Any]]:
        return dict(self._entities)


# ── Factory ──────────────────────────────────────────────────────────────────

_TYPES = {
    "buffer": ConversationBufferMemory,
    "summary": ConversationSummaryMemory,
    "vector": VectorMemory,
    "redis": RedisMemory,
    "postgres": PostgresMemory,
    "entity": EntityMemory,
}


class MemoryFactory:
    @staticmethod
    def create(memory_type: str, **kwargs: Any) -> BaseMemory:
        cls = _TYPES.get(memory_type)
        if cls is None:
            raise ValueError(f"Unknown memory type: {memory_type}")
        return cls(**kwargs)
