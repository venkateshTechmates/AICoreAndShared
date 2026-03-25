# Domain Examples — Real-World Multi-Agent Pipelines

**Version:** 1.1.0  
**Python:** 3.11+

This document covers four production-grade domain examples shipped with the toolkit.
Each example demonstrates a different `CoordinationMode` in a regulated industry context.

---

## Overview

| # | Domain | File | Mode | Compliance |
|---|---|---|---|---|
| 07 | Medical Records AI | `examples/07_medical_domain.py` | Hierarchical | HIPAA, PHI |
| 08 | E-commerce Intelligence | `examples/08_ecommerce_domain.py` | Parallel + Swarm | SOC2 |
| 09 | Real Estate Valuation | `examples/09_real_estate_domain.py` | Debate | RESPA, Fair-Lending |
| 10 | Loan Underwriting | `examples/10_loan_processing_domain.py` | Supervisor | PCI-DSS, FCRA |

---

## 07 — Medical Records AI (`HIERARCHICAL`)

### Use Case

A hospital system needs to process incoming patient records through a pipeline that:
1. Detects and redacts PHI before any LLM call
2. Routes the record to the appropriate clinical specialist (triage, diagnostics, medication)
3. Logs every data access for HIPAA audit purposes

### Architecture

```
Patient Record
     ↓
[PHI Detection + Redaction]  ← PIIDetector.redact()
     ↓
[HIPAA Compliance Gate]      ← verify_encryption + verify_rbac_enforcement
     ↓
[SupervisorAgent]            ← routes to specialist
    ├── [TriageAgent]         ← classify urgency
    ├── [DiagnosticsAgent]    ← ICD-10 coding
    └── [MedicationAgent]     ← drug interaction check
     ↓
[RecordsAgent]               ← consolidate
     ↓
[AuditLogger]                ← write HIPAA audit event
```

### Key Code

```python
from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode
from ai_shared.compliance import ComplianceManager
from ai_shared.security import PIIDetector
from ai_shared.governance import AuditLogger

mgr = ComplianceManager()
await mgr.verify_encryption(resource="patient-db", encrypted=True)
await mgr.verify_rbac_enforcement(roles_configured=True)

detector = PIIDetector()
safe_text = detector.redact(patient_note)     # masks SSN, phone, DOB, etc.

system = MultiAgentSystem(
    agents=[triage, diagnostics, medication, records],
    mode=CoordinationMode.HIERARCHICAL,
)
result = await system.run(
    f"Analyse patient record: {safe_text}",
    context={"patient_id": "P-2024-001", "department": "cardiology"},
)

audit = AuditLogger(service="medical-ai", log_level="INFO")
await audit.log_event(
    event_type="phi_access",
    user_id="dr.smith",
    resource="patient_record",
    action="read",
    outcome="redacted_and_processed",
)
```

### Test Coverage

```bash
pytest tests/test_shared/test_compliance.py -k "hipaa"
pytest tests/test_core/test_agents.py -k "hierarchical"
```

---

## 08 — E-commerce Intelligence (`PARALLEL + SWARM`)

### Use Case

An online retailer needs to evaluate every order in real time for:
- Dynamic pricing based on demand signals
- Inventory and reorder thresholds
- Review sentiment and return risk
- Fraud detection before payment

All four checks must complete within an SLA target, so they run in parallel.
A follow-on swarm phase merges the outputs into a personalised offer.

### Architecture

```
Order Event
     ↓
[PARALLEL fan-out]
    ├── [PricingAgent]         ← demand-based price model
    ├── [InventoryAgent]       ← stock levels + reorder
    ├── [ReviewAgent]          ← sentiment scoring
    └── [FraudAgent]           ← risk scoring
     ↓
[SWARM merge phase]
    ├── [RecommendationAgent]  ← personalise offer
    └── [PricingAgent]         ← apply dynamic discount
     ↓
Unified product brief + personalised offer
```

### Key Code

```python
parallel_system = MultiAgentSystem(
    agents=[pricing_agent, inventory_agent, review_agent, fraud_agent],
    mode=CoordinationMode.PARALLEL,
)
parallel_result = await parallel_system.run(
    f"Evaluate product SKU-{sku} for order #{order_id}",
    context={"customer_tier": "premium", "cart_value": 349.99},
)

swarm_system = MultiAgentSystem(
    agents=[recommendation_agent, pricing_agent],
    mode=CoordinationMode.SWARM,
)
final = await swarm_system.run(
    "Combine intel and generate personalised offer",
    context={"parallel_outputs": parallel_result.results},
)
```

---

## 09 — Real Estate Valuation (`DEBATE`)

### Use Case

A mortgage lender wants an automated valuation model (AVM) that considers both bullish
and bearish market interpretations before issuing a final appraisal, with a
regulatory check to ensure fair-lending compliance.

### Architecture

```
Property Data (comps, zoning, market trends via RAG)
     ↓
[DEBATE — 3 rounds]
    ├── Round 1: BullishAppraiserAgent vs BearishAppraiserAgent (independent)
    ├── Round 2: Cross-critique
    └── Round 3: Narrowed range + negotiated consensus
     ↓
[MarketAnalystAgent]         ← moderates + arbitrates
     ↓
[RegulatoryAgent]            ← fair-lending compliance check
     ↓
Final valuation with confidence interval
```

### Key Code

```python
debate_system = MultiAgentSystem(
    agents=[bullish_appraiser, bearish_appraiser, market_analyst],
    mode=CoordinationMode.DEBATE,
    rounds=3,
)

result = await debate_system.run(
    "Provide a fair market value estimate with confidence interval",
    context={
        "address": "123 Oak Street, Austin TX",
        "bedrooms": 4,
        "sqft": 2850,
        "recent_comps": [680000, 725000, 695000],
    },
)

print(f"Consensus value : {result.consensus}")
print(f"Rounds completed: {result.metadata['rounds_completed']}")
```

---

## 10 — Loan Underwriting (`SUPERVISOR`)

### Use Case

A bank's automated underwriting engine must process mortgage applications through:
1. PCI-DSS compliance gate (encrypt payment data, mask SSN/account numbers)
2. Parallel credit, income, and AML checks
3. A supervisor coordinator that dynamically routes tasks and owns the final decision

### Architecture

```
Loan Application
     ↓
[PCI-DSS Gate]              ← verify_encryption + PIIDetector.redact()
     ↓
[CoordinatorAgent]          ← SUPERVISOR — analyses and dispatches
    ├── [CreditAgent]        ← bureau query + FICO
    ├── [IncomeAgent]        ← W2/bank-statement verification
    ├── [PropertyAgent]      ← collateral appraisal
    └── [AMLAgent]           ← watchlist screening
     ↓
[UnderwriterAgent]          ← final APPROVE / DENY / REFER decision
     ↓
Decision record with reasoning + compliance trail
```

### Key Code

```python
from ai_shared.compliance import ComplianceManager
from ai_shared.security import PIIDetector, InputValidator

# Compliance gate
mgr = ComplianceManager()
await mgr.verify_encryption(resource="loan-db", encrypted=True)

# Sanitise application
validator = InputValidator()
result = validator.validate(application_json)
if not result.is_valid:
    raise ValueError(f"Invalid input: {result.errors}")
safe_application = PIIDetector().redact(str(application_json))

# Supervisor orchestration
underwriting_system = MultiAgentSystem(
    agents=[intake, credit, income, property_agent, aml, underwriter],
    mode=CoordinationMode.SUPERVISOR,
)
decision = await underwriting_system.run(
    f"Process loan application: {safe_application}",
    context={"loan_amount": 450000, "loan_type": "30yr-fixed", "ltv_ratio": 0.80},
)

print(f"Decision  : {decision.results['decision']}")
print(f"Rate      : {decision.results['rate']}")
print(f"Reasoning : {decision.results['reasoning']}")
```

### Test Coverage

```bash
pytest tests/test_shared/test_compliance.py -k "pci"
pytest tests/test_core/test_agents.py -k "supervisor"
pytest tests/test_shared/test_security.py -k "pii"
```

---

## Running the Examples

```bash
# Medical — HIPAA hierarchical
python examples/07_medical_domain.py

# E-commerce — parallel + swarm
python examples/08_ecommerce_domain.py

# Real estate — debate
python examples/09_real_estate_domain.py

# Loan processing — supervisor
python examples/10_loan_processing_domain.py
```

---

## Common Patterns

### Always sanitise before LLM calls

```python
detector = PIIDetector()
safe_input = detector.redact(raw_user_input)
result = await agent.run(safe_input)
```

### Compliance gate at pipeline entry

```python
mgr = ComplianceManager()
for resource in secured_resources:
    await mgr.verify_encryption(resource=resource, encrypted=True)
await mgr.verify_rbac_enforcement(roles_configured=True)
```

### Audit every LLM interaction

```python
audit = AuditLogger(service="my-ai-service", log_level="INFO")
await audit.log_event(
    event_type="llm_call",
    user_id=current_user,
    resource="knowledge_base",
    action="query",
    outcome="success",
)
```
