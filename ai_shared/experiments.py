"""
Experiments — Feature flags, experiment management, and analytics for AI pipelines.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


# ── Feature Flags ────────────────────────────────────────────────────────────

@dataclass
class FeatureFlag:
    name: str
    enabled: bool = False
    rollout_pct: float = 100.0  # 0-100
    allowed_users: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class FeatureFlags:
    """Simple feature flag system with percentage-based rollouts."""

    def __init__(self) -> None:
        self._flags: dict[str, FeatureFlag] = {}

    def define(
        self,
        name: str,
        *,
        enabled: bool = False,
        rollout_pct: float = 100.0,
        allowed_users: list[str] | None = None,
    ) -> FeatureFlag:
        flag = FeatureFlag(
            name=name,
            enabled=enabled,
            rollout_pct=rollout_pct,
            allowed_users=allowed_users or [],
        )
        self._flags[name] = flag
        return flag

    def is_enabled(self, name: str, *, user_id: str = "") -> bool:
        flag = self._flags.get(name)
        if flag is None or not flag.enabled:
            return False
        if flag.allowed_users and user_id in flag.allowed_users:
            return True
        if flag.rollout_pct >= 100.0:
            return True
        if flag.rollout_pct <= 0.0:
            return False
        # Deterministic bucket based on user_id + flag name
        if user_id:
            h = int(hashlib.md5(f"{user_id}:{name}".encode()).hexdigest(), 16)  # noqa: S324
            return (h % 100) < flag.rollout_pct
        return random.random() * 100 < flag.rollout_pct  # noqa: S311

    def toggle(self, name: str, enabled: bool) -> None:
        if name in self._flags:
            self._flags[name].enabled = enabled

    def list_flags(self) -> list[FeatureFlag]:
        return list(self._flags.values())


# ── Experiment Variant ───────────────────────────────────────────────────────

@dataclass
class ExperimentVariant:
    variant_id: str
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


@dataclass
class Experiment:
    experiment_id: str
    name: str
    description: str = ""
    status: str = "draft"  # draft, running, paused, completed
    variants: list[ExperimentVariant] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: str | None = None
    ended_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Experiment Manager ───────────────────────────────────────────────────────

class ExperimentManager:
    """Create and manage multi-variant experiments for AI pipelines."""

    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._assignments: dict[str, dict[str, str]] = {}  # exp_id → {user → variant_id}
        self._results: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def create(
        self,
        name: str,
        variants: list[dict[str, Any]],
        description: str = "",
    ) -> Experiment:
        exp = Experiment(
            experiment_id=uuid4().hex[:12],
            name=name,
            description=description,
            variants=[
                ExperimentVariant(
                    variant_id=uuid4().hex[:8],
                    name=v.get("name", f"variant_{i}"),
                    config=v.get("config", {}),
                    weight=v.get("weight", 1.0),
                )
                for i, v in enumerate(variants)
            ],
        )
        self._experiments[exp.experiment_id] = exp
        return exp

    def start(self, experiment_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if exp is None or exp.status not in ("draft", "paused"):
            return False
        exp.status = "running"
        exp.started_at = datetime.utcnow().isoformat()
        return True

    def pause(self, experiment_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if exp is None or exp.status != "running":
            return False
        exp.status = "paused"
        return True

    def complete(self, experiment_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if exp is None:
            return False
        exp.status = "completed"
        exp.ended_at = datetime.utcnow().isoformat()
        return True

    def assign_variant(self, experiment_id: str, user_id: str) -> ExperimentVariant | None:
        """Assign a user to a variant (sticky assignment)."""
        exp = self._experiments.get(experiment_id)
        if exp is None or exp.status != "running" or not exp.variants:
            return None

        # Check existing assignment
        assignments = self._assignments.setdefault(experiment_id, {})
        if user_id in assignments:
            vid = assignments[user_id]
            for v in exp.variants:
                if v.variant_id == vid:
                    return v

        # Weighted random assignment
        total_weight = sum(v.weight for v in exp.variants)
        h = int(hashlib.md5(f"{experiment_id}:{user_id}".encode()).hexdigest(), 16)  # noqa: S324
        threshold = (h % 10000) / 10000 * total_weight
        cumulative = 0.0
        for v in exp.variants:
            cumulative += v.weight
            if threshold <= cumulative:
                assignments[user_id] = v.variant_id
                return v

        # Fallback
        chosen = exp.variants[0]
        assignments[user_id] = chosen.variant_id
        return chosen

    def record_metric(
        self,
        experiment_id: str,
        variant_id: str,
        metric_name: str,
        value: float,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._results[experiment_id].append({
            "variant_id": variant_id,
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {}),
        })

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        return self._experiments.get(experiment_id)

    def list_experiments(self, *, status: str | None = None) -> list[Experiment]:
        exps = list(self._experiments.values())
        if status:
            exps = [e for e in exps if e.status == status]
        return exps


# ── Experiment Analytics ─────────────────────────────────────────────────────

class ExperimentAnalytics:
    """Analyze experiment results across variants."""

    def __init__(self, manager: ExperimentManager) -> None:
        self.manager = manager

    def summary(self, experiment_id: str) -> dict[str, Any]:
        exp = self.manager.get_experiment(experiment_id)
        if exp is None:
            return {}

        results = self.manager._results.get(experiment_id, [])
        variant_metrics: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for r in results:
            variant_metrics[r["variant_id"]][r["metric"]].append(r["value"])

        variant_summaries: dict[str, Any] = {}
        for variant in exp.variants:
            metrics = variant_metrics.get(variant.variant_id, {})
            variant_summaries[variant.name] = {
                "variant_id": variant.variant_id,
                "sample_count": sum(len(v) for v in metrics.values()),
                "metrics": {
                    m: {
                        "count": len(vals),
                        "mean": sum(vals) / len(vals) if vals else 0,
                        "min": min(vals) if vals else 0,
                        "max": max(vals) if vals else 0,
                    }
                    for m, vals in metrics.items()
                },
            }

        return {
            "experiment_id": experiment_id,
            "name": exp.name,
            "status": exp.status,
            "variants": variant_summaries,
        }

    def recommend_winner(self, experiment_id: str, metric_name: str) -> str | None:
        """Return the variant name with the highest mean for the given metric."""
        summary = self.summary(experiment_id)
        variants = summary.get("variants", {})
        best_name: str | None = None
        best_mean = float("-inf")
        for name, data in variants.items():
            metric = data.get("metrics", {}).get(metric_name, {})
            mean = metric.get("mean", 0)
            if mean > best_mean:
                best_mean = mean
                best_name = name
        return best_name
