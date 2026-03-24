"""
Chunking Engine — 10 strategies for intelligent document splitting.

Strategies: fixed, recursive, semantic, sentence, document_aware,
            agentic, sliding_window, paragraph, code_aware, markdown
"""

from __future__ import annotations

import re
import uuid
from abc import ABC, abstractmethod
from typing import Any

from ai_core.schemas import Chunk, ChunkingConfig, ChunkingStrategy


class BaseChunker(ABC):
    """Abstract base for all chunking strategies."""

    def __init__(self, config: ChunkingConfig) -> None:
        self.config = config

    @abstractmethod
    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        ...

    def _make_chunk(
        self,
        text: str,
        index: int,
        start: int,
        end: int,
        source: str = "",
        extra_meta: dict[str, Any] | None = None,
    ) -> Chunk:
        return Chunk(
            id=str(uuid.uuid4()),
            text=text,
            index=index,
            start_char=start,
            end_char=end,
            source=source,
            metadata=extra_meta or {},
        )


# ── Strategy Implementations ────────────────────────────────────────────────


class FixedSizeChunker(BaseChunker):
    """Split text into fixed-size chunks with optional overlap."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        step = max(size - overlap, 1)
        chunks: list[Chunk] = []
        for i, start in enumerate(range(0, len(text), step)):
            end = min(start + size, len(text))
            segment = text[start:end]
            if segment.strip():
                chunks.append(self._make_chunk(segment, i, start, end, extra_meta=metadata))
            if end >= len(text):
                break
        return chunks


class RecursiveChunker(BaseChunker):
    """Recursively split by a priority list of separators."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        separators = self.config.separators
        pieces = self._recursive_split(text, separators, self.config.chunk_size)
        chunks: list[Chunk] = []
        pos = 0
        for i, piece in enumerate(pieces):
            start = text.find(piece, pos)
            if start == -1:
                start = pos
            end = start + len(piece)
            chunks.append(self._make_chunk(piece, i, start, end, extra_meta=metadata))
            pos = end
        return chunks

    def _recursive_split(self, text: str, separators: list[str], max_size: int) -> list[str]:
        if len(text) <= max_size:
            return [text] if text.strip() else []
        for sep in separators:
            parts = text.split(sep)
            if len(parts) > 1:
                result: list[str] = []
                current = ""
                for part in parts:
                    candidate = current + sep + part if current else part
                    if len(candidate) <= max_size:
                        current = candidate
                    else:
                        if current.strip():
                            result.append(current)
                        current = part
                if current.strip():
                    result.append(current)
                return result
        # Fall back to fixed-size split
        return [text[i : i + max_size] for i in range(0, len(text), max_size)]


class SemanticChunker(BaseChunker):
    """
    Split at semantic boundaries using embedding similarity.

    Uses a sliding window and splits where the cosine similarity
    between adjacent windows drops below *threshold*.
    """

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= 1:
            return [self._make_chunk(text, 0, 0, len(text), extra_meta=metadata)]

        # Compute pairwise similarity between adjacent sentence groups
        similarities = self._compute_similarities(sentences)
        threshold = self.config.threshold

        groups: list[list[str]] = [[sentences[0]]]
        for i, sim in enumerate(similarities):
            if sim < threshold:
                groups.append([sentences[i + 1]])
            else:
                groups[-1].append(sentences[i + 1])

        chunks: list[Chunk] = []
        pos = 0
        for i, group in enumerate(groups):
            chunk_text = " ".join(group)
            start = text.find(chunk_text[:40], pos)
            if start == -1:
                start = pos
            end = start + len(chunk_text)
            chunks.append(self._make_chunk(chunk_text, i, start, end, extra_meta=metadata))
            pos = end
        return chunks

    @staticmethod
    def _compute_similarities(sentences: list[str]) -> list[float]:
        """Compute naive character-overlap similarities between adjacent sentences."""
        sims: list[float] = []
        for i in range(len(sentences) - 1):
            a, b = set(sentences[i].lower().split()), set(sentences[i + 1].lower().split())
            if a | b:
                sims.append(len(a & b) / len(a | b))
            else:
                sims.append(0.0)
        return sims


class SentenceChunker(BaseChunker):
    """Split text into individual sentences."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks: list[Chunk] = []
        pos = 0
        for i, sent in enumerate(sentences):
            if not sent.strip():
                continue
            start = text.find(sent, pos)
            if start == -1:
                start = pos
            end = start + len(sent)
            chunks.append(self._make_chunk(sent, i, start, end, extra_meta=metadata))
            pos = end
        return chunks


class DocumentAwareChunker(BaseChunker):
    """Respect document structure — headings, tables, lists."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        # Split on markdown headings
        sections = re.split(r'\n(?=#{1,6}\s)', text)
        chunks: list[Chunk] = []
        pos = 0
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            start = text.find(section[:40], pos)
            if start == -1:
                start = pos
            end = start + len(section)
            # If section is too large, recursively split
            if len(section) > self.config.chunk_size:
                sub = RecursiveChunker(self.config)
                sub_chunks = sub.chunk(section, metadata=metadata)
                for sc in sub_chunks:
                    sc.index = len(chunks)
                    chunks.append(sc)
            else:
                chunks.append(self._make_chunk(section, i, start, end, extra_meta=metadata))
            pos = end
        return chunks


class SlidingWindowChunker(BaseChunker):
    """Sliding window with configurable stride."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        window = self.config.chunk_size
        stride = max(self.config.chunk_overlap, 1)
        words = text.split()
        chunks: list[Chunk] = []
        for i in range(0, max(len(words) - window + 1, 1), stride):
            segment = " ".join(words[i : i + window])
            if segment.strip():
                chunks.append(self._make_chunk(segment, len(chunks), 0, len(segment), extra_meta=metadata))
        return chunks


class ParagraphChunker(BaseChunker):
    """Split on blank lines (paragraph boundaries)."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        paragraphs = re.split(r'\n\s*\n', text)
        chunks: list[Chunk] = []
        pos = 0
        for i, para in enumerate(paragraphs):
            if not para.strip():
                continue
            start = text.find(para[:40], pos)
            if start == -1:
                start = pos
            end = start + len(para)
            chunks.append(self._make_chunk(para.strip(), i, start, end, extra_meta=metadata))
            pos = end
        return chunks


class CodeAwareChunker(BaseChunker):
    """Split code by function/class definitions."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        # Match Python class and function definitions
        pattern = r'\n(?=(?:class |def |async def ))'
        parts = re.split(pattern, text)
        chunks: list[Chunk] = []
        pos = 0
        for i, part in enumerate(parts):
            if not part.strip():
                continue
            start = text.find(part[:40], pos)
            if start == -1:
                start = pos
            end = start + len(part)
            chunks.append(self._make_chunk(part, i, start, end, extra_meta=metadata))
            pos = end
        return chunks


class MarkdownChunker(BaseChunker):
    """Split markdown while preserving code blocks and heading hierarchy."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        # Protect code blocks
        code_blocks: list[str] = []
        protected = re.sub(
            r'```[\s\S]*?```',
            lambda m: f"__CODE_BLOCK_{len(code_blocks)}__" or code_blocks.append(m.group(0)) or f"__CODE_BLOCK_{len(code_blocks) - 1}__",
            text,
        )
        sections = re.split(r'\n(?=#{1,6}\s)', protected)
        chunks: list[Chunk] = []
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            # Restore code blocks
            restored = section
            for j, block in enumerate(code_blocks):
                restored = restored.replace(f"__CODE_BLOCK_{j}__", block)
            chunks.append(self._make_chunk(restored, i, 0, len(restored), extra_meta=metadata))
        return chunks


class AgenticChunker(BaseChunker):
    """LLM-guided chunking — uses an LLM to decide optimal chunk boundaries."""

    def chunk(self, text: str, *, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        # Falls back to document-aware chunking (LLM call requires async)
        return DocumentAwareChunker(self.config).chunk(text, metadata=metadata)

    async def chunk_async(
        self,
        text: str,
        llm: Any,
        *,
        instructions: str = "Split the following text into coherent chunks. Return JSON array of strings.",
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        import json

        resp = await llm.generate(f"{instructions}\n\n{text}")
        try:
            parts = json.loads(resp.text)
        except (json.JSONDecodeError, AttributeError):
            return DocumentAwareChunker(self.config).chunk(text, metadata=metadata)

        return [
            self._make_chunk(part, i, 0, len(part), extra_meta=metadata)
            for i, part in enumerate(parts)
            if isinstance(part, str) and part.strip()
        ]


# ── Factory ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[ChunkingStrategy, type[BaseChunker]] = {
    ChunkingStrategy.FIXED: FixedSizeChunker,
    ChunkingStrategy.RECURSIVE: RecursiveChunker,
    ChunkingStrategy.SEMANTIC: SemanticChunker,
    ChunkingStrategy.SENTENCE: SentenceChunker,
    ChunkingStrategy.DOCUMENT_AWARE: DocumentAwareChunker,
    ChunkingStrategy.AGENTIC: AgenticChunker,
    ChunkingStrategy.SLIDING_WINDOW: SlidingWindowChunker,
    ChunkingStrategy.PARAGRAPH: ParagraphChunker,
    ChunkingStrategy.CODE_AWARE: CodeAwareChunker,
    ChunkingStrategy.MARKDOWN: MarkdownChunker,
}


class ChunkingEngine:
    """Create a chunker for the given strategy and apply it."""

    @staticmethod
    def create(
        strategy: str | ChunkingStrategy,
        config: ChunkingConfig | None = None,
    ) -> BaseChunker:
        strat = ChunkingStrategy(strategy)
        if config is None:
            config = ChunkingConfig(strategy=strat)
        cls = _REGISTRY.get(strat)
        if cls is None:
            raise ValueError(f"Unknown chunking strategy: {strat}")
        return cls(config)

    @staticmethod
    def chunk(
        text: str,
        strategy: str | ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        config: ChunkingConfig | None = None,
        **kwargs: Any,
    ) -> list[Chunk]:
        chunker = ChunkingEngine.create(strategy, config)
        return chunker.chunk(text, **kwargs)
