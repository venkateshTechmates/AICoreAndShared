"""
Example 01 — Basic RAG Pipeline
================================
Demonstrates:
- RAGConfig setup
- Document ingestion with chunking
- Querying with hybrid search + reranking
- Streaming responses
- Pipeline hooks
- Cost tracking

Run:
    python examples/01_basic_rag.py
"""

import asyncio
import os

from ai_core.config import LibConfig
from ai_core.rag import RAGPipeline
from ai_core.schemas import (
    ChunkingStrategy,
    RAGConfig,
    SearchStrategy,
    VectorDocument,
    PipelineHook,
)
from ai_shared.cost import CostTracker
from ai_shared.logging_utils import get_logger
from ai_shared.observability import Tracer, metrics
from ai_shared.tokens import count_tokens

logger = get_logger("example.rag")
tracer = Tracer()


# ── Sample Documents ─────────────────────────────────────────────────────────

DOCUMENTS = [
    VectorDocument(
        id="doc-001",
        content=(
            "Retrieval-Augmented Generation (RAG) is an AI framework that combines "
            "the strengths of retrieval-based and generation-based models. It retrieves "
            "relevant documents from a knowledge base and uses them as context when "
            "generating responses, reducing hallucinations and improving accuracy."
        ),
        metadata={"source": "ai-glossary", "topic": "RAG", "version": 1},
    ),
    VectorDocument(
        id="doc-002",
        content=(
            "Vector databases store high-dimensional embeddings and support "
            "approximate nearest-neighbour (ANN) search. Popular choices include "
            "Qdrant, Pinecone, Weaviate, Chroma, and Milvus. They are a core component "
            "of modern RAG architectures."
        ),
        metadata={"source": "ai-glossary", "topic": "vector-stores", "version": 1},
    ),
    VectorDocument(
        id="doc-003",
        content=(
            "Hybrid search combines dense vector search (semantic similarity) with "
            "sparse keyword search (BM25). Reciprocal Rank Fusion (RRF) merges results "
            "from both approaches, typically outperforming either method alone."
        ),
        metadata={"source": "ai-glossary", "topic": "search", "version": 1},
    ),
    VectorDocument(
        id="doc-004",
        content=(
            "Reranking is a post-retrieval step that re-scores candidate documents using "
            "a cross-encoder model (e.g. Cohere Rerank, BGE Reranker). It improves "
            "precision by considering the full query–document pair rather than just "
            "independent embeddings."
        ),
        metadata={"source": "ai-glossary", "topic": "reranking", "version": 1},
    ),
    VectorDocument(
        id="doc-005",
        content=(
            "Chunking strategy profoundly affects RAG quality. Recursive chunking "
            "splits on progressively smaller separators. Semantic chunking groups "
            "sentences by similarity. Document-aware chunking respects markdown headings. "
            "Chunk size and overlap are key hyperparameters."
        ),
        metadata={"source": "ai-glossary", "topic": "chunking", "version": 1},
    ),
]


# ── Pipeline Setup ────────────────────────────────────────────────────────────

def build_pipeline() -> RAGPipeline:
    """Build a RAG pipeline using Chroma (in-memory) + OpenAI."""
    config = RAGConfig(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        embedding_provider="openai",
        vector_store_provider="chroma",
        chunking_strategy=ChunkingStrategy.RECURSIVE,
        search_strategy=SearchStrategy.HYBRID,
        top_k=3,
        rerank=True,
        rerank_top_k=3,
        temperature=0.2,
        cost_limit_usd=1.0,
    )
    return RAGPipeline(config)


# ── Cost Tracking Hook ────────────────────────────────────────────────────────

cost_tracker = CostTracker()


def post_generation_hook(context: dict) -> None:
    """Record token usage and estimated cost after every generation."""
    usage = context.get("token_usage")
    if usage:
        cost_tracker.record(
            model=context.get("model", "gpt-4o-mini"),
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            user_id="example-user",
            project_id="example-01",
        )
        logger.info(
            "token_usage",
            extra={
                "input": usage.input_tokens,
                "output": usage.output_tokens,
                "total": usage.total_tokens,
            },
        )


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    # ── 0. Check for API key ─────────────────────────────────────────────────
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning(
            "OPENAI_API_KEY not set — this example will show structure only."
        )

    # ── 1. Build pipeline ────────────────────────────────────────────────────
    logger.info("Building RAG pipeline …")
    pipeline = build_pipeline()
    pipeline.add_hook(PipelineHook.POST_GENERATION, post_generation_hook)

    # ── 2. Ingest documents ──────────────────────────────────────────────────
    logger.info("Ingesting %d documents …", len(DOCUMENTS))
    with tracer.trace("ingest"):
        await pipeline.ingest(DOCUMENTS, namespace="ai-glossary")
    metrics.increment("docs_ingested", len(DOCUMENTS))
    logger.info("Ingestion complete.")

    # ── 3. Single query ──────────────────────────────────────────────────────
    query = "What is RAG and how does hybrid search improve it?"
    logger.info("Query: %s", query)

    token_count = count_tokens(query, model="gpt-4o-mini")
    logger.info("Query token count: %d", token_count)

    with tracer.trace("query"):
        response = await pipeline.query(
            query,
            namespace="ai-glossary",
            include_sources=True,
        )

    print("\n── Answer ──────────────────────────────────────────")
    print(response.answer)

    if response.citations:
        print("\n── Sources ─────────────────────────────────────────")
        for c in response.citations:
            print(f"  [{c.document_id}] score={c.score:.3f}  {c.text[:80]}…")

    # ── 4. Streaming query ───────────────────────────────────────────────────
    print("\n── Streaming ───────────────────────────────────────")
    async for token in pipeline.stream(
        "Explain chunking strategies for RAG",
        namespace="ai-glossary",
    ):
        print(token, end="", flush=True)
    print()

    # ── 5. Multi-namespace query ─────────────────────────────────────────────
    logger.info("Ingesting a second namespace …")
    await pipeline.ingest(
        [
            VectorDocument(
                id="prod-001",
                content="Our product uses Qdrant for production vector storage.",
                metadata={"source": "internal", "topic": "infrastructure"},
            )
        ],
        namespace="internal",
    )

    merged_response = await pipeline.multi_query(
        "How is vector search used in production?",
        namespaces=["ai-glossary", "internal"],
        merge_strategy="rrf",
    )
    print("\n── Multi-namespace answer ───────────────────────────")
    print(merged_response.answer)

    # ── 6. Cost summary ──────────────────────────────────────────────────────
    summary = cost_tracker.summary()
    print(f"\n── Cost Summary ─────────────────────────────────────")
    print(f"  Total cost : ${summary['total_cost_usd']:.4f}")
    print(f"  Requests   : {summary['total_requests']}")
    print(f"  Input tok  : {summary['total_input_tokens']}")
    print(f"  Output tok : {summary['total_output_tokens']}")


if __name__ == "__main__":
    asyncio.run(main())
