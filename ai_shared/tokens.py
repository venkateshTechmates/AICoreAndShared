"""
Token Budget Management — counting, estimating, and enforcing token budgets.

Strategies: greedy, proportional, priority, fixed
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any


class BudgetStrategy(str, Enum):
    GREEDY = "greedy"
    PROPORTIONAL = "proportional"
    PRIORITY = "priority"
    FIXED = "fixed"


# ── Encoder helpers ──────────────────────────────────────────────────────────

_ENC_CACHE: dict[str, Any] = {}


def _get_encoder(model: str = "gpt-4") -> Any:
    """Return a tiktoken encoder, falling back to cl100k_base."""
    if model not in _ENC_CACHE:
        try:
            import tiktoken  # type: ignore[import-untyped]

            try:
                _ENC_CACHE[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                _ENC_CACHE[model] = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            _ENC_CACHE[model] = None
    return _ENC_CACHE[model]


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in a string, falling back to whitespace approximation."""
    enc = _get_encoder(model)
    if enc is not None:
        return len(enc.encode(text))
    # Rough heuristic: ~4 chars per token
    return max(1, len(text) // 4)


def count_messages_tokens(messages: list[dict[str, str]], model: str = "gpt-4") -> int:
    """Count tokens for a chat message list (OpenAI format)."""
    total = 0
    for msg in messages:
        total += 4  # metadata overhead per message
        total += count_tokens(msg.get("content", ""), model)
        total += count_tokens(msg.get("role", ""), model)
    total += 2  # priming
    return total


# ── Cost estimation ──────────────────────────────────────────────────────────

# Prices per 1K tokens (input, output)
_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-4": (0.03, 0.06),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "claude-3-opus": (0.015, 0.075),
    "claude-3-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    "claude-3.5-sonnet": (0.003, 0.015),
}


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4o",
) -> float:
    """Estimate cost in USD for a given token usage."""
    rate = _PRICING.get(model, (0.01, 0.03))
    return (input_tokens / 1000) * rate[0] + (output_tokens / 1000) * rate[1]


# ── Token Budget ─────────────────────────────────────────────────────────────

class TokenBudget:
    """Manages token allocation across prompt sections."""

    def __init__(
        self,
        max_tokens: int,
        model: str = "gpt-4",
        *,
        strategy: BudgetStrategy = BudgetStrategy.PROPORTIONAL,
        reserve_output: int = 500,
    ) -> None:
        self.max_tokens = max_tokens
        self.model = model
        self.strategy = strategy
        self.reserve_output = reserve_output
        self._sections: dict[str, _Section] = {}

    def add_section(
        self,
        name: str,
        content: str,
        *,
        priority: int = 1,
        min_tokens: int = 0,
        max_tokens: int | None = None,
    ) -> None:
        self._sections[name] = _Section(
            content=content,
            priority=priority,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
            token_count=count_tokens(content, self.model),
        )

    def fit(self) -> dict[str, str]:
        """Allocate tokens to sections and truncate as needed."""
        available = self.max_tokens - self.reserve_output
        if available <= 0:
            return {}

        if self.strategy == BudgetStrategy.GREEDY:
            return self._greedy(available)
        elif self.strategy == BudgetStrategy.PROPORTIONAL:
            return self._proportional(available)
        elif self.strategy == BudgetStrategy.PRIORITY:
            return self._priority(available)
        else:  # FIXED
            return self._fixed(available)

    def _greedy(self, budget: int) -> dict[str, str]:
        result: dict[str, str] = {}
        remaining = budget
        for name, sec in self._sections.items():
            if remaining <= 0:
                break
            text = self._truncate(sec.content, remaining)
            result[name] = text
            remaining -= count_tokens(text, self.model)
        return result

    def _proportional(self, budget: int) -> dict[str, str]:
        total_requested = sum(s.token_count for s in self._sections.values())
        if total_requested == 0:
            return {n: "" for n in self._sections}
        result: dict[str, str] = {}
        for name, sec in self._sections.items():
            ratio = sec.token_count / total_requested
            alloc = int(budget * ratio)
            alloc = max(alloc, sec.min_tokens)
            if sec.max_tokens is not None:
                alloc = min(alloc, sec.max_tokens)
            result[name] = self._truncate(sec.content, alloc)
        return result

    def _priority(self, budget: int) -> dict[str, str]:
        result: dict[str, str] = {}
        remaining = budget
        ordered = sorted(self._sections.items(), key=lambda x: x[1].priority, reverse=True)
        for name, sec in ordered:
            if remaining <= sec.min_tokens:
                break
            alloc = min(sec.token_count, remaining)
            if sec.max_tokens is not None:
                alloc = min(alloc, sec.max_tokens)
            result[name] = self._truncate(sec.content, alloc)
            remaining -= count_tokens(result[name], self.model)
        return result

    def _fixed(self, budget: int) -> dict[str, str]:
        result: dict[str, str] = {}
        for name, sec in self._sections.items():
            limit = sec.max_tokens if sec.max_tokens is not None else budget
            result[name] = self._truncate(sec.content, limit)
        return result

    def remaining_tokens(self) -> int:
        used = sum(s.token_count for s in self._sections.values())
        return max(0, self.max_tokens - used - self.reserve_output)

    def usage_summary(self) -> dict[str, Any]:
        sections = {
            n: {"tokens": s.token_count, "priority": s.priority} for n, s in self._sections.items()
        }
        total_used = sum(s.token_count for s in self._sections.values())
        return {
            "max_tokens": self.max_tokens,
            "reserve_output": self.reserve_output,
            "total_used": total_used,
            "remaining": self.remaining_tokens(),
            "sections": sections,
        }

    def _truncate(self, text: str, max_tok: int) -> str:
        enc = _get_encoder(self.model)
        if enc is not None:
            tokens = enc.encode(text)
            if len(tokens) <= max_tok:
                return text
            return enc.decode(tokens[:max_tok])
        # Heuristic
        chars = max_tok * 4
        return text[:chars]


class _Section:
    __slots__ = ("content", "priority", "min_tokens", "max_tokens", "token_count")

    def __init__(
        self,
        content: str,
        priority: int,
        min_tokens: int,
        max_tokens: int | None,
        token_count: int,
    ) -> None:
        self.content = content
        self.priority = priority
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.token_count = token_count
