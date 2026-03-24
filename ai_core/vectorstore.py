"""
Vector Database Abstraction — Unified interface for 9 vector store providers.

Supports: Qdrant, Pinecone, Weaviate, Chroma, Milvus, PgVector,
          Redis VSS, OpenSearch, Azure AI Search
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ai_core.schemas import SearchQuery, SearchResult, VectorDocument, VectorStoreProvider


class BaseVectorStore(ABC):
    """Abstract base for vector store providers."""

    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        self.collection = collection
        self.config = config

    @abstractmethod
    async def upsert(self, documents: list[VectorDocument]) -> int:
        ...

    @abstractmethod
    async def search(self, query: SearchQuery) -> list[SearchResult]:
        ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> int:
        ...

    @abstractmethod
    async def delete_namespace(self, namespace: str) -> int:
        ...

    async def list_namespaces(self) -> list[str]:
        raise NotImplementedError

    async def collection_stats(self) -> dict[str, Any]:
        raise NotImplementedError


# ── Qdrant ───────────────────────────────────────────────────────────────────


class QdrantVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        from qdrant_client import AsyncQdrantClient  # type: ignore[import-untyped]

        self._client = AsyncQdrantClient(
            url=config.get("url", "http://localhost:6333"),
            api_key=config.get("api_key"),
        )

    async def upsert(self, documents: list[VectorDocument]) -> int:
        from qdrant_client.models import PointStruct  # type: ignore[import-untyped]

        points = [
            PointStruct(
                id=doc.id,
                vector=doc.vector,
                payload={"text": doc.text, "namespace": doc.namespace, **doc.metadata},
            )
            for doc in documents
        ]
        await self._client.upsert(collection_name=self.collection, points=points)
        return len(points)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        results = await self._client.search(
            collection_name=self.collection,
            query_vector=query.query_vector,
            limit=query.top_k,
            query_filter=self._build_filter(query.filters, query.namespace),
            with_payload=query.include_metadata,
            with_vectors=query.include_vectors,
            score_threshold=query.score_threshold,
        )
        return [
            SearchResult(
                id=str(r.id),
                text=r.payload.get("text", "") if r.payload else "",
                score=r.score,
                metadata=dict(r.payload) if r.payload else {},
            )
            for r in results
        ]

    async def delete(self, ids: list[str]) -> int:
        from qdrant_client.models import PointIdsList  # type: ignore[import-untyped]

        await self._client.delete(
            collection_name=self.collection,
            points_selector=PointIdsList(points=ids),
        )
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore[import-untyped]

        await self._client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[FieldCondition(key="namespace", match=MatchValue(value=namespace))]
            ),
        )
        return 0  # Qdrant does not return count

    async def collection_stats(self) -> dict[str, Any]:
        info = await self._client.get_collection(self.collection)
        return {
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "status": info.status.value,
        }

    @staticmethod
    def _build_filter(filters: dict[str, Any], namespace: str) -> Any:
        from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore[import-untyped]

        conditions = [FieldCondition(key="namespace", match=MatchValue(value=namespace))]
        for key, value in filters.items():
            conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        return Filter(must=conditions) if conditions else None


# ── Pinecone ─────────────────────────────────────────────────────────────────


class PineconeVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        from pinecone import Pinecone  # type: ignore[import-untyped]

        pc = Pinecone(api_key=config.get("api_key", ""))
        self._index = pc.Index(collection)

    async def upsert(self, documents: list[VectorDocument]) -> int:
        import asyncio

        vectors = [
            {
                "id": doc.id,
                "values": doc.vector,
                "metadata": {"text": doc.text, **doc.metadata},
            }
            for doc in documents
        ]
        ns = documents[0].namespace if documents else "default"
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._index.upsert(vectors=vectors, namespace=ns)
        )
        return len(vectors)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        import asyncio

        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._index.query(
                vector=query.query_vector,
                top_k=query.top_k,
                namespace=query.namespace,
                filter=query.filters or None,
                include_metadata=query.include_metadata,
            ),
        )
        return [
            SearchResult(
                id=m["id"],
                text=m.get("metadata", {}).get("text", ""),
                score=m["score"],
                metadata=m.get("metadata", {}),
            )
            for m in resp["matches"]
        ]

    async def delete(self, ids: list[str]) -> int:
        import asyncio

        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._index.delete(ids=ids)
        )
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        import asyncio

        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._index.delete(delete_all=True, namespace=namespace)
        )
        return 0


# ── Chroma ───────────────────────────────────────────────────────────────────


class ChromaVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        import chromadb  # type: ignore[import-untyped]

        if "host" in config:
            self._client = chromadb.HttpClient(
                host=config["host"], port=config.get("port", 8000)
            )
        else:
            self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(collection)

    async def upsert(self, documents: list[VectorDocument]) -> int:
        self._collection.upsert(
            ids=[doc.id for doc in documents],
            embeddings=[doc.vector for doc in documents],
            documents=[doc.text for doc in documents],
            metadatas=[{**doc.metadata, "namespace": doc.namespace} for doc in documents],
        )
        return len(documents)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        where = {"namespace": query.namespace} if query.namespace else None
        if query.filters:
            where = {**(where or {}), **query.filters}
        results = self._collection.query(
            query_embeddings=[query.query_vector],
            n_results=query.top_k,
            where=where or None,
            include=["documents", "metadatas", "distances"],
        )
        items: list[SearchResult] = []
        if results["ids"]:
            for i, id_ in enumerate(results["ids"][0]):
                items.append(
                    SearchResult(
                        id=id_,
                        text=(results["documents"] or [[]])[0][i] if results.get("documents") else "",
                        score=1.0 - (results["distances"] or [[]])[0][i],
                        metadata=(results["metadatas"] or [[]])[0][i] if results.get("metadatas") else {},
                    )
                )
        return items

    async def delete(self, ids: list[str]) -> int:
        self._collection.delete(ids=ids)
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        self._collection.delete(where={"namespace": namespace})
        return 0

    async def collection_stats(self) -> dict[str, Any]:
        return {"count": self._collection.count()}


# ── Weaviate ─────────────────────────────────────────────────────────────────


class WeaviateVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        import weaviate  # type: ignore[import-untyped]

        self._client = weaviate.Client(
            url=config.get("url", "http://localhost:8080"),
            auth_client_secret=weaviate.AuthApiKey(config["api_key"]) if config.get("api_key") else None,
        )

    async def upsert(self, documents: list[VectorDocument]) -> int:
        with self._client.batch as batch:
            for doc in documents:
                batch.add_data_object(
                    data_object={"text": doc.text, "namespace": doc.namespace, **doc.metadata},
                    class_name=self.collection,
                    uuid=doc.id,
                    vector=doc.vector,
                )
        return len(documents)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        result = (
            self._client.query.get(self.collection, ["text"])
            .with_near_vector({"vector": query.query_vector})
            .with_limit(query.top_k)
            .with_additional(["id", "distance"])
            .do()
        )
        items: list[SearchResult] = []
        for obj in result.get("data", {}).get("Get", {}).get(self.collection, []):
            items.append(
                SearchResult(
                    id=obj.get("_additional", {}).get("id", ""),
                    text=obj.get("text", ""),
                    score=1.0 - float(obj.get("_additional", {}).get("distance", 1.0)),
                    metadata=obj,
                )
            )
        return items

    async def delete(self, ids: list[str]) -> int:
        for id_ in ids:
            self._client.data_object.delete(uuid=id_, class_name=self.collection)
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        self._client.batch.delete_objects(
            class_name=self.collection,
            where={"path": ["namespace"], "operator": "Equal", "valueText": namespace},
        )
        return 0


# ── Milvus ───────────────────────────────────────────────────────────────────


class MilvusVectorStore(BaseVectorStore):
    """Milvus / Zilliz vector store with GPU-accelerated indexing."""

    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        from pymilvus import MilvusClient  # type: ignore[import-untyped]

        self._client = MilvusClient(
            uri=config.get("uri", "http://localhost:19530"),
            token=config.get("token", ""),
        )

    async def upsert(self, documents: list[VectorDocument]) -> int:
        import asyncio

        data = [
            {
                "id": doc.id,
                "vector": doc.vector,
                "text": doc.text,
                "namespace": doc.namespace,
                **doc.metadata,
            }
            for doc in documents
        ]
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._client.upsert(collection_name=self.collection, data=data)
        )
        return len(data)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        import asyncio

        filter_expr = f'namespace == "{query.namespace}"'
        for key, value in (query.filters or {}).items():
            filter_expr += f' and {key} == "{value}"'

        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._client.search(
                collection_name=self.collection,
                data=[query.query_vector],
                limit=query.top_k,
                filter=filter_expr,
                output_fields=["text", "namespace"],
            ),
        )
        items: list[SearchResult] = []
        for hit in results[0] if results else []:
            items.append(
                SearchResult(
                    id=str(hit["id"]),
                    text=hit.get("entity", {}).get("text", ""),
                    score=hit.get("distance", 0.0),
                    metadata=hit.get("entity", {}),
                )
            )
        return items

    async def delete(self, ids: list[str]) -> int:
        import asyncio

        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._client.delete(collection_name=self.collection, ids=ids),
        )
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        import asyncio

        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._client.delete(
                collection_name=self.collection,
                filter=f'namespace == "{namespace}"',
            ),
        )
        return 0

    async def collection_stats(self) -> dict[str, Any]:
        import asyncio

        stats = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._client.get_collection_stats(self.collection),
        )
        return {"row_count": stats.get("row_count", 0)}


# ── PgVector ─────────────────────────────────────────────────────────────────


class PgVectorStore(BaseVectorStore):
    """PostgreSQL pgvector extension for embedding storage."""

    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        self._dsn = config.get(
            "dsn",
            "postgresql://localhost:5432/vectors",
        )
        self._pool: Any = None

    async def _get_pool(self) -> Any:
        if self._pool is None:
            import asyncpg  # type: ignore[import-untyped]

            self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=2, max_size=10)
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.collection} (
                        id TEXT PRIMARY KEY,
                        vector vector,
                        text TEXT,
                        namespace TEXT DEFAULT 'default',
                        metadata JSONB DEFAULT '{{}}'::jsonb,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
        return self._pool

    async def upsert(self, documents: list[VectorDocument]) -> int:
        import json

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            for doc in documents:
                await conn.execute(
                    f"""
                    INSERT INTO {self.collection} (id, vector, text, namespace, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO UPDATE SET
                        vector = EXCLUDED.vector,
                        text = EXCLUDED.text,
                        metadata = EXCLUDED.metadata
                    """,
                    doc.id,
                    str(doc.vector),
                    doc.text,
                    doc.namespace,
                    json.dumps(doc.metadata),
                )
        return len(documents)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, text, metadata,
                       1 - (vector <=> $1::vector) AS score
                FROM {self.collection}
                WHERE namespace = $2
                ORDER BY vector <=> $1::vector
                LIMIT $3
                """,
                str(query.query_vector),
                query.namespace,
                query.top_k,
            )
        return [
            SearchResult(
                id=row["id"],
                text=row["text"],
                score=float(row["score"]),
                metadata=dict(row["metadata"]) if row["metadata"] else {},
            )
            for row in rows
        ]

    async def delete(self, ids: list[str]) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                f"DELETE FROM {self.collection} WHERE id = ANY($1)", ids
            )
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.collection} WHERE namespace = $1", namespace
            )
        return int(result.split()[-1]) if result else 0

    async def collection_stats(self) -> dict[str, Any]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.collection}")
        return {"count": count or 0}


# ── Redis VSS ────────────────────────────────────────────────────────────────


class RedisVectorStore(BaseVectorStore):
    """Redis Vector Similarity Search (Redis Stack / RediSearch)."""

    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        import redis.asyncio as aioredis  # type: ignore[import-untyped]

        self._redis = aioredis.Redis(
            host=config.get("host", "localhost"),
            port=config.get("port", 6379),
            password=config.get("password"),
            decode_responses=False,
        )
        self._prefix = f"{collection}:"
        self._index_name = f"idx:{collection}"
        self._dim = config.get("dimensions", 3072)

    async def upsert(self, documents: list[VectorDocument]) -> int:
        import json
        import struct

        pipe = self._redis.pipeline()
        for doc in documents:
            key = f"{self._prefix}{doc.id}"
            vec_bytes = struct.pack(f"{len(doc.vector)}f", *doc.vector)
            pipe.hset(
                key,
                mapping={
                    "id": doc.id,
                    "text": doc.text,
                    "namespace": doc.namespace,
                    "metadata": json.dumps(doc.metadata),
                    "vector": vec_bytes,
                },
            )
        await pipe.execute()
        return len(documents)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        import json
        import struct

        vec_bytes = struct.pack(f"{len(query.query_vector)}f", *query.query_vector)
        q = (
            f"(@namespace:{{{query.namespace}}})"
            f"=>[KNN {query.top_k} @vector $vec_param AS score]"
        )
        from redis.commands.search.query import Query  # type: ignore[import-untyped]

        search_query = (
            Query(q)
            .sort_by("score")
            .return_fields("id", "text", "metadata", "score")
            .dialect(2)
        )
        results = await self._redis.ft(self._index_name).search(
            search_query, query_params={"vec_param": vec_bytes}
        )
        items: list[SearchResult] = []
        for doc in results.docs:
            meta = {}
            if hasattr(doc, "metadata") and doc.metadata:
                meta = json.loads(doc.metadata)
            items.append(
                SearchResult(
                    id=doc.id.replace(self._prefix, ""),
                    text=getattr(doc, "text", ""),
                    score=1.0 - float(getattr(doc, "score", 1.0)),
                    metadata=meta,
                )
            )
        return items

    async def delete(self, ids: list[str]) -> int:
        keys = [f"{self._prefix}{id_}" for id_ in ids]
        if keys:
            await self._redis.delete(*keys)
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self._redis.scan(
                cursor=cursor, match=f"{self._prefix}*", count=500
            )
            for key in keys:
                data = await self._redis.hget(key, "namespace")
                if data and data.decode("utf-8") == namespace:
                    await self._redis.delete(key)
                    deleted += 1
            if cursor == 0:
                break
        return deleted


# ── OpenSearch ───────────────────────────────────────────────────────────────


class OpenSearchVectorStore(BaseVectorStore):
    """AWS OpenSearch with kNN plugin for vector similarity."""

    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        from opensearchpy import AsyncOpenSearch  # type: ignore[import-untyped]

        self._client = AsyncOpenSearch(
            hosts=config.get("hosts", [{"host": "localhost", "port": 9200}]),
            http_auth=(config.get("username", ""), config.get("password", "")),
            use_ssl=config.get("use_ssl", False),
            verify_certs=config.get("verify_certs", False),
        )
        self._index = collection

    async def upsert(self, documents: list[VectorDocument]) -> int:
        actions: list[dict[str, Any]] = []
        for doc in documents:
            actions.append({"index": {"_index": self._index, "_id": doc.id}})
            actions.append(
                {
                    "text": doc.text,
                    "vector": doc.vector,
                    "namespace": doc.namespace,
                    "metadata": doc.metadata,
                }
            )
        if actions:
            await self._client.bulk(body=actions)
        return len(documents)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        body: dict[str, Any] = {
            "size": query.top_k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "vector": {
                                    "vector": query.query_vector,
                                    "k": query.top_k,
                                }
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"namespace": query.namespace}},
                    ],
                }
            },
        }
        for key, value in (query.filters or {}).items():
            body["query"]["bool"]["filter"].append({"term": {f"metadata.{key}": value}})

        resp = await self._client.search(index=self._index, body=body)
        return [
            SearchResult(
                id=hit["_id"],
                text=hit["_source"].get("text", ""),
                score=hit.get("_score", 0.0),
                metadata=hit["_source"].get("metadata", {}),
            )
            for hit in resp.get("hits", {}).get("hits", [])
        ]

    async def delete(self, ids: list[str]) -> int:
        actions = [{"delete": {"_index": self._index, "_id": id_}} for id_ in ids]
        if actions:
            await self._client.bulk(body=actions)
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        resp = await self._client.delete_by_query(
            index=self._index,
            body={"query": {"term": {"namespace": namespace}}},
        )
        return resp.get("deleted", 0)

    async def collection_stats(self) -> dict[str, Any]:
        stats = await self._client.indices.stats(index=self._index)
        idx_stats = stats.get("indices", {}).get(self._index, {}).get("primaries", {})
        return {"doc_count": idx_stats.get("docs", {}).get("count", 0)}


# ── Azure AI Search ──────────────────────────────────────────────────────────


class AzureAISearchVectorStore(BaseVectorStore):
    """Azure AI Search (formerly Azure Cognitive Search) vector store."""

    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        super().__init__(collection, config)
        from azure.search.documents.aio import SearchClient  # type: ignore[import-untyped]
        from azure.core.credentials import AzureKeyCredential  # type: ignore[import-untyped]

        self._client = SearchClient(
            endpoint=config["endpoint"],
            index_name=collection,
            credential=AzureKeyCredential(config["api_key"]),
        )

    async def upsert(self, documents: list[VectorDocument]) -> int:
        docs = [
            {
                "id": doc.id,
                "text": doc.text,
                "vector": doc.vector,
                "namespace": doc.namespace,
                **doc.metadata,
            }
            for doc in documents
        ]
        result = await self._client.upload_documents(documents=docs)
        return sum(1 for r in result if r.succeeded)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        from azure.search.documents.models import VectorizedQuery  # type: ignore[import-untyped]

        vector_query = VectorizedQuery(
            vector=query.query_vector,
            k_nearest_neighbors=query.top_k,
            fields="vector",
        )
        filter_str = f"namespace eq '{query.namespace}'"
        results = await self._client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=filter_str,
            top=query.top_k,
        )
        items: list[SearchResult] = []
        async for result in results:
            items.append(
                SearchResult(
                    id=result["id"],
                    text=result.get("text", ""),
                    score=result.get("@search.score", 0.0),
                    metadata={k: v for k, v in result.items() if k not in ("id", "text", "vector", "@search.score")},
                )
            )
        return items

    async def delete(self, ids: list[str]) -> int:
        docs = [{"id": id_} for id_ in ids]
        await self._client.delete_documents(documents=docs)
        return len(ids)

    async def delete_namespace(self, namespace: str) -> int:
        results = await self._client.search(
            search_text="*",
            filter=f"namespace eq '{namespace}'",
            select=["id"],
        )
        ids_to_delete: list[dict[str, str]] = []
        async for r in results:
            ids_to_delete.append({"id": r["id"]})
        if ids_to_delete:
            await self._client.delete_documents(documents=ids_to_delete)
        return len(ids_to_delete)


# ── Factory ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[VectorStoreProvider, type[BaseVectorStore]] = {
    VectorStoreProvider.QDRANT: QdrantVectorStore,
    VectorStoreProvider.PINECONE: PineconeVectorStore,
    VectorStoreProvider.CHROMA: ChromaVectorStore,
    VectorStoreProvider.WEAVIATE: WeaviateVectorStore,
    VectorStoreProvider.MILVUS: MilvusVectorStore,
    VectorStoreProvider.PGVECTOR: PgVectorStore,
    VectorStoreProvider.REDIS: RedisVectorStore,
    VectorStoreProvider.OPENSEARCH: OpenSearchVectorStore,
    VectorStoreProvider.AZURE_AI_SEARCH: AzureAISearchVectorStore,
}


class VectorStoreFactory:
    """Create vector store instances by provider name."""

    @staticmethod
    def create(
        provider: str | VectorStoreProvider,
        collection: str,
        config: dict[str, Any] | None = None,
    ) -> BaseVectorStore:
        prov = VectorStoreProvider(provider)
        cls = _REGISTRY.get(prov)
        if cls is None:
            raise ValueError(f"Unsupported vector store provider: {prov}. Available: {list(_REGISTRY.keys())}")
        return cls(collection, config or {})

    @staticmethod
    def register(provider: VectorStoreProvider, cls: type[BaseVectorStore]) -> None:
        _REGISTRY[provider] = cls

    @staticmethod
    def register(provider: VectorStoreProvider, cls: type[BaseVectorStore]) -> None:
        _REGISTRY[provider] = cls
