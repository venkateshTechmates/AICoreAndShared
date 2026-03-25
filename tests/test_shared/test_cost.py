"""
Tests for ai_shared.cost — CostTracker, CostOptimizer, QuotaManager, estimate_cost.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ai_shared.cost import (
    CostOptimizer,
    CostRecord,
    CostTracker,
    QuotaConfig,
    QuotaManager,
    QuotaStatus,
    estimate_cost,
)


# ── estimate_cost ─────────────────────────────────────────────────────────────


class TestEstimateCost:
    def test_known_model(self):
        cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=1000)
        assert cost == pytest.approx(0.005 + 0.015, abs=1e-6)

    def test_unknown_model_uses_default(self):
        cost = estimate_cost("unknown-model", input_tokens=1000, output_tokens=1000)
        assert cost > 0

    def test_zero_tokens(self):
        cost = estimate_cost("gpt-4o", input_tokens=0, output_tokens=0)
        assert cost == 0.0

    def test_cheap_model(self):
        cost = estimate_cost("gpt-4o-mini", input_tokens=1000, output_tokens=1000)
        cheap = cost
        expensive = estimate_cost("gpt-4", input_tokens=1000, output_tokens=1000)
        assert cheap < expensive


# ── CostTracker ───────────────────────────────────────────────────────────────


class TestCostTracker:
    def setup_method(self):
        self.tracker = CostTracker()

    def test_record_returns_cost_record(self):
        rec = self.tracker.record("openai", "gpt-4o", 500, 200)
        assert isinstance(rec, CostRecord)
        assert rec.cost_usd > 0

    def test_total_cost(self):
        self.tracker.record("openai", "gpt-4o", 1000, 1000)
        self.tracker.record("openai", "gpt-4o-mini", 1000, 1000)
        total = self.tracker.total_cost()
        assert total > 0

    def test_cost_by_model(self):
        self.tracker.record("openai", "gpt-4o", 1000, 500)
        self.tracker.record("anthropic", "claude-3-haiku", 1000, 500)
        by_model = self.tracker.cost_by_model()
        assert "gpt-4o" in by_model
        assert "claude-3-haiku" in by_model

    def test_cost_by_user(self):
        self.tracker.record("openai", "gpt-4o", 100, 100, user_id="alice")
        self.tracker.record("openai", "gpt-4o", 200, 200, user_id="bob")
        by_user = self.tracker.cost_by_user()
        assert "alice" in by_user
        assert "bob" in by_user

    def test_cost_by_project(self):
        self.tracker.record("openai", "gpt-4o", 100, 100, project="proj_a")
        self.tracker.record("openai", "gpt-4o", 100, 100, project="proj_b")
        by_proj = self.tracker.cost_by_project()
        assert "proj_a" in by_proj

    def test_summary(self):
        self.tracker.record("openai", "gpt-4o", 1000, 500)
        s = self.tracker.summary()
        assert s["total_requests"] == 1
        assert s["total_tokens"] == 1500
        assert s["total_cost_usd"] > 0
        assert "by_model" in s
        assert "by_user" in s

    def test_filter_by_since(self):
        self.tracker.record("openai", "gpt-4o", 100, 100)
        # Use a future cutoff to filter everything out
        future = datetime.utcnow() + timedelta(hours=1)
        total = self.tracker.total_cost(since=future)
        assert total == 0.0

    def test_metadata_stored(self):
        rec = self.tracker.record(
            "openai", "gpt-4o", 100, 100,
            metadata={"task": "summarize"},
        )
        assert rec.metadata["task"] == "summarize"


# ── CostOptimizer ─────────────────────────────────────────────────────────────


class TestCostOptimizer:
    def test_suggests_downgrades(self):
        tracker = CostTracker()
        tracker.record("openai", "gpt-4", 10000, 5000)
        optimizer = CostOptimizer()
        suggestions = optimizer.suggest(tracker)
        assert len(suggestions) >= 1
        assert suggestions[0].estimated_savings_pct > 0

    def test_no_suggestion_for_cheapest(self):
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o-mini", 10000, 5000)
        optimizer = CostOptimizer()
        suggestions = optimizer.suggest(tracker)
        assert len(suggestions) == 0

    def test_suggestion_has_reason(self):
        tracker = CostTracker()
        tracker.record("anthropic", "claude-3-opus", 5000, 2000)
        optimizer = CostOptimizer()
        suggestions = optimizer.suggest(tracker)
        assert len(suggestions) >= 1
        assert "savings" in suggestions[0].reason.lower()


# ── QuotaManager ──────────────────────────────────────────────────────────────


class TestQuotaManager:
    def test_within_limits(self):
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o-mini", 100, 100, user_id="user1")
        qm = QuotaManager(default_quota=QuotaConfig(max_cost_usd=100.0))
        status = qm.check("user1", tracker)
        assert status.within_limits is True

    def test_cost_exceeded(self):
        tracker = CostTracker()
        # Record enough to exceed a tiny quota
        for _ in range(100):
            tracker.record("openai", "gpt-4", 10000, 10000, user_id="bigspender")
        qm = QuotaManager(default_quota=QuotaConfig(max_cost_usd=0.01))
        status = qm.check("bigspender", tracker)
        assert status.within_limits is False
        assert "cost" in status.exceeded

    def test_custom_quota_per_key(self):
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o-mini", 100, 100, user_id="vip")
        qm = QuotaManager()
        qm.set_quota("vip", QuotaConfig(max_cost_usd=1000.0, max_requests=1000))
        status = qm.check("vip", tracker)
        assert status.within_limits is True

    def test_request_limit_exceeded(self):
        tracker = CostTracker()
        for _ in range(20):
            tracker.record("openai", "gpt-4o-mini", 10, 10, user_id="spammer")
        qm = QuotaManager(default_quota=QuotaConfig(max_requests=5))
        status = qm.check("spammer", tracker)
        assert status.within_limits is False
        assert "requests" in status.exceeded

    def test_status_fields(self):
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o", 500, 500, user_id="u1")
        qm = QuotaManager()
        status = qm.check("u1", tracker)
        assert isinstance(status, QuotaStatus)
        assert status.cost_limit > 0
        assert status.requests_limit > 0
        assert status.tokens_limit > 0
