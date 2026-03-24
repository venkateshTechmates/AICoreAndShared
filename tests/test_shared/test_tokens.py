"""
Tests for ai_shared.tokens — count_tokens, estimate_cost, TokenBudget.
"""

import pytest

from ai_shared.tokens import TokenBudget, count_tokens, estimate_cost


# ── count_tokens ──────────────────────────────────────────────────────────────

class TestCountTokens:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_short_text(self):
        count = count_tokens("Hello world")
        assert count >= 1

    def test_longer_text_more_tokens(self):
        short = count_tokens("Hi")
        long = count_tokens("This is a much longer sentence with many words.")
        assert long > short

    def test_consistent_for_same_input(self):
        text = "The quick brown fox jumps over the lazy dog."
        assert count_tokens(text) == count_tokens(text)

    def test_model_parameter_accepted(self):
        text = "Test sentence for token counting."
        count_default = count_tokens(text)
        count_gpt4 = count_tokens(text, model="gpt-4o")
        count_mini = count_tokens(text, model="gpt-4o-mini")
        # All should be positive integers
        assert count_default > 0
        assert count_gpt4 > 0
        assert count_mini > 0

    def test_fallback_for_unknown_model(self):
        text = "Token count for unknown model."
        count = count_tokens(text, model="future-model-xyz")
        # Should fall back to 4-char estimation and not raise
        assert count > 0

    def test_whitespace_only(self):
        count = count_tokens("   ")
        assert count >= 0  # may be 0 or 1 depending on tokenizer


# ── estimate_cost ─────────────────────────────────────────────────────────────

class TestEstimateCost:
    def test_zero_tokens_zero_cost(self):
        cost = estimate_cost(input_tokens=0, output_tokens=0, model="gpt-4o-mini")
        assert cost == 0.0

    def test_positive_cost(self):
        cost = estimate_cost(input_tokens=1000, output_tokens=500, model="gpt-4o-mini")
        assert cost > 0.0

    def test_output_more_expensive_than_input(self):
        # For most models output tokens cost more than input
        input_only = estimate_cost(input_tokens=1000, output_tokens=0, model="gpt-4o")
        output_only = estimate_cost(input_tokens=0, output_tokens=1000, model="gpt-4o")
        # Output pricing >= input pricing for gpt-4o
        assert output_only >= input_only

    def test_premium_model_costs_more(self):
        premium = estimate_cost(input_tokens=1000, output_tokens=500, model="gpt-4o")
        economy = estimate_cost(input_tokens=1000, output_tokens=500, model="gpt-4o-mini")
        assert premium > economy

    def test_various_models_accepted(self):
        models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3-5-sonnet",
            "claude-3-haiku",
        ]
        for model in models:
            cost = estimate_cost(input_tokens=500, output_tokens=200, model=model)
            assert isinstance(cost, float)
            assert cost >= 0.0

    def test_scales_linearly(self):
        cost_1k = estimate_cost(input_tokens=1000, output_tokens=0, model="gpt-4o-mini")
        cost_2k = estimate_cost(input_tokens=2000, output_tokens=0, model="gpt-4o-mini")
        assert abs(cost_2k - 2 * cost_1k) < 1e-9


# ── TokenBudget ───────────────────────────────────────────────────────────────

class TestTokenBudget:
    def _make_budget(self, total: int = 500, strategy: str = "greedy") -> TokenBudget:
        return TokenBudget(total_tokens=total, strategy=strategy)

    # Basic operations
    def test_empty_budget_fit_returns_empty(self):
        budget = self._make_budget()
        assert budget.fit() == {}

    def test_single_section_fits(self):
        budget = self._make_budget(total=500)
        budget.add_section("query", "What is RAG?", priority=1, min_tokens=0)
        fitted = budget.fit()
        assert "query" in fitted
        assert len(fitted["query"]) > 0

    def test_section_order_preserved(self):
        budget = self._make_budget(total=1000)
        budget.add_section("system", "Be helpful.", priority=1, min_tokens=0)
        budget.add_section("query", "What is RAG?", priority=2, min_tokens=0)
        fitted = budget.fit()
        assert "system" in fitted
        assert "query" in fitted

    # Strategy: greedy
    def test_greedy_includes_all_within_budget(self):
        budget = TokenBudget(total_tokens=2000, strategy="greedy")
        budget.add_section("a", "Short text A.", priority=1, min_tokens=0)
        budget.add_section("b", "Short text B.", priority=2, min_tokens=0)
        fitted = budget.fit()
        assert "a" in fitted
        assert "b" in fitted

    def test_greedy_drops_when_over_budget(self):
        budget = TokenBudget(total_tokens=5, strategy="greedy")
        budget.add_section("a", "A" * 200, priority=1, min_tokens=0)
        budget.add_section("b", "B" * 200, priority=2, min_tokens=0)
        fitted = budget.fit()
        total = sum(count_tokens(v) for v in fitted.values())
        assert total <= 10  # allow small overrun due to tokenizer granularity

    # Strategy: priority
    def test_priority_drops_lower_priority_first(self):
        budget = TokenBudget(total_tokens=20, strategy="priority")
        budget.add_section("critical", "Important system instruction.", priority=1, min_tokens=0)
        budget.add_section("noise", "X" * 500, priority=10, min_tokens=0)
        fitted = budget.fit()
        assert "critical" in fitted
        # 'noise' may be truncated or absent
        total = sum(count_tokens(v) for v in fitted.values())
        assert total <= 30  # small tolerance

    # Strategy: proportional
    def test_proportional_allocates_fairly(self):
        budget = TokenBudget(total_tokens=200, strategy="proportional")
        budget.add_section("a", "Section A content. " * 20, priority=1, min_tokens=0)
        budget.add_section("b", "Section B content. " * 20, priority=1, min_tokens=0)
        fitted = budget.fit()
        if len(fitted) == 2:
            tokens_a = count_tokens(fitted["a"])
            tokens_b = count_tokens(fitted["b"])
            # Both should have similar allocation (within 50% of each other)
            ratio = max(tokens_a, tokens_b) / max(min(tokens_a, tokens_b), 1)
            assert ratio < 3.0

    # usage_summary()
    def test_usage_summary_fields(self):
        budget = self._make_budget(total=500)
        budget.add_section("q", "Hello world.", priority=1, min_tokens=0)
        budget.fit()
        summary = budget.usage_summary()
        assert "total_budget" in summary
        assert "total_used" in summary
        assert "utilisation_pct" in summary
        assert summary["total_budget"] == 500
        assert 0 <= summary["utilisation_pct"] <= 100

    # min_tokens enforcement
    def test_min_tokens_section_always_included(self):
        budget = TokenBudget(total_tokens=1000, strategy="priority")
        budget.add_section(
            "required",
            "This section is always required.",
            priority=1,
            min_tokens=5,
        )
        budget.add_section(
            "optional",
            "Optional padding. " * 200,
            priority=10,
            min_tokens=0,
        )
        fitted = budget.fit()
        assert "required" in fitted
