"""
Tests for ai_core.chunking — all 10 chunking strategies.
"""

import pytest

from ai_core.chunking import ChunkingEngine
from ai_core.schemas import ChunkingConfig, ChunkingStrategy


# ── Fixtures ──────────────────────────────────────────────────────────────────

SHORT_TEXT = "Hello world. This is a test sentence."

MEDIUM_TEXT = (
    "Retrieval-Augmented Generation (RAG) is an AI framework. "
    "It combines retrieval with language model generation. "
    "Documents are chunked and embedded into a vector store. "
    "At query time, relevant chunks are retrieved and injected as context. "
    "This reduces hallucinations and improves factual accuracy."
)

LONG_TEXT = ("Enterprise AI requires careful planning. " * 50).strip()

MARKDOWN_TEXT = """# Introduction

This is the introduction section with some text.

## Background

The background provides context about the problem.

### Details

Here are more specific details about the approach.

## Methodology

We followed a rigorous experimental methodology.
"""

CODE_TEXT = """
class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, item):
        return item.strip()

async def main():
    processor = DataProcessor()
    result = processor.process("  hello  ")
    print(result)

def helper():
    return 42
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def chunk(strategy: ChunkingStrategy, text: str, **kwargs) -> list:
    config = ChunkingConfig(strategy=strategy, **kwargs)
    return ChunkingEngine.chunk(text, strategy, config)


# ── Fixed Size ────────────────────────────────────────────────────────────────

class TestFixedSizeChunker:
    def test_produces_chunks(self):
        chunks = chunk(ChunkingStrategy.FIXED, LONG_TEXT, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 1

    def test_chunk_size_respected(self):
        chunks = chunk(ChunkingStrategy.FIXED, LONG_TEXT, chunk_size=100, chunk_overlap=0)
        for c in chunks:
            assert len(c.content) <= 120  # allow small overrun at word boundary

    def test_overlap_positive(self):
        chunks_no_overlap = chunk(ChunkingStrategy.FIXED, LONG_TEXT, chunk_size=100, chunk_overlap=0)
        chunks_overlap = chunk(ChunkingStrategy.FIXED, LONG_TEXT, chunk_size=100, chunk_overlap=20)
        # With overlap, more total content (some text repeated)
        total_no = sum(len(c.content) for c in chunks_no_overlap)
        total_ov = sum(len(c.content) for c in chunks_overlap)
        assert total_ov > total_no

    def test_empty_text_returns_empty(self):
        chunks = chunk(ChunkingStrategy.FIXED, "")
        assert chunks == []

    def test_short_text_single_chunk(self):
        chunks = chunk(ChunkingStrategy.FIXED, SHORT_TEXT, chunk_size=500)
        assert len(chunks) == 1


# ── Recursive ─────────────────────────────────────────────────────────────────

class TestRecursiveChunker:
    def test_produces_chunks(self):
        chunks = chunk(ChunkingStrategy.RECURSIVE, MEDIUM_TEXT)
        assert len(chunks) >= 1

    def test_all_chunks_non_empty(self):
        chunks = chunk(ChunkingStrategy.RECURSIVE, LONG_TEXT, chunk_size=200)
        assert all(len(c.content.strip()) > 0 for c in chunks)

    def test_metadata_attached(self):
        config = ChunkingConfig(strategy=ChunkingStrategy.RECURSIVE)
        engine_chunks = ChunkingEngine.chunk(MEDIUM_TEXT, ChunkingStrategy.RECURSIVE, config)
        for c in engine_chunks:
            assert hasattr(c, "metadata")
            assert hasattr(c, "chunk_index")


# ── Semantic ──────────────────────────────────────────────────────────────────

class TestSemanticChunker:
    def test_produces_chunks(self):
        chunks = chunk(ChunkingStrategy.SEMANTIC, MEDIUM_TEXT)
        assert len(chunks) >= 1

    def test_content_preserved(self):
        chunks = chunk(ChunkingStrategy.SEMANTIC, MEDIUM_TEXT)
        combined = " ".join(c.content for c in chunks)
        # All words from original text should appear in the combined output
        original_words = set(MEDIUM_TEXT.lower().split())
        combined_words = set(combined.lower().split())
        assert original_words.issubset(combined_words)


# ── Sentence ──────────────────────────────────────────────────────────────────

class TestSentenceChunker:
    def test_splits_on_sentences(self):
        chunks = chunk(ChunkingStrategy.SENTENCE, MEDIUM_TEXT, chunk_size=1)
        # Each chunk should be a sentence or part of it
        assert len(chunks) >= 2

    def test_empty_input(self):
        chunks = chunk(ChunkingStrategy.SENTENCE, "")
        assert chunks == []


# ── Document-Aware (Markdown) ─────────────────────────────────────────────────

class TestDocumentAwareChunker:
    def test_respects_headings(self):
        chunks = chunk(ChunkingStrategy.DOCUMENT_AWARE, MARKDOWN_TEXT, chunk_size=200)
        # Should split on ## boundaries
        assert len(chunks) >= 2

    def test_content_completeness(self):
        chunks = chunk(ChunkingStrategy.DOCUMENT_AWARE, MARKDOWN_TEXT)
        combined = "\n".join(c.content for c in chunks)
        assert "Introduction" in combined
        assert "Methodology" in combined


# ── Sliding Window ────────────────────────────────────────────────────────────

class TestSlidingWindowChunker:
    def test_produces_overlapping_chunks(self):
        chunks = chunk(ChunkingStrategy.SLIDING_WINDOW, MEDIUM_TEXT, chunk_size=50, chunk_overlap=10)
        if len(chunks) > 1:
            # First word of chunk[1] should appear in chunk[0] (due to overlap)
            first_word_c1 = chunks[1].content.split()[0]
            assert first_word_c1 in chunks[0].content


# ── Paragraph ─────────────────────────────────────────────────────────────────

class TestParagraphChunker:
    def test_splits_on_blank_lines(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunk(ChunkingStrategy.PARAGRAPH, text)
        assert len(chunks) == 3

    def test_no_blank_lines(self):
        chunks = chunk(ChunkingStrategy.PARAGRAPH, "Single block of text.")
        assert len(chunks) == 1


# ── Code-Aware ────────────────────────────────────────────────────────────────

class TestCodeAwareChunker:
    def test_splits_on_defs(self):
        chunks = chunk(ChunkingStrategy.CODE_AWARE, CODE_TEXT, chunk_size=100)
        assert len(chunks) >= 2

    def test_python_class_preserved(self):
        chunks = chunk(ChunkingStrategy.CODE_AWARE, CODE_TEXT)
        combined = "\n".join(c.content for c in chunks)
        assert "DataProcessor" in combined


# ── Markdown ──────────────────────────────────────────────────────────────────

class TestMarkdownChunker:
    def test_handles_headings(self):
        chunks = chunk(ChunkingStrategy.MARKDOWN, MARKDOWN_TEXT)
        assert len(chunks) >= 1

    def test_handles_empty(self):
        chunks = chunk(ChunkingStrategy.MARKDOWN, "")
        assert chunks == []


# ── ChunkingEngine Factory ────────────────────────────────────────────────────

class TestChunkingEngine:
    def test_create_returns_correct_type(self):
        from ai_core.chunking import FixedSizeChunker, RecursiveChunker
        config = ChunkingConfig(strategy=ChunkingStrategy.FIXED)
        chunker = ChunkingEngine.create(ChunkingStrategy.FIXED, config)
        assert isinstance(chunker, FixedSizeChunker)

    def test_chunk_all_strategies(self):
        text = "This is a moderately long piece of text. " * 10
        for strategy in ChunkingStrategy:
            if strategy == ChunkingStrategy.AGENTIC:
                continue  # requires async LLM
            chunks = ChunkingEngine.chunk(text, strategy, ChunkingConfig(strategy=strategy))
            assert isinstance(chunks, list), f"Strategy {strategy} did not return a list"

    def test_unknown_strategy_raises(self):
        with pytest.raises((KeyError, ValueError)):
            ChunkingEngine.create("nonexistent_strategy", ChunkingConfig(strategy=ChunkingStrategy.FIXED))
