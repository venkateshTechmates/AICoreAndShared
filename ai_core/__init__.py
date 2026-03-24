"""
AI Core Library — Enterprise-grade AI Engineering Framework.

Provides unified abstractions for RAG pipelines, vector databases,
search strategies, chunking, prompt engineering, agentic AI,
multi-framework orchestration, evaluation, reranking, deployment,
and disaster recovery.

Version: 1.1.0
Python: 3.11+
"""

__version__ = "1.1.0"
__author__ = "AI Core Team"

from ai_core.config import LibConfig
from ai_core.schemas import (
    RAGConfig,
    RAGResponse,
    VectorDocument,
    SearchQuery,
    SearchResult,
    RerankerProvider,
    EmbeddingProvider,
)

__all__ = [
    "LibConfig",
    "RAGConfig",
    "RAGResponse",
    "VectorDocument",
    "SearchQuery",
    "SearchResult",
    "RerankerProvider",
    "EmbeddingProvider",
    "__version__",
]
