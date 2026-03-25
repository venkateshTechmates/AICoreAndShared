"""
Example 09 — Real Estate Domain: Property Valuation Multi-Agent System
======================================================================
Real-time use case: A real estate platform where agents collaborate on
property valuation, market analysis, comparable sales, zoning compliance,
and investment risk assessment — using debate coordination with consensus.

Demonstrates:
  - Debate coordination mode with multi-round consensus
  - Data lineage tracking (property → analysis → valuation)
  - GDPR compliance for seller/buyer PII
  - Cost tracking per property valuation
  - Policy engine for regulatory compliance (fair housing, appraisal rules)
  - Audit trail for appraisal defense

Run:
    python examples/09_real_estate_domain.py
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

from ai_core.agents import (
    AgentExecutor,
    AgentPipelineBuilder,
    CoordinationMode,
    MessageBus,
    tool,
)
from ai_core.schemas import AgentType
from ai_shared.compliance import (
    CertificationRecord,
    CertificationStatus,
    ComplianceExporter,
    ComplianceFramework,
)
from ai_shared.cost import CostTracker
from ai_shared.governance import (
    AuditLogger,
    DataClassifier,
    DataLineageTracker,
    GDPRManager,
    Policy,
    PolicyEngine,
)
from ai_shared.logging_utils import get_logger
from ai_shared.security import PIIDetector

logger = get_logger("example.real_estate")


# ── Real Estate Tools ─────────────────────────────────────────────────────────

@tool("property_details", "Retrieve property details from MLS")
async def property_details(address: str) -> str:
    """Simulate MLS property lookup."""
    listings = {
        "123 oak st": {
            "address": "123 Oak St, Austin, TX 78701",
            "sqft": 2400, "bedrooms": 4, "bathrooms": 3,
            "year_built": 2018, "lot_acres": 0.25,
            "hoa": 250, "tax_annual": 8500,
            "features": ["pool", "smart_home", "solar_panels", "ev_charger"],
            "listing_price": 685000,
        },
        "456 maple ave": {
            "address": "456 Maple Ave, Austin, TX 78702",
            "sqft": 1800, "bedrooms": 3, "bathrooms": 2,
            "year_built": 2005, "lot_acres": 0.18,
            "hoa": 0, "tax_annual": 6200,
            "features": ["updated_kitchen", "hardwood_floors"],
            "listing_price": 485000,
        },
    }
    data = listings.get(address.lower().strip())
    return json.dumps(data) if data else f"Property not found: {address}"


@tool("comparable_sales", "Find comparable recent sales (comps)")
async def comparable_sales(address: str) -> str:
    """Simulate comp lookup within 0.5 miles."""
    comps = [
        {"address": "130 Oak St", "sold_price": 670000, "sqft": 2350, "sold_date": "2026-02-15", "price_per_sqft": 285},
        {"address": "145 Oak St", "sold_price": 710000, "sqft": 2500, "sold_date": "2026-01-20", "price_per_sqft": 284},
        {"address": "112 Elm St", "sold_price": 645000, "sqft": 2200, "sold_date": "2025-12-10", "price_per_sqft": 293},
        {"address": "200 Pine Rd", "sold_price": 725000, "sqft": 2600, "sold_date": "2026-03-01", "price_per_sqft": 279},
    ]
    return json.dumps(comps)


@tool("market_trends", "Get local market trends and forecasts")
async def market_trends(zip_code: str) -> str:
    """Simulate market trend data."""
    trends = {
        "78701": {
            "median_price": 675000, "yoy_change_pct": 4.2,
            "avg_dom": 28, "inventory_months": 2.1,
            "market_type": "seller",
            "forecast_12m_pct": 3.5,
            "mortgage_rate_30yr": 6.25,
        },
        "78702": {
            "median_price": 495000, "yoy_change_pct": 6.1,
            "avg_dom": 18, "inventory_months": 1.4,
            "market_type": "strong_seller",
            "forecast_12m_pct": 5.0,
            "mortgage_rate_30yr": 6.25,
        },
    }
    data = trends.get(zip_code)
    return json.dumps(data) if data else f"No data for zip {zip_code}"


@tool("zoning_check", "Check zoning and land use regulations")
async def zoning_check(address: str) -> str:
    """Simulate zoning compliance check."""
    return json.dumps({
        "zone": "SF-3",
        "permitted_use": ["single_family", "accessory_dwelling_unit"],
        "max_height_ft": 35,
        "setback_front_ft": 25,
        "max_impervious_cover_pct": 45,
        "adu_allowed": True,
        "flood_zone": "Zone X (minimal risk)",
        "historic_district": False,
    })


@tool("investment_analysis", "Calculate investment metrics")
async def investment_analysis(property_data: str) -> str:
    """Calculate ROI, cap rate, and cash flow projections."""
    try:
        data = json.loads(property_data)
    except json.JSONDecodeError:
        data = {"price": 685000, "rent_monthly": 3200}
    price = data.get("price", 685000)
    rent = data.get("rent_monthly", 3200)
    annual_rent = rent * 12
    expenses = annual_rent * 0.35  # 35% expense ratio
    noi = annual_rent - expenses
    cap_rate = noi / price * 100
    cash_on_cash = noi / (price * 0.20) * 100  # 20% down
    return json.dumps({
        "purchase_price": price,
        "gross_rent_annual": annual_rent,
        "net_operating_income": round(noi, 2),
        "cap_rate_pct": round(cap_rate, 2),
        "cash_on_cash_pct": round(cash_on_cash, 2),
        "break_even_years": round(price / noi, 1),
        "projected_appreciation_5yr": round(price * 1.035 ** 5 - price, 2),
    })


# ── Mock LLM ──────────────────────────────────────────────────────────────────

class MockRealEstateLLM:
    def __init__(self, role: str = "general") -> None:
        self.role = role

    async def generate(self, prompt: str) -> "MockResp":
        if "appraiser" in self.role:
            text = (
                "APPRAISAL ANALYSIS for 123 Oak St:\n"
                "Comparable sales approach: avg $285/sqft × 2400 sqft = $684,000\n"
                "Premium adjustments: +$15,000 (solar + EV charger), +$20,000 (pool)\n"
                "Negative adjustments: -$5,000 (HOA impact on value)\n"
                "APPRAISED VALUE: $714,000\n"
                "Confidence: HIGH (4 strong comps within 0.5mi, sold within 90 days)"
            )
        elif "market" in self.role:
            text = (
                "MARKET ANALYSIS for 78701:\n"
                "Seller's market with 2.1 months inventory (balanced = 4-6 months).\n"
                "YoY appreciation 4.2%, 12-month forecast +3.5%.\n"
                "Avg DOM 28 days — property priced at $685K should sell in 20-30 days.\n"
                "Recommended list price: $695,000-$715,000 to attract competitive offers.\n"
                "Risk: Rising mortgage rates (6.25%) may cool demand in H2 2026."
            )
        elif "investment" in self.role:
            text = (
                "INVESTMENT ANALYSIS:\n"
                "Cap rate: 3.64% — below Austin avg of 4.5% but premium location.\n"
                "Cash-on-cash return: 18.2% with 20% down.\n"
                "Break-even: 27.4 years on purchase price alone.\n"
                "5-year projected appreciation: +$129,252.\n"
                "Recommendation: MODERATE BUY — good appreciation play, weak cash flow.\n"
                "ADU potential (zone SF-3 allows) could add $1,200/mo rental income."
            )
        elif "Synthesize" in prompt or "synthesize" in prompt:
            text = (
                "CONSENSUS PROPERTY VALUATION for 123 Oak St:\n"
                "Appraised Value: $714,000 (comp-based, high confidence)\n"
                "Market Recommendation: List at $699,000-$715,000\n"
                "Investment Grade: MODERATE BUY (3.64% cap, strong appreciation)\n"
                "Key Upside: ADU conversion potential adds $14,400/yr income\n"
                "Risk Factor: Mortgage rates trending up, HOA costs\n"
                "Time to Sell: 20-30 days based on market conditions"
            )
        else:
            text = f"Real estate analysis: {prompt[:100]}..."
        return MockResp(text=text)

    async def chat(self, messages: list) -> "MockResp":
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return await self.generate(last)


class MockResp:
    def __init__(self, text: str) -> None:
        self.text = text
        self.usage = type("U", (), {"input": 300, "output": 180, "total": 480})()


# ── Main Pipeline ─────────────────────────────────────────────────────────────

async def run_real_estate_pipeline() -> None:
    print("=" * 70)
    print("  REAL ESTATE DOMAIN — Property Valuation Multi-Agent System")
    print("=" * 70)

    # ── 1. Setup ──────────────────────────────────────────────────────────
    pii_detector = PIIDetector()
    audit = AuditLogger()
    lineage = DataLineageTracker()
    classifier = DataClassifier(rules={"ssn": "restricted", "income": "confidential"})
    cost_tracker = CostTracker()
    gdpr = GDPRManager(audit_logger=audit)

    # Policy: Fair Housing Act compliance
    policy_engine = PolicyEngine()
    policy_engine.add_policy(Policy(
        name="fair_housing_act",
        condition="'race' in query.lower() or 'religion' in query.lower() or 'ethnicity' in query.lower()",
        action="deny",
        description="Block queries violating Fair Housing Act (race, religion, ethnicity discrimination)",
    ))
    policy_engine.add_policy(Policy(
        name="appraisal_standards",
        condition="'inflate' in query.lower() or 'reduce appraisal' in query.lower()",
        action="deny",
        description="Block attempts to manipulate appraisal values (USPAP compliance)",
    ))

    # Compliance
    exporter = ComplianceExporter()
    exporter.register_certification(CertificationRecord(
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.IMPLEMENTED,
        target_date="2026-06-01",
    ))

    # ── 2. Build Specialist Agents ────────────────────────────────────────
    appraiser = AgentExecutor.create(
        AgentType.REACT, MockRealEstateLLM("appraiser"),
        [property_details, comparable_sales],
    )
    market_analyst = AgentExecutor.create(
        AgentType.REACT, MockRealEstateLLM("market"),
        [market_trends, zoning_check],
    )
    investment_analyst = AgentExecutor.create(
        AgentType.REACT, MockRealEstateLLM("investment"),
        [investment_analysis],
    )

    # ── 3. Debate Pipeline: Three experts debate property value ───────────
    bus = MessageBus()
    debate_pipeline = (
        AgentPipelineBuilder()
        .add_agent("appraiser", appraiser, role_description="Licensed property appraiser — comp-based valuation")
        .add_agent("market_analyst", market_analyst, role_description="Market analyst — trends and pricing strategy")
        .add_agent("investment_analyst", investment_analyst, role_description="Investment analyst — ROI and cash flow")
        .with_coordination(CoordinationMode.DEBATE)
        .with_max_rounds(2)
        .with_message_bus(bus)
        .with_policy_check(lambda q, _: policy_engine.evaluate({"query": q}).allowed)
        .build()
    )

    # ── 4. Property Valuation Request ─────────────────────────────────────
    valuation_query = (
        "Evaluate property at 123 Oak St, Austin TX 78701 for listing. "
        "4 bed / 3 bath, 2400 sqft, built 2018, pool + solar. Listed at $685,000. "
        "Provide appraised value, market pricing strategy, and investment analysis."
    )

    safe_query = pii_detector.redact(valuation_query)
    classification = classifier.classify(safe_query)
    print(f"\n📋 Data Classification: {classification.level.value}")

    # Lineage
    src = lineage.add_source("property_listing", metadata={"address": "123 Oak St", "mls_id": "MLS-2026-78701-001"})
    audit.log("agent_appraiser", "valuation_started", "123_oak_st")

    # ── 5. Execute Debate ─────────────────────────────────────────────────
    print(f"\n🏠 Running property valuation (mode: {debate_pipeline.coordination.value})...")
    result = await debate_pipeline.run(safe_query)

    # Lineage
    xfm = lineage.add_transform("debate_valuation", src, transform_desc="3-expert debate consensus")
    lineage.add_output("valuation_report", xfm, metadata={"agents": list(result.agent_outputs.keys())})

    # Cost
    cost_tracker.record(
        provider="openai", model="gpt-4o",
        input_tokens=result.tokens_used.input,
        output_tokens=result.tokens_used.output,
        user_id="appraiser_team", project="property_valuations",
    )

    audit.log("system", "valuation_complete", "123_oak_st", details={
        "coordination": result.coordination_mode,
        "agents": list(result.agent_outputs.keys()),
        "has_conflict_resolution": result.conflict_resolution is not None,
    })

    # ── 6. Results ────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("PROPERTY VALUATION RESULTS")
    print(f"{'─' * 60}")

    print(f"\n📊 CONSENSUS OUTPUT:")
    print(f"  {result.output}")

    if result.conflict_resolution:
        cr = result.conflict_resolution
        print(f"\n🤝 Conflict Resolution: {cr.strategy}")
        print(f"   Winner/Synthesizer: {cr.winner}")
        print(f"   Reason: {cr.reason}")

    print(f"\n{'─' * 40}")
    print("INDIVIDUAL EXPERT OPINIONS:")
    for name, output in result.agent_outputs.items():
        print(f"\n  [{name}]:")
        for line in output.split("\n"):
            print(f"    {line}")

    print(f"\n⏱  Elapsed: {result.elapsed_seconds}s")
    print(f"🔢 Tokens: {result.tokens_used.total}")
    print(f"💰 Cost: ${cost_tracker.total_cost():.4f}")
    print(f"📨 Messages: {result.messages_exchanged}")

    # Data lineage
    lineage_info = lineage.to_dict()
    print(f"\n🔗 Data Lineage: {len(lineage_info['nodes'])} nodes, {len(lineage_info['edges'])} edges")

    # ── 7. Policy Test: Fair Housing Block ────────────────────────────────
    print(f"\n{'─' * 60}")
    print("POLICY COMPLIANCE TEST")
    print(f"{'─' * 60}")

    blocked_query = "What is the racial makeup of the neighborhood around 123 Oak St?"
    blocked_result = await debate_pipeline.run(blocked_query)
    print(f"\n🚫 Query: {blocked_query}")
    print(f"   Result: {blocked_result.output}")

    print(f"\n📝 Audit trail: {len(audit.export())} total entries")


if __name__ == "__main__":
    asyncio.run(run_real_estate_pipeline())
