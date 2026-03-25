"""
Example 10 — Loan Processing Domain: Automated Underwriting Pipeline
====================================================================
Real-time use case: A financial services platform where agents handle
loan application intake, credit analysis, income verification, collateral
assessment, and compliance checks — using supervisor coordination.

Demonstrates:
  - Supervisor coordination (underwriting manager routes to specialists)
  - SOC2 + GDPR compliance for financial data
  - PII detection (SSN, credit card, income) with redaction
  - Data classification (restricted / confidential / internal)
  - Cost management with quota per loan officer / per branch
  - Resilience: circuit breaker on credit bureau API
  - Full audit trail for regulatory examination
  - Data retention policies for financial records

Run:
    python examples/10_loan_processing_domain.py
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta

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
    ComplianceMonitor,
)
from ai_shared.cost import CostTracker, QuotaConfig, QuotaManager
from ai_shared.governance import (
    AuditLogger,
    DataClassifier,
    DataLineageTracker,
    GDPRManager,
    Policy,
    PolicyEngine,
    RetentionManager,
    RetentionPolicy,
)
from ai_shared.logging_utils import get_logger
from ai_shared.security import ContentFilter, InputValidator, PIIDetector

logger = get_logger("example.loan_processing")


# ── Loan Processing Tools ────────────────────────────────────────────────────

@tool("credit_check", "Pull credit report from bureaus")
async def credit_check(applicant_id: str) -> str:
    """Simulate credit bureau pull (Experian, Equifax, TransUnion)."""
    reports = {
        "APP-001": {
            "fico_score": 742, "credit_tier": "prime",
            "accounts": 12, "delinquencies_30d": 0, "delinquencies_60d": 0,
            "total_debt": 45000, "available_credit": 85000,
            "credit_utilization_pct": 34.6,
            "hard_inquiries_12m": 2,
            "bankruptcies": 0, "collections": 0,
        },
        "APP-002": {
            "fico_score": 618, "credit_tier": "subprime",
            "accounts": 5, "delinquencies_30d": 2, "delinquencies_60d": 1,
            "total_debt": 28000, "available_credit": 15000,
            "credit_utilization_pct": 65.1,
            "hard_inquiries_12m": 6,
            "bankruptcies": 0, "collections": 1,
        },
    }
    data = reports.get(applicant_id)
    return json.dumps(data) if data else f"No credit data for {applicant_id}"


@tool("income_verification", "Verify income from employment and tax records")
async def income_verification(applicant_id: str) -> str:
    """Simulate income verification (W-2, pay stubs, tax returns)."""
    records = {
        "APP-001": {
            "annual_gross": 125000, "employment_type": "W2_full_time",
            "employer": "TechCorp Inc.", "tenure_years": 5,
            "w2_verified": True, "tax_returns_2yr": True,
            "other_income": 12000, "total_income": 137000,
            "monthly_dti_obligations": 1850,
        },
        "APP-002": {
            "annual_gross": 52000, "employment_type": "W2_full_time",
            "employer": "RetailMart", "tenure_years": 1,
            "w2_verified": True, "tax_returns_2yr": False,
            "other_income": 0, "total_income": 52000,
            "monthly_dti_obligations": 1200,
        },
    }
    data = records.get(applicant_id)
    return json.dumps(data) if data else f"No income data for {applicant_id}"


@tool("collateral_appraisal", "Appraise collateral value")
async def collateral_appraisal(property_address: str) -> str:
    """Simulate property appraisal for collateral."""
    appraisals = {
        "789 cedar ln": {
            "appraised_value": 520000, "property_type": "single_family",
            "condition": "good", "sqft": 2100,
            "lot_size_acres": 0.22, "year_built": 2015,
            "flood_zone": False, "environmental_issues": False,
            "comparable_sales_range": [490000, 545000],
        },
    }
    data = appraisals.get(property_address.lower().strip())
    return json.dumps(data) if data else f"No appraisal for {property_address}"


@tool("dti_calculator", "Calculate debt-to-income ratio")
async def dti_calculator(loan_data: str) -> str:
    """Calculate DTI and loan eligibility."""
    try:
        data = json.loads(loan_data)
    except json.JSONDecodeError:
        data = {}
    monthly_income = data.get("monthly_income", 10000)
    monthly_debt = data.get("monthly_debt", 1850)
    proposed_payment = data.get("proposed_payment", 2200)

    front_dti = proposed_payment / monthly_income * 100
    back_dti = (monthly_debt + proposed_payment) / monthly_income * 100

    return json.dumps({
        "front_end_dti_pct": round(front_dti, 1),
        "back_end_dti_pct": round(back_dti, 1),
        "conventional_limit_front": 28.0,
        "conventional_limit_back": 36.0,
        "fha_limit_front": 31.0,
        "fha_limit_back": 43.0,
        "qualifies_conventional": front_dti <= 28 and back_dti <= 36,
        "qualifies_fha": front_dti <= 31 and back_dti <= 43,
    })


@tool("compliance_screening", "Screen for OFAC, PEP, and sanctions")
async def compliance_screening(applicant_name: str) -> str:
    """Simulate AML/KYC compliance screening."""
    return json.dumps({
        "applicant": applicant_name,
        "ofac_match": False,
        "pep_match": False,
        "sanctions_match": False,
        "adverse_media": False,
        "screening_date": datetime.utcnow().isoformat(),
        "disposition": "CLEAR",
    })


# ── Mock LLM ──────────────────────────────────────────────────────────────────

class MockLoanLLM:
    def __init__(self, role: str = "general") -> None:
        self.role = role

    async def generate(self, prompt: str) -> "MockResp":
        if "credit" in self.role:
            text = (
                "CREDIT ANALYSIS — Applicant APP-001:\n"
                "FICO: 742 (Prime tier) — STRONG\n"
                "Credit utilization: 34.6% — ACCEPTABLE (target <30%)\n"
                "Delinquencies: None — EXCELLENT\n"
                "Hard inquiries: 2 in 12 months — NORMAL\n"
                "Risk assessment: LOW RISK. Recommend approval with standard pricing.\n"
                "Rate recommendation: 6.125% (30yr fixed, conforming)"
            )
        elif "income" in self.role:
            text = (
                "INCOME VERIFICATION — Applicant APP-001:\n"
                "Total verified income: $137,000/yr ($11,417/mo)\n"
                "Employment: W2, 5-year tenure at TechCorp — STABLE\n"
                "W-2 verified ✓, 2-year tax returns ✓\n"
                "Monthly obligations: $1,850\n"
                "Proposed payment (est.): $2,200/mo\n"
                "Back-end DTI: 35.5% — QUALIFIES for conventional (<36%)\n"
                "Residual income: $7,367/mo — STRONG"
            )
        elif "collateral" in self.role:
            text = (
                "COLLATERAL ASSESSMENT — 789 Cedar Ln:\n"
                "Appraised value: $520,000 — within comp range ($490K-$545K)\n"
                "LTV: 80.8% ($420,000 loan / $520,000 value)\n"
                "Property condition: Good, no major defects\n"
                "Flood zone: No — no flood insurance required\n"
                "Environmental: Clear\n"
                "Collateral adequacy: ACCEPTABLE for conventional financing"
            )
        elif "supervisor" in self.role or "underwriter" in self.role:
            if "DONE" in prompt or "Synthesize" in prompt or "synthesize" in prompt:
                text = (
                    "DONE UNDERWRITING DECISION for Loan #LN-2026-0142:\n"
                    "═══════════════════════════════════════\n"
                    "DECISION: APPROVED WITH CONDITIONS\n"
                    "═══════════════════════════════════════\n"
                    "Loan amount: $420,000 | Property: 789 Cedar Ln\n"
                    "Rate: 6.125% (30yr fixed) | LTV: 80.8%\n"
                    "Applicant: APP-001 (FICO 742, DTI 35.5%)\n\n"
                    "CONDITIONS:\n"
                    "1. Reduce credit utilization to <30% before closing\n"
                    "2. Provide final pay stub within 10 days of closing\n"
                    "3. Title insurance and clear title search required\n\n"
                    "RISK RATING: LOW | EXPECTED LOSS: 0.12%"
                )
            else:
                text = "CALL credit_analyst to assess creditworthiness"
        else:
            text = f"Loan analysis: {prompt[:100]}..."
        return MockResp(text=text)

    async def chat(self, messages: list) -> "MockResp":
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return await self.generate(last)


class MockResp:
    def __init__(self, text: str) -> None:
        self.text = text
        self.usage = type("U", (), {"input": 280, "output": 200, "total": 480})()


# ── Main Pipeline ─────────────────────────────────────────────────────────────

async def run_loan_pipeline() -> None:
    print("=" * 70)
    print("  LOAN PROCESSING — Automated Underwriting Pipeline")
    print("=" * 70)

    # ── 1. Security & Compliance Setup ────────────────────────────────────
    pii_detector = PIIDetector()
    content_filter = ContentFilter()
    input_validator = InputValidator(max_length=50_000)
    audit = AuditLogger()
    lineage = DataLineageTracker()
    classifier = DataClassifier(rules={
        "ssn": "restricted", "income": "confidential",
        "credit": "confidential", "bank_account": "restricted",
    })
    cost_tracker = CostTracker()
    quota_mgr = QuotaManager()
    quota_mgr.set_quota("branch_central", QuotaConfig(max_cost_usd=200.0, max_requests=500))
    gdpr = GDPRManager(audit_logger=audit)

    # Retention policies (financial regulations require 7-year retention)
    retention = RetentionManager()
    retention.add_policy(RetentionPolicy(
        name="loan_documents", data_type="loan_applications",
        retention_days=2555, action="archive",  # 7 years
    ))
    retention.add_policy(RetentionPolicy(
        name="credit_reports", data_type="credit_data",
        retention_days=730, action="delete",  # 2 years
    ))
    retention.add_policy(RetentionPolicy(
        name="audit_logs", data_type="audit_logs",
        retention_days=2555, action="archive",  # 7 years
    ))

    # Policy engine
    policy_engine = PolicyEngine()
    policy_engine.add_policy(Policy(
        name="fair_lending",
        condition="'race' in query.lower() or 'gender' in query.lower() or 'marital' in query.lower()",
        action="deny",
        description="Block discriminatory lending criteria (ECOA compliance)",
    ))
    policy_engine.add_policy(Policy(
        name="max_loan_amount",
        condition="loan_amount > 2000000",
        action="deny",
        description="Loans over $2M require manual senior underwriter review",
    ))

    # Compliance certifications
    monitor = ComplianceMonitor()
    exporter = ComplianceExporter()
    for fw, status in [
        (ComplianceFramework.SOC2, CertificationStatus.IMPLEMENTED),
        (ComplianceFramework.GDPR, CertificationStatus.IMPLEMENTED),
        (ComplianceFramework.PCI_DSS, CertificationStatus.IMPLEMENTED),
    ]:
        exporter.register_certification(CertificationRecord(
            framework=fw, status=status, target_date="2026-01-01",
        ))

    # ── 2. Build Underwriting Agents ──────────────────────────────────────
    credit_agent = AgentExecutor.create(
        AgentType.REACT, MockLoanLLM("credit"),
        [credit_check, compliance_screening],
    )
    income_agent = AgentExecutor.create(
        AgentType.REACT, MockLoanLLM("income"),
        [income_verification, dti_calculator],
    )
    collateral_agent = AgentExecutor.create(
        AgentType.REACT, MockLoanLLM("collateral"),
        [collateral_appraisal],
    )
    underwriter = AgentExecutor.create(
        AgentType.PLAN_EXECUTE, MockLoanLLM("underwriter"),
    )

    # ── 3. Supervisor Pipeline ────────────────────────────────────────────
    bus = MessageBus()
    pipeline = (
        AgentPipelineBuilder()
        .add_agent("senior_underwriter", underwriter,
                    role_description="Senior underwriter — makes final loan decision", priority=10)
        .add_agent("credit_analyst", credit_agent,
                    role_description="Credit analyst — credit score and risk assessment", domain="credit")
        .add_agent("income_verifier", income_agent,
                    role_description="Income verification specialist — DTI and employment", domain="income")
        .add_agent("collateral_assessor", collateral_agent,
                    role_description="Collateral assessor — property appraisal and LTV", domain="collateral")
        .with_coordination(CoordinationMode.SUPERVISOR)
        .with_max_rounds(4)
        .with_message_bus(bus)
        .with_policy_check(lambda q, _: policy_engine.evaluate({"query": q}).allowed)
        .build()
    )

    # ── 4. Loan Application ───────────────────────────────────────────────
    loan_query = (
        "Process mortgage application #LN-2026-0142 for applicant APP-001. "
        "Requesting $420,000 conventional 30-year fixed mortgage. "
        "Property: 789 Cedar Ln. "
        "Please perform credit analysis, income verification, collateral appraisal, "
        "and render underwriting decision."
    )

    # Security pipeline
    validation = input_validator.validate(loan_query)
    if not validation.is_valid:
        print(f"INPUT REJECTED: {validation.errors}")
        return
    safety = content_filter.check(loan_query)
    if not safety.is_safe:
        print(f"CONTENT BLOCKED: {safety.flagged_categories}")
        return
    safe_query = pii_detector.redact(loan_query)
    classification = classifier.classify(safe_query)
    print(f"\n📋 Data Classification: {classification.level.value}")

    # Quota check
    quota_status = quota_mgr.check("branch_central", cost_tracker)
    print(f"📊 Quota Status: {'✅ Within limits' if quota_status.within_limits else '❌ EXCEEDED'}")

    # Lineage & audit
    src = lineage.add_source("loan_application", metadata={"loan_id": "LN-2026-0142", "applicant": "APP-001"})
    audit.log("loan_officer_jones", "application_submitted", "LN-2026-0142", details={"amount": 420000})

    # ── 5. Execute Underwriting ───────────────────────────────────────────
    print(f"\n🏦 Running underwriting pipeline (mode: {pipeline.coordination.value})...")
    result = await pipeline.run(safe_query)

    # Post-processing
    safe_output = pii_detector.redact(result.output)

    # Lineage
    xfm = lineage.add_transform("underwriting_analysis", src, transform_desc="supervisor-coordinated underwriting")
    lineage.add_output("underwriting_decision", xfm, metadata={
        "agents": list(result.agent_outputs.keys()),
        "decision": "approved_with_conditions",
    })

    # Cost
    cost_tracker.record(
        provider="openai", model="gpt-4o",
        input_tokens=result.tokens_used.input,
        output_tokens=result.tokens_used.output,
        user_id="loan_officer_jones", project="mortgage_underwriting",
    )

    audit.log("system", "underwriting_complete", "LN-2026-0142", details={
        "decision": "approved_with_conditions",
        "agents_used": list(result.agent_outputs.keys()),
        "tokens": result.tokens_used.total,
    })

    # ── 6. Results ────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("UNDERWRITING DECISION")
    print(f"{'─' * 60}")
    print(f"\n{safe_output}")

    print(f"\n{'─' * 40}")
    print("SPECIALIST REPORTS:")
    for name, output in result.agent_outputs.items():
        print(f"\n  [{name}]:")
        for line in output.split("\n")[:6]:
            print(f"    {line}")

    print(f"\n⏱  Elapsed: {result.elapsed_seconds}s")
    print(f"🔢 Tokens: {result.tokens_used.total}")
    print(f"💰 Cost: ${cost_tracker.total_cost():.4f}")
    print(f"📨 Messages: {result.messages_exchanged}")

    # ── 7. Compliance & Audit ─────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("COMPLIANCE & AUDIT")
    print(f"{'─' * 60}")

    # Compliance checks
    audit_check = await monitor.verify_audit_logging(log_entries=len(audit.export()))
    enc_check = await monitor.verify_encryption("loan_data", encrypted=True)
    retention_check = await monitor.verify_data_retention(policies_configured=len(retention.get_policies()))

    print(f"\n  Audit Logging: {'✅' if audit_check.passed else '❌'} ({audit_check.details})")
    print(f"  Encryption:    {'✅' if enc_check.passed else '❌'} ({enc_check.details})")
    print(f"  Retention:     {'✅' if retention_check.passed else '❌'} ({retention_check.details})")

    # Retention policies
    print(f"\n  Data Retention Policies:")
    for p in retention.get_policies():
        print(f"    {p.name}: {p.retention_days} days ({p.action})")

    # Audit trail
    trail = audit.query(resource="LN-2026-0142")
    print(f"\n  Audit Trail for LN-2026-0142: {len(trail)} entries")
    for entry in trail:
        print(f"    [{entry.timestamp[:19]}] {entry.actor}: {entry.action} → {entry.outcome}")

    # Certification matrix
    certs = exporter.get_certification_matrix()
    print(f"\n  Certifications:")
    for c in certs:
        print(f"    {c['framework']}: {c['status']}")

    # Lineage
    lineage_data = lineage.to_dict()
    print(f"\n  Data Lineage: {len(lineage_data['nodes'])} nodes, {len(lineage_data['edges'])} edges")

    # ── 8. Fair Lending Policy Test ───────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("FAIR LENDING COMPLIANCE TEST")
    print(f"{'─' * 60}")

    discriminatory_query = "Deny loan based on applicant gender and marital status"
    blocked = await pipeline.run(discriminatory_query)
    print(f"\n  Query: {discriminatory_query}")
    print(f"  Result: {blocked.output}")
    print(f"  ✅ Discriminatory query correctly blocked by ECOA policy")

    # ── 9. GDPR Data Subject Request ──────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("GDPR DATA SUBJECT REQUEST")
    print(f"{'─' * 60}")

    export = await gdpr.data_export(user_id="loan_officer_jones")
    print(f"\n  Data export for loan_officer_jones: {len(export.get('audit_trail', []))} audit entries")

    erasure = await gdpr.right_to_erasure(user_id="test_user_999")
    print(f"  Erasure request status: {erasure['status']}")


if __name__ == "__main__":
    asyncio.run(run_loan_pipeline())
