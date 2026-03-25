"""
Example 08 — E-Commerce Domain: Intelligent Order Processing Pipeline
=====================================================================
Real-time use case: An enterprise e-commerce platform where multiple agents
handle product recommendations, fraud detection, inventory management,
and customer service — coordinated via parallel + debate strategy.

Demonstrates:
  - Parallel multi-agent execution (recommendation + fraud check simultaneously)
  - Swarm routing (route queries to domain-specific agents)
  - PII redaction on customer data (credit cards, emails, addresses)
  - Cost optimization with model downgrade suggestions
  - Quota management per merchant / per API tenant
  - Feature flags for A/B testing new recommendation models
  - Real-time content filtering for product reviews

Run:
    python examples/08_ecommerce_domain.py
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

from ai_core.agents import (
    AgentExecutor,
    AgentPipelineBuilder,
    AgentRole,
    CoordinationMode,
    MessageBus,
    MultiAgentSystem,
    tool,
)
from ai_core.schemas import AgentType
from ai_shared.cost import CostOptimizer, CostTracker, QuotaConfig, QuotaManager
from ai_shared.experiments import ExperimentManager, FeatureFlags
from ai_shared.governance import AuditLogger, DataLineageTracker, PolicyEngine, Policy
from ai_shared.logging_utils import get_logger
from ai_shared.security import ContentFilter, InputValidator, PIIDetector

logger = get_logger("example.ecommerce")


# ── E-Commerce Tools ──────────────────────────────────────────────────────────

@tool("product_search", "Search product catalog")
async def product_search(query: str) -> str:
    """Simulate product catalog search."""
    catalog = [
        {"sku": "ELEC-001", "name": "Wireless Noise-Cancelling Headphones", "price": 299.99, "stock": 45, "rating": 4.7},
        {"sku": "ELEC-002", "name": "Smart Watch Pro", "price": 449.99, "stock": 12, "rating": 4.5},
        {"sku": "HOME-001", "name": "Robot Vacuum Cleaner", "price": 599.99, "stock": 8, "rating": 4.8},
        {"sku": "FASH-001", "name": "Merino Wool Sweater", "price": 89.99, "stock": 120, "rating": 4.3},
        {"sku": "BOOK-001", "name": "AI Engineering Handbook", "price": 49.99, "stock": 200, "rating": 4.9},
    ]
    q = query.lower()
    matches = [p for p in catalog if q in p["name"].lower() or q in p["sku"].lower()]
    return json.dumps(matches[:5]) if matches else json.dumps(catalog[:3])


@tool("check_inventory", "Check real-time inventory levels")
async def check_inventory(sku: str) -> str:
    """Simulate inventory check across warehouses."""
    inventory = {
        "ELEC-001": {"warehouse_us": 20, "warehouse_eu": 15, "warehouse_asia": 10, "reorder_point": 25},
        "ELEC-002": {"warehouse_us": 5, "warehouse_eu": 4, "warehouse_asia": 3, "reorder_point": 15},
        "HOME-001": {"warehouse_us": 3, "warehouse_eu": 2, "warehouse_asia": 3, "reorder_point": 10},
    }
    data = inventory.get(sku.upper())
    if data:
        total = sum(v for k, v in data.items() if k.startswith("warehouse"))
        data["total_available"] = total
        data["below_reorder"] = total < data["reorder_point"]
        return json.dumps(data)
    return f"SKU {sku} not found in inventory system."


@tool("fraud_check", "Run fraud detection on order")
async def fraud_check(order_data: str) -> str:
    """Simulate fraud detection scoring."""
    try:
        order = json.loads(order_data)
    except json.JSONDecodeError:
        order = {"amount": 0}
    amount = order.get("amount", 0)
    signals = []
    risk_score = 0.1

    if amount > 1000:
        risk_score += 0.3
        signals.append("high_value_order")
    if order.get("new_customer", False):
        risk_score += 0.2
        signals.append("new_account")
    if order.get("shipping_country") != order.get("billing_country"):
        risk_score += 0.25
        signals.append("geo_mismatch")
    if order.get("rush_shipping", False):
        risk_score += 0.1
        signals.append("rush_shipping")

    decision = "APPROVE" if risk_score < 0.5 else ("REVIEW" if risk_score < 0.75 else "DECLINE")
    return json.dumps({
        "risk_score": round(min(risk_score, 1.0), 2),
        "decision": decision,
        "signals": signals,
    })


@tool("customer_history", "Look up customer purchase history")
async def customer_history(customer_id: str) -> str:
    """Simulate customer history lookup."""
    histories = {
        "C001": {
            "total_orders": 23, "total_spent": 4589.50, "member_since": "2022-03-15",
            "tier": "gold", "last_order": "2026-03-20",
            "top_categories": ["electronics", "books"],
        },
        "C002": {
            "total_orders": 2, "total_spent": 150.00, "member_since": "2026-03-01",
            "tier": "standard", "last_order": "2026-03-18",
            "top_categories": ["fashion"],
        },
    }
    data = histories.get(customer_id)
    return json.dumps(data) if data else f"Customer {customer_id} not found."


@tool("generate_recommendation", "Generate personalised product recommendations")
async def generate_recommendation(customer_id: str) -> str:
    """Simulate recommendation engine output."""
    recs = {
        "C001": [
            {"sku": "ELEC-002", "name": "Smart Watch Pro", "reason": "Based on electronics purchase history", "score": 0.92},
            {"sku": "BOOK-001", "name": "AI Engineering Handbook", "reason": "Top-rated in books category", "score": 0.88},
        ],
        "C002": [
            {"sku": "FASH-001", "name": "Merino Wool Sweater", "reason": "Trending in fashion", "score": 0.85},
            {"sku": "HOME-001", "name": "Robot Vacuum Cleaner", "reason": "New customer welcome offer", "score": 0.72},
        ],
    }
    data = recs.get(customer_id, [])
    return json.dumps(data)


# ── Mock LLM ──────────────────────────────────────────────────────────────────

class MockEcommerceLLM:
    def __init__(self, role: str = "general") -> None:
        self.role = role

    async def generate(self, prompt: str) -> "MockResp":
        if "recommend" in self.role:
            text = (
                "Based on customer C001's purchase history (23 orders, Gold tier, "
                "electronics + books preference), I recommend:\n"
                "1. Smart Watch Pro ($449.99) — 92% match score\n"
                "2. AI Engineering Handbook ($49.99) — 88% match\n"
                "Upsell: Bundle both for 10% discount = $449.99 savings."
            )
        elif "fraud" in self.role:
            text = (
                "Fraud analysis for order #ORD-2026-0342:\n"
                "Risk score: 0.35 (LOW) — APPROVED\n"
                "Signals: high_value_order ($1,249.98)\n"
                "Mitigating factors: Gold tier customer, consistent shipping address, "
                "purchase pattern matches historical behaviour."
            )
        elif "inventory" in self.role:
            text = (
                "Inventory status: ELEC-002 (Smart Watch Pro) — 12 units total.\n"
                "US: 5, EU: 4, Asia: 3. BELOW reorder point (15).\n"
                "Action: Triggered auto-reorder PO #PO-2026-0891 for 50 units.\n"
                "Estimated restock: 5 business days."
            )
        elif "customer_service" in self.role:
            text = (
                "Customer C001 support summary:\n"
                "- Order #ORD-2026-0342 processed successfully\n"
                "- Estimated delivery: March 28, 2026\n"
                "- Gold tier benefits applied: free expedited shipping\n"
                "- Loyalty points earned: 450 pts"
            )
        else:
            text = f"E-commerce analysis: {prompt[:80]}..."
        return MockResp(text=text)

    async def chat(self, messages: list) -> "MockResp":
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return await self.generate(last)


class MockResp:
    def __init__(self, text: str) -> None:
        self.text = text
        self.usage = type("U", (), {"input": 200, "output": 120, "total": 320})()


# ── Main Pipeline ─────────────────────────────────────────────────────────────

async def run_ecommerce_pipeline() -> None:
    print("=" * 70)
    print("  E-COMMERCE DOMAIN — Intelligent Order Processing Pipeline")
    print("=" * 70)

    # ── 1. Setup ──────────────────────────────────────────────────────────
    pii_detector = PIIDetector()
    content_filter = ContentFilter()
    input_validator = InputValidator()
    audit = AuditLogger()
    lineage = DataLineageTracker()
    cost_tracker = CostTracker()
    optimizer = CostOptimizer()
    quota_mgr = QuotaManager()
    quota_mgr.set_quota("merchant_acme", QuotaConfig(max_cost_usd=50.0, max_requests=1000))

    # Feature flags for A/B testing
    flags = FeatureFlags()
    flags.set("new_recommendation_model_v2", True)
    flags.set("enhanced_fraud_scoring", True)

    # Policy engine
    policy_engine = PolicyEngine()
    policy_engine.add_policy(Policy(
        name="block_competitor_scraping",
        condition="'scrape' in query.lower() or 'competitor' in query.lower()",
        action="deny",
        description="Block competitor price scraping attempts",
    ))

    # ── 2. Build Domain Agents ────────────────────────────────────────────
    rec_agent = AgentExecutor.create(
        AgentType.REACT, MockEcommerceLLM("recommend"),
        [product_search, customer_history, generate_recommendation],
    )
    fraud_agent = AgentExecutor.create(
        AgentType.REACT, MockEcommerceLLM("fraud"), [fraud_check],
    )
    inventory_agent = AgentExecutor.create(
        AgentType.REACT, MockEcommerceLLM("inventory"), [check_inventory],
    )
    cs_agent = AgentExecutor.create(
        AgentType.REACT, MockEcommerceLLM("customer_service"), [customer_history],
    )

    # ── 3. Parallel Pipeline: Recommendation + Fraud run simultaneously ──
    bus = MessageBus()
    parallel_pipeline = (
        AgentPipelineBuilder()
        .add_agent("recommendation_engine", rec_agent, role_description="Product recommendation specialist", domain="recommend")
        .add_agent("fraud_detector", fraud_agent, role_description="Fraud detection and risk scoring", domain="fraud")
        .add_agent("inventory_manager", inventory_agent, role_description="Inventory and supply chain", domain="inventory")
        .add_agent("customer_service", cs_agent, role_description="Customer support and order tracking", domain="support")
        .with_coordination(CoordinationMode.PARALLEL)
        .with_message_bus(bus)
        .build()
    )

    # ── 4. Process Order ──────────────────────────────────────────────────
    order_query = (
        "Customer C001 (Gold tier) wants to purchase Smart Watch Pro and AI Engineering Handbook. "
        "Total: $499.98. Shipping to USA. Billing: USA. "
        "Please check recommendations, run fraud detection, verify inventory, and confirm order."
    )

    # Validate and sanitize
    validation = input_validator.validate(order_query)
    safe_query = pii_detector.redact(order_query)

    # Check quota
    quota_status = quota_mgr.check("merchant_acme", cost_tracker)
    if not quota_status.within_limits:
        print(f"QUOTA EXCEEDED: {quota_status.exceeded}")
        return

    # Audit
    audit.log("system", "order_processing_started", "ORD-2026-0342", details={"customer": "C001"})

    # Lineage
    src = lineage.add_source("order_request", metadata={"order_id": "ORD-2026-0342"})

    # ── 5. Execute Parallel ───────────────────────────────────────────────
    print(f"\n🛒 Processing order (mode: {parallel_pipeline.coordination.value})...")
    result = await parallel_pipeline.run(safe_query)

    # Track lineage
    txn = lineage.add_transform("parallel_analysis", src, transform_desc="parallel agent execution")
    lineage.add_output("order_decision", txn)

    # Track costs
    cost_tracker.record(
        provider="openai", model="gpt-4o-mini",
        input_tokens=result.tokens_used.input,
        output_tokens=result.tokens_used.output,
        user_id="merchant_acme", project="order_processing",
    )

    # ── 6. Results ────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("ORDER PROCESSING RESULT")
    print(f"{'─' * 60}")
    for agent_name, output in result.agent_outputs.items():
        print(f"\n📦 [{agent_name}]:")
        print(f"  {output[:250]}")

    print(f"\n⏱  Elapsed: {result.elapsed_seconds}s")
    print(f"🔢 Tokens: {result.tokens_used.total}")
    print(f"💰 Cost: ${cost_tracker.total_cost():.4f}")
    print(f"📨 Messages: {result.messages_exchanged}")

    # ── 7. Cost Optimization ──────────────────────────────────────────────
    suggestions = optimizer.suggest(cost_tracker)
    if suggestions:
        print(f"\n💡 Cost Optimization Suggestions:")
        for s in suggestions:
            print(f"   Switch {s.current_model} → {s.suggested_model}: ~{s.estimated_savings_pct}% savings")

    # ── 8. Swarm Demo: Dynamic Routing ────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("SWARM ROUTING DEMO — Domain-Specific Agent Selection")
    print(f"{'─' * 60}")

    swarm_pipeline = (
        AgentPipelineBuilder()
        .add_agent("recommendation_engine", rec_agent, domain="recommend", priority=5)
        .add_agent("fraud_detector", fraud_agent, domain="fraud", priority=10)
        .add_agent("customer_service", cs_agent, domain="support", priority=3)
        .with_coordination(CoordinationMode.SWARM)
        .build()
    )

    fraud_query = "Check fraud risk for order #ORD-2026-0343 amount $2,500 new customer rush shipping"
    print(f"\n🔍 Query: {fraud_query[:80]}...")
    swarm_result = await swarm_pipeline.run(fraud_query)
    print(f"   Routed to: {list(swarm_result.agent_outputs.keys())}")
    print(f"   Result: {swarm_result.output[:200]}")

    audit.log("system", "order_processing_complete", "ORD-2026-0342", outcome="success")
    print(f"\n📝 Audit trail: {len(audit.query(resource='ORD-2026-0342'))} entries")


if __name__ == "__main__":
    asyncio.run(run_ecommerce_pipeline())
