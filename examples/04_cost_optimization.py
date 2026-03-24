"""
Example 04 — Cost Optimization
================================
Demonstrates:
- TokenBudget: fit multiple content sections into a token limit
- estimate_cost / count_tokens: token accounting before LLM calls
- CostTracker: record and summarise spend by model/user/project
- CostOptimizer: surface actionable savings suggestions
- QuotaManager: per-team quota enforcement
- ModelRegistry + ABTestingFramework: A/B test cheaper models
- ExperimentManager + FeatureFlags: feature-flag-gated model selection

Run:
    python examples/04_cost_optimization.py
"""

import asyncio
import random
import uuid

from ai_shared.cost import CostOptimizer, CostTracker, QuotaManager
from ai_shared.experiments import ExperimentManager, FeatureFlags
from ai_shared.logging_utils import get_logger
from ai_shared.models import ABTestingFramework, ModelRegistry
from ai_shared.tokens import TokenBudget, count_tokens, estimate_cost

logger = get_logger("example.cost")


# ── 1. Token Counting & Cost Estimation ───────────────────────────────────────

def demo_token_counting() -> None:
    print("\n── 1. Token Counting & Cost Estimation ──────────────")

    texts = {
        "short_query": "What is retrieval-augmented generation?",
        "medium_context": (
            "RAG combines retrieval with generation. It indexes documents into a "
            "vector store, retrieves the most relevant chunks at query time, and "
            "feeds them as context to a language model. This grounds the model's "
            "response in real documents rather than relying solely on parametric memory."
        ),
        "long_document": ("Enterprise AI requires robust infrastructure. " * 50).strip(),
    }

    models_to_compare = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "claude-3-haiku"]

    for label, text in texts.items():
        tokens = count_tokens(text, model="gpt-4o")
        print(f"\n  '{label}' — {tokens} tokens")
        for model in models_to_compare:
            cost = estimate_cost(input_tokens=tokens, output_tokens=200, model=model)
            print(f"    {model:25} → ${cost:.5f}")


# ── 2. Token Budget ───────────────────────────────────────────────────────────

def demo_token_budget() -> None:
    print("\n── 2. Token Budget Manager ──────────────────────────")

    budget = TokenBudget(total_tokens=2000, strategy="priority")

    # Add sections with different priorities (lower = higher priority)
    budget.add_section(
        name="system_prompt",
        content="You are a helpful enterprise AI assistant. Answer concisely and cite sources.",
        priority=1,
        min_tokens=50,
    )
    budget.add_section(
        name="user_query",
        content="What are the best practices for chunking documents in a RAG system?",
        priority=2,
        min_tokens=20,
    )
    budget.add_section(
        name="retrieved_context_1",
        content=(
            "Chunking strategy 1: Recursive splitting uses a priority list of separators "
            "(\\n\\n, \\n, . , space) and recursively splits until chunks fit the target size. "
            "Overlap between chunks preserves context across boundaries."
        ),
        priority=3,
        min_tokens=0,
    )
    budget.add_section(
        name="retrieved_context_2",
        content=(
            "Chunking strategy 2: Semantic chunking groups sentences by embedding similarity "
            "using a Jaccard threshold. It produces semantically coherent chunks but requires "
            "an embedding step during ingestion."
        ),
        priority=3,
        min_tokens=0,
    )
    budget.add_section(
        name="chat_history",
        content=("User: tell me about AI. Assistant: AI is amazing. " * 20),
        priority=5,  # lowest priority — will be trimmed first
        min_tokens=0,
    )

    fitted = budget.fit()
    summary = budget.usage_summary()

    print(f"  Budget: 2000 tokens | Strategy: priority")
    print(f"  Sections fitted: {len(fitted)}/{len(budget._sections)}")
    for section_name, content in fitted.items():
        tokens = count_tokens(content)
        print(f"    {section_name:25} {tokens:5d} tokens | {content[:50]}…")
    print(f"  Total used: {summary['total_used']} / {summary['total_budget']} tokens")
    print(f"  Utilisation: {summary['utilisation_pct']:.1f}%")


# ── 3. Cost Tracker ───────────────────────────────────────────────────────────

def demo_cost_tracker() -> None:
    print("\n── 3. Cost Tracker ──────────────────────────────────")

    tracker = CostTracker()
    teams = ["team-alpha", "team-beta", "team-gamma"]
    model_pool = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "claude-3-haiku"]

    # Simulate 30 API calls across teams
    rng = random.Random(42)
    for _ in range(30):
        model = rng.choice(model_pool)
        input_tok = rng.randint(100, 800)
        output_tok = rng.randint(50, 400)
        tracker.record(
            model=model,
            input_tokens=input_tok,
            output_tokens=output_tok,
            user_id=rng.choice(["alice", "bob", "charlie", "diana"]),
            project_id=rng.choice(teams),
        )

    summary = tracker.summary()
    print(f"  Total cost       : ${summary['total_cost_usd']:.4f}")
    print(f"  Total requests   : {summary['total_requests']}")
    print(f"  Input tokens     : {summary['total_input_tokens']:,}")
    print(f"  Output tokens    : {summary['total_output_tokens']:,}")

    print("\n  By model:")
    for model, cost in tracker.cost_by_model().items():
        print(f"    {model:25} ${cost:.4f}")

    print("\n  By project:")
    for project, cost in tracker.cost_by_project().items():
        print(f"    {project:20} ${cost:.4f}")


# ── 4. Cost Optimizer ─────────────────────────────────────────────────────────

def demo_cost_optimizer(tracker: CostTracker | None = None) -> None:
    print("\n── 4. Cost Optimizer ────────────────────────────────")

    if tracker is None:
        tracker = CostTracker()
        rng = random.Random(99)
        for _ in range(50):
            input_tok = rng.randint(300, 1200)
            output_tok = rng.randint(100, 600)
            tracker.record(
                model="gpt-4o",
                input_tokens=input_tok,
                output_tokens=output_tok,
                user_id="alice",
                project_id="main",
            )

    optimizer = CostOptimizer()
    suggestions = optimizer.suggest(tracker)

    if suggestions:
        for s in suggestions:
            print(f"  [{s.category}] {s.description}")
            print(f"    Potential savings: {s.savings_pct:.1f}%  (${s.estimated_savings_usd:.4f})")
    else:
        print("  No optimisation suggestions at this time.")


# ── 5. Quota Manager ──────────────────────────────────────────────────────────

def demo_quota_manager() -> None:
    print("\n── 5. Quota Manager ─────────────────────────────────")
    from ai_core.schemas import QuotaConfig

    quota_mgr = QuotaManager()
    quota_mgr.set_quota(
        "team-alpha",
        QuotaConfig(
            daily_cost_usd=2.0,
            daily_requests=100,
            daily_tokens=50_000,
        ),
    )
    quota_mgr.set_quota(
        "team-beta",
        QuotaConfig(
            daily_cost_usd=0.50,
            daily_requests=20,
            daily_tokens=10_000,
        ),
    )

    tracker = CostTracker()
    rng = random.Random(7)

    # Simulate usage
    for i in range(25):
        team = "team-alpha" if i < 15 else "team-beta"
        tracker.record(
            model="gpt-4o-mini",
            input_tokens=rng.randint(100, 500),
            output_tokens=rng.randint(50, 200),
            user_id="bot",
            project_id=team,
        )

    for team in ["team-alpha", "team-beta"]:
        status = quota_mgr.check(team, tracker)
        print(f"  {team}:")
        print(f"    cost_used=${status.cost_used:.4f} / ${status.cost_limit:.2f}  "
              f"({status.cost_pct:.1f}%)")
        print(f"    requests={status.requests_used} / {status.requests_limit}  "
              f"({'EXCEEDED' if status.requests_exceeded else 'OK'})")


# ── 6. Model Registry & A/B Testing ──────────────────────────────────────────

def demo_ab_testing() -> None:
    print("\n── 6. Model Registry & A/B Testing ──────────────────")

    registry = ModelRegistry()
    registry.register(
        name="query-llm",
        version_id="v1",
        provider="openai",
        model_id="gpt-4o",
        metadata={"cost_tier": "premium"},
    )
    registry.register(
        name="query-llm",
        version_id="v2",
        provider="openai",
        model_id="gpt-4o-mini",
        metadata={"cost_tier": "economy"},
    )
    registry.promote("query-llm", "v2")
    active = registry.get_active("query-llm")
    print(f"  Active model: {active.model_id} ({active.version_id})")

    ab = ABTestingFramework()
    ab.create_test("model-cost-test", variants=["gpt-4o", "gpt-4o-mini"], weights=[0.2, 0.8])

    variant_counts: dict[str, int] = {}
    for _ in range(200):
        user_id = str(uuid.uuid4())
        variant = ab.route_request("model-cost-test", user_id=user_id)
        variant_counts[variant] = variant_counts.get(variant, 0) + 1

    print(f"  A/B routing (200 requests, 20/80 split):")
    for variant, count in sorted(variant_counts.items()):
        print(f"    {variant:25} {count:3d} requests  ({count/2:.1f}%)")

    # Simulate results — cheaper model slightly worse quality
    rng = random.Random(5)
    for _ in range(50):
        variant = rng.choices(["gpt-4o", "gpt-4o-mini"], weights=[0.2, 0.8])[0]
        quality = rng.gauss(0.85 if variant == "gpt-4o" else 0.78, 0.05)
        cost = rng.uniform(0.03, 0.06) if variant == "gpt-4o" else rng.uniform(0.003, 0.008)
        ab.record_result("model-cost-test", variant, metrics={"quality": quality, "cost_usd": cost})

    results = ab.get_results("model-cost-test")
    print(f"\n  A/B test results:")
    for variant, stats in results.items():
        if stats["sample_size"] > 0:
            q = stats["metrics"].get("quality", {}).get("mean", 0)
            c = stats["metrics"].get("cost_usd", {}).get("mean", 0)
            print(f"    {variant:25} quality={q:.3f}  avg_cost=${c:.4f}  n={stats['sample_size']}")


# ── 7. Feature Flags ─────────────────────────────────────────────────────────

def demo_feature_flags() -> None:
    print("\n── 7. Feature Flags ─────────────────────────────────")

    flags = FeatureFlags()
    flags.define("use_gpt4o_mini", rollout_pct=70, description="Route 70% of users to gpt-4o-mini")
    flags.define("enable_reranking", rollout_pct=100, description="Always enable reranking")
    flags.define("streaming_responses", rollout_pct=0, description="Disabled — not yet in prod")

    # Test a sample of user IDs
    test_users = [f"user-{i:04d}" for i in range(20)]
    enabled_mini = sum(1 for u in test_users if flags.is_enabled("use_gpt4o_mini", user_id=u))
    enabled_rerank = sum(1 for u in test_users if flags.is_enabled("enable_reranking", user_id=u))
    enabled_stream = sum(1 for u in test_users if flags.is_enabled("streaming_responses", user_id=u))

    print(f"  use_gpt4o_mini   (  70% rollout): {enabled_mini:2d}/20 users enabled")
    print(f"  enable_reranking ( 100% rollout): {enabled_rerank:2d}/20 users enabled")
    print(f"  streaming_responses (  0% rollout): {enabled_stream:2d}/20 users enabled")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    demo_token_counting()
    demo_token_budget()
    demo_cost_tracker()
    demo_cost_optimizer()
    demo_quota_manager()
    demo_ab_testing()
    demo_feature_flags()
    print("\nAll cost optimisation demos completed.")


if __name__ == "__main__":
    main()
