"""
Cost Management — tracking, optimization, and quota enforcement for LLM usage.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4


# ── Cost Record ──────────────────────────────────────────────────────────────

@dataclass
class CostRecord:
    record_id: str
    timestamp: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    user_id: str = ""
    project: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Pricing table ────────────────────────────────────────────────────────────

_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_1k, output_per_1k)
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-4": (0.03, 0.06),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "claude-3-opus": (0.015, 0.075),
    "claude-3-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    "claude-3.5-sonnet": (0.003, 0.015),
    "claude-4-opus": (0.015, 0.075),
    "claude-4-sonnet": (0.003, 0.015),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-1.5-flash": (0.000075, 0.0003),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rate = _PRICING.get(model, (0.01, 0.03))
    return (input_tokens / 1000) * rate[0] + (output_tokens / 1000) * rate[1]


# ── Cost Tracker ─────────────────────────────────────────────────────────────

class CostTracker:
    """Track and aggregate LLM usage costs."""

    def __init__(self) -> None:
        self._records: list[CostRecord] = []

    def record(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        *,
        user_id: str = "",
        project: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> CostRecord:
        cost = estimate_cost(model, input_tokens, output_tokens)
        rec = CostRecord(
            record_id=uuid4().hex[:16],
            timestamp=datetime.utcnow().isoformat(),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            user_id=user_id,
            project=project,
            metadata=metadata or {},
        )
        self._records.append(rec)
        return rec

    def total_cost(self, *, since: datetime | None = None) -> float:
        return sum(r.cost_usd for r in self._filter(since=since))

    def cost_by_model(self, *, since: datetime | None = None) -> dict[str, float]:
        agg: dict[str, float] = defaultdict(float)
        for r in self._filter(since=since):
            agg[r.model] += r.cost_usd
        return dict(agg)

    def cost_by_user(self, *, since: datetime | None = None) -> dict[str, float]:
        agg: dict[str, float] = defaultdict(float)
        for r in self._filter(since=since):
            agg[r.user_id] += r.cost_usd
        return dict(agg)

    def cost_by_project(self, *, since: datetime | None = None) -> dict[str, float]:
        agg: dict[str, float] = defaultdict(float)
        for r in self._filter(since=since):
            agg[r.project] += r.cost_usd
        return dict(agg)

    def summary(self, *, since: datetime | None = None) -> dict[str, Any]:
        records = self._filter(since=since)
        total_tokens = sum(r.input_tokens + r.output_tokens for r in records)
        return {
            "total_cost_usd": sum(r.cost_usd for r in records),
            "total_requests": len(records),
            "total_tokens": total_tokens,
            "by_model": self.cost_by_model(since=since),
            "by_user": self.cost_by_user(since=since),
        }

    def _filter(self, *, since: datetime | None = None) -> list[CostRecord]:
        if since is None:
            return self._records
        cutoff = since.isoformat()
        return [r for r in self._records if r.timestamp >= cutoff]


# ── Cost Optimizer ───────────────────────────────────────────────────────────

@dataclass
class OptimizationSuggestion:
    current_model: str
    suggested_model: str
    estimated_savings_pct: float
    reason: str


class CostOptimizer:
    """Suggest cheaper model alternatives and optimizations."""

    _DOWNGRADE_MAP: dict[str, list[str]] = {
        "gpt-4o": ["gpt-4o-mini"],
        "gpt-4-turbo": ["gpt-4o", "gpt-4o-mini"],
        "gpt-4": ["gpt-4o", "gpt-4o-mini"],
        "claude-3-opus": ["claude-3-sonnet", "claude-3-haiku"],
        "claude-3-sonnet": ["claude-3-haiku"],
        "claude-4-opus": ["claude-4-sonnet"],
        "gemini-1.5-pro": ["gemini-1.5-flash"],
    }

    def suggest(self, tracker: CostTracker) -> list[OptimizationSuggestion]:
        suggestions: list[OptimizationSuggestion] = []
        by_model = tracker.cost_by_model()
        for model, cost in by_model.items():
            alternatives = self._DOWNGRADE_MAP.get(model, [])
            for alt in alternatives:
                if alt in _PRICING and model in _PRICING:
                    current_input = _PRICING[model][0]
                    alt_input = _PRICING[alt][0]
                    if alt_input < current_input:
                        savings = (1 - alt_input / current_input) * 100
                        suggestions.append(
                            OptimizationSuggestion(
                                current_model=model,
                                suggested_model=alt,
                                estimated_savings_pct=round(savings, 1),
                                reason=f"Switch from {model} to {alt} for ~{savings:.0f}% savings",
                            )
                        )
                        break  # Best alternative only
        return suggestions


# ── Quota Manager ────────────────────────────────────────────────────────────

@dataclass
class QuotaConfig:
    max_cost_usd: float = 100.0
    max_requests: int = 10_000
    max_tokens: int = 10_000_000
    period_hours: int = 24


@dataclass
class QuotaStatus:
    within_limits: bool
    cost_used: float = 0.0
    cost_limit: float = 0.0
    requests_used: int = 0
    requests_limit: int = 0
    tokens_used: int = 0
    tokens_limit: int = 0
    exceeded: list[str] = field(default_factory=list)


class QuotaManager:
    """Enforce usage quotas per user, project, or globally."""

    def __init__(self, default_quota: QuotaConfig | None = None) -> None:
        self.default_quota = default_quota or QuotaConfig()
        self._quotas: dict[str, QuotaConfig] = {}  # key → quota

    def set_quota(self, key: str, quota: QuotaConfig) -> None:
        self._quotas[key] = quota

    def check(self, key: str, tracker: CostTracker) -> QuotaStatus:
        quota = self._quotas.get(key, self.default_quota)
        since = datetime.utcnow() - timedelta(hours=quota.period_hours)
        records = tracker._filter(since=since)

        # Filter records matching the key (user_id or project)
        filtered = [r for r in records if r.user_id == key or r.project == key]
        if not filtered:
            filtered = records  # Global check

        cost_used = sum(r.cost_usd for r in filtered)
        requests_used = len(filtered)
        tokens_used = sum(r.input_tokens + r.output_tokens for r in filtered)

        exceeded: list[str] = []
        if cost_used >= quota.max_cost_usd:
            exceeded.append("cost")
        if requests_used >= quota.max_requests:
            exceeded.append("requests")
        if tokens_used >= quota.max_tokens:
            exceeded.append("tokens")

        return QuotaStatus(
            within_limits=len(exceeded) == 0,
            cost_used=cost_used,
            cost_limit=quota.max_cost_usd,
            requests_used=requests_used,
            requests_limit=quota.max_requests,
            tokens_used=tokens_used,
            tokens_limit=quota.max_tokens,
            exceeded=exceeded,
        )
