"""
Model Management — Registry, A/B testing, rollback, and version tracking.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


# ── Model Version ────────────────────────────────────────────────────────────

@dataclass
class ModelVersion:
    version_id: str
    model_name: str
    provider: str
    config: dict[str, Any] = field(default_factory=dict)
    status: str = "active"  # active, deprecated, rollback
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metrics: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


# ── Model Registry ──────────────────────────────────────────────────────────

class ModelRegistry:
    """Central registry for managing model versions and configurations."""

    def __init__(self) -> None:
        self._models: dict[str, list[ModelVersion]] = {}  # name → versions
        self._active: dict[str, str] = {}  # name → active version_id

    def register(
        self,
        name: str,
        provider: str,
        *,
        config: dict[str, Any] | None = None,
        metrics: dict[str, float] | None = None,
        tags: list[str] | None = None,
    ) -> ModelVersion:
        version = ModelVersion(
            version_id=uuid4().hex[:12],
            model_name=name,
            provider=provider,
            config=config or {},
            metrics=metrics or {},
            tags=tags or [],
        )
        self._models.setdefault(name, []).append(version)
        # First version becomes active automatically
        if name not in self._active:
            self._active[name] = version.version_id
        return version

    def get_active(self, name: str) -> ModelVersion | None:
        active_id = self._active.get(name)
        if active_id is None:
            return None
        for v in self._models.get(name, []):
            if v.version_id == active_id:
                return v
        return None

    def promote(self, name: str, version_id: str) -> bool:
        versions = self._models.get(name, [])
        for v in versions:
            if v.version_id == version_id:
                # Deprecate old active
                old_id = self._active.get(name)
                if old_id:
                    for old_v in versions:
                        if old_v.version_id == old_id:
                            old_v.status = "deprecated"
                v.status = "active"
                self._active[name] = version_id
                return True
        return False

    def list_versions(self, name: str) -> list[ModelVersion]:
        return list(self._models.get(name, []))

    def list_models(self) -> list[str]:
        return list(self._models.keys())

    def get_version(self, name: str, version_id: str) -> ModelVersion | None:
        for v in self._models.get(name, []):
            if v.version_id == version_id:
                return v
        return None

    def update_metrics(self, name: str, version_id: str, metrics: dict[str, float]) -> bool:
        v = self.get_version(name, version_id)
        if v is None:
            return False
        v.metrics.update(metrics)
        return True


# ── A/B Testing Framework ───────────────────────────────────────────────────

@dataclass
class ABTestConfig:
    test_id: str
    name: str
    model_a: str
    model_b: str
    version_a: str
    version_b: str
    traffic_split: float = 0.5  # % to variant B
    status: str = "running"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    results_a: list[dict[str, Any]] = field(default_factory=list)
    results_b: list[dict[str, Any]] = field(default_factory=list)


class ABTestingFramework:
    """Run A/B tests between model versions."""

    def __init__(self) -> None:
        self._tests: dict[str, ABTestConfig] = {}

    def create_test(
        self,
        name: str,
        model_a: str,
        version_a: str,
        model_b: str,
        version_b: str,
        *,
        traffic_split: float = 0.5,
    ) -> ABTestConfig:
        test = ABTestConfig(
            test_id=uuid4().hex[:12],
            name=name,
            model_a=model_a,
            model_b=model_b,
            version_a=version_a,
            version_b=version_b,
            traffic_split=traffic_split,
        )
        self._tests[test.test_id] = test
        return test

    def route_request(self, test_id: str) -> str:
        """Return 'a' or 'b' to decide which variant handles the request."""
        import random

        test = self._tests.get(test_id)
        if test is None or test.status != "running":
            return "a"
        return "b" if random.random() < test.traffic_split else "a"  # noqa: S311

    def record_result(
        self,
        test_id: str,
        variant: str,
        *,
        latency_ms: float = 0,
        quality_score: float = 0,
        cost_usd: float = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        test = self._tests.get(test_id)
        if test is None:
            return
        result = {
            "latency_ms": latency_ms,
            "quality_score": quality_score,
            "cost_usd": cost_usd,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }
        if variant == "b":
            test.results_b.append(result)
        else:
            test.results_a.append(result)

    def get_results(self, test_id: str) -> dict[str, Any]:
        test = self._tests.get(test_id)
        if test is None:
            return {}

        def _agg(results: list[dict[str, Any]]) -> dict[str, Any]:
            if not results:
                return {"count": 0}
            latencies = [r["latency_ms"] for r in results]
            scores = [r["quality_score"] for r in results]
            costs = [r["cost_usd"] for r in results]
            return {
                "count": len(results),
                "avg_latency_ms": sum(latencies) / len(latencies),
                "avg_quality": sum(scores) / len(scores),
                "total_cost_usd": sum(costs),
            }

        return {
            "test_id": test.test_id,
            "name": test.name,
            "status": test.status,
            "variant_a": {"model": test.model_a, "version": test.version_a, **_agg(test.results_a)},
            "variant_b": {"model": test.model_b, "version": test.version_b, **_agg(test.results_b)},
        }

    def conclude(self, test_id: str, winner: str = "auto") -> str:
        test = self._tests.get(test_id)
        if test is None:
            return "unknown"
        test.status = "completed"
        if winner == "auto":
            results = self.get_results(test_id)
            a_quality = results.get("variant_a", {}).get("avg_quality", 0)
            b_quality = results.get("variant_b", {}).get("avg_quality", 0)
            return "b" if b_quality > a_quality else "a"
        return winner


# ── Rollback Manager ────────────────────────────────────────────────────────

class RollbackManager:
    """Manage safe model version rollbacks."""

    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
        self._rollback_history: list[dict[str, Any]] = []

    def rollback(self, model_name: str, target_version_id: str, *, reason: str = "") -> bool:
        current = self.registry.get_active(model_name)
        if current is None:
            return False
        target = self.registry.get_version(model_name, target_version_id)
        if target is None:
            return False

        self._rollback_history.append({
            "model": model_name,
            "from_version": current.version_id,
            "to_version": target_version_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return self.registry.promote(model_name, target_version_id)

    def list_rollbacks(self, model_name: str | None = None) -> list[dict[str, Any]]:
        if model_name is None:
            return list(self._rollback_history)
        return [r for r in self._rollback_history if r["model"] == model_name]
