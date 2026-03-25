"""
Example 07 — Medical Domain: HIPAA-Compliant Multi-Agent Clinical Pipeline
==========================================================================
Real-time use case: A hospital AI system where multiple specialised agents
collaborate to assist clinicians with patient triage, diagnosis support,
drug interaction checks, and medical record summarisation.

Demonstrates:
  - Multi-agent hierarchical orchestration (Supervisor → Specialist agents)
  - HIPAA compliance with PHI detection and redaction
  - PII/PHI guardrails on every agent input/output
  - Cost tracking per department / per patient encounter
  - Audit logging for regulatory trail
  - Policy-based security (deny if PHI leak detected in output)
  - Data lineage tracking for provenance
  - Resilience: circuit breaker on LLM endpoints

Run:
    python examples/07_medical_domain.py
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
    Tool,
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
)
from ai_shared.logging_utils import get_logger
from ai_shared.security import ContentFilter, InputValidator, PIIDetector

logger = get_logger("example.medical")


# ── Medical Tools ─────────────────────────────────────────────────────────────

@tool("check_drug_interactions", "Check for drug-drug interactions")
async def check_drug_interactions(drugs: str) -> str:
    """Simulate a drug interaction lookup from a pharmacy database."""
    interaction_db = {
        ("warfarin", "aspirin"): "HIGH RISK: Increased bleeding risk. Monitor INR closely.",
        ("metformin", "contrast_dye"): "MODERATE: Risk of lactic acidosis. Hold metformin 48h.",
        ("lisinopril", "potassium"): "MODERATE: Risk of hyperkalemia. Monitor K+ levels.",
        ("simvastatin", "amiodarone"): "HIGH RISK: Rhabdomyolysis. Max simvastatin 20mg.",
    }
    drug_list = [d.strip().lower() for d in drugs.split(",")]
    interactions = []
    for i, d1 in enumerate(drug_list):
        for d2 in drug_list[i + 1:]:
            key = tuple(sorted([d1, d2]))
            if key in interaction_db:
                interactions.append(f"{d1} + {d2}: {interaction_db[key]}")
    return "\n".join(interactions) if interactions else "No known interactions found."


@tool("lookup_icd10", "Look up ICD-10 diagnosis codes")
async def lookup_icd10(symptoms: str) -> str:
    """Simulate ICD-10 code lookup from symptoms."""
    code_map = {
        "chest pain": "R07.9 — Chest pain, unspecified",
        "shortness of breath": "R06.0 — Dyspnea",
        "fever": "R50.9 — Fever, unspecified",
        "headache": "R51 — Headache",
        "diabetes": "E11.9 — Type 2 diabetes mellitus without complications",
        "hypertension": "I10 — Essential (primary) hypertension",
        "cough": "R05 — Cough",
        "fatigue": "R53.83 — Other fatigue",
    }
    symptom_list = [s.strip().lower() for s in symptoms.split(",")]
    codes = [code_map[s] for s in symptom_list if s in code_map]
    return "\n".join(codes) if codes else "No matching ICD-10 codes found."


@tool("patient_vitals", "Retrieve latest patient vitals")
async def patient_vitals(patient_id: str) -> str:
    """Simulate EHR vitals retrieval (redacted for demo)."""
    vitals = {
        "P001": {"bp": "145/92", "hr": 88, "temp": 98.6, "spo2": 96, "weight_kg": 82},
        "P002": {"bp": "120/80", "hr": 72, "temp": 101.3, "spo2": 94, "weight_kg": 65},
        "P003": {"bp": "160/100", "hr": 95, "temp": 98.2, "spo2": 97, "weight_kg": 110},
    }
    v = vitals.get(patient_id)
    if v:
        return json.dumps(v)
    return "Patient not found."


@tool("lab_results", "Retrieve recent lab results")
async def lab_results(patient_id: str) -> str:
    """Simulate lab result retrieval."""
    labs = {
        "P001": {"hba1c": 7.8, "creatinine": 1.4, "potassium": 5.1, "inr": 2.8},
        "P002": {"wbc": 14.2, "crp": 45.0, "procalcitonin": 1.2, "lactate": 2.8},
    }
    result = labs.get(patient_id)
    return json.dumps(result) if result else "No recent labs found."


# ── Mock LLM for demo ────────────────────────────────────────────────────────

class MockMedicalLLM:
    """Mock LLM that returns domain-appropriate responses for medical demo."""

    def __init__(self, role: str = "general") -> None:
        self.role = role

    async def generate(self, prompt: str) -> "MockResponse":
        if "triage" in self.role:
            text = (
                "Based on vitals (BP 145/92, elevated K+ 5.1, HbA1c 7.8), "
                "this patient requires URGENT review. Risk factors: uncontrolled diabetes, "
                "borderline hyperkalemia, elevated INR 2.8 on warfarin. "
                "Recommend: hold potassium supplements, check INR, nephrology consult."
            )
        elif "pharmacist" in self.role:
            text = (
                "Drug review: Warfarin INR 2.8 (therapeutic 2.0-3.0 but high end). "
                "Aspirin co-prescription increases bleeding risk. "
                "Metformin appropriate for HbA1c 7.8 but monitor renal function (Cr 1.4). "
                "Recommend: reduce warfarin dose, discontinue aspirin, recheck INR in 3 days."
            )
        elif "diagnosis" in self.role:
            text = (
                "Assessment: Type 2 Diabetes (E11.9) with suboptimal control, "
                "Essential Hypertension (I10), "
                "Chronic Kidney Disease stage 3a (N18.31) — Cr 1.4 with eGFR ~55. "
                "Warfarin anticoagulation with supratherapeutic INR. "
                "Plan: optimise glycemic control, renal-dose medications, INR management."
            )
        elif "supervisor" in self.role or "manager" in self.role:
            if "Synthesize" in prompt or "synthesize" in prompt:
                text = (
                    "CLINICAL SUMMARY for Patient P001:\n"
                    "1. TRIAGE: Urgent — hyperkalemia risk + elevated INR\n"
                    "2. DIAGNOSES: T2DM (E11.9), HTN (I10), CKD 3a (N18.31)\n"
                    "3. MEDICATIONS: Adjust warfarin, stop aspirin, monitor metformin\n"
                    "4. ACTIONS: Nephrology consult, recheck INR 3 days, K+ monitoring"
                )
            else:
                text = (
                    "CALL triage_agent to assess vitals, "
                    "CALL pharmacist_agent for drug review, "
                    "CALL diagnosis_agent for clinical assessment."
                )
        else:
            text = f"Medical analysis complete for query: {prompt[:100]}..."

        return MockResponse(text=text)

    async def chat(self, messages: list) -> "MockResponse":
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return await self.generate(last_user)


class MockResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.usage = type("U", (), {"input": 250, "output": 150, "total": 400})()


# ── Main Pipeline ─────────────────────────────────────────────────────────────

async def run_medical_pipeline() -> None:
    print("=" * 70)
    print("  MEDICAL DOMAIN — HIPAA-Compliant Multi-Agent Clinical Pipeline")
    print("=" * 70)

    # ── 1. Security & Compliance Setup ────────────────────────────────────
    pii_detector = PIIDetector()
    content_filter = ContentFilter()
    input_validator = InputValidator(max_length=50_000)
    audit = AuditLogger()
    lineage = DataLineageTracker()
    classifier = DataClassifier(rules={"patient": "restricted", "diagnosis": "confidential"})
    cost_tracker = CostTracker()

    # Policy: block any output that leaks PHI
    policy_engine = PolicyEngine()
    policy_engine.add_policy(Policy(
        name="hipaa_phi_guard",
        condition="'ssn' in query.lower() or 'social security' in query.lower()",
        action="deny",
        description="Block queries requesting SSN/PHI directly",
    ))

    # Compliance monitor with real checks
    monitor = ComplianceMonitor()
    exporter = ComplianceExporter()
    exporter.register_certification(CertificationRecord(
        framework=ComplianceFramework.HIPAA,
        status=CertificationStatus.IMPLEMENTED,
        target_date="2026-01-01",
        evidence="BAA signed, PHI encryption at rest + transit",
    ))
    exporter.register_certification(CertificationRecord(
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.IMPLEMENTED,
        target_date="2026-06-01",
        evidence="Annual SOC2 Type II audit",
    ))

    # ── 2. Build Specialist Agents ────────────────────────────────────────
    triage_llm = MockMedicalLLM(role="triage")
    pharma_llm = MockMedicalLLM(role="pharmacist")
    diagnosis_llm = MockMedicalLLM(role="diagnosis")
    supervisor_llm = MockMedicalLLM(role="supervisor")

    triage_agent = AgentExecutor.create(AgentType.REACT, triage_llm, [patient_vitals, lab_results])
    pharma_agent = AgentExecutor.create(AgentType.REACT, pharma_llm, [check_drug_interactions])
    diagnosis_agent = AgentExecutor.create(AgentType.REACT, diagnosis_llm, [lookup_icd10])
    supervisor = AgentExecutor.create(AgentType.PLAN_EXECUTE, supervisor_llm)

    # ── 3. Multi-Agent Orchestration ──────────────────────────────────────
    bus = MessageBus()

    pipeline = (
        AgentPipelineBuilder()
        .add_agent("supervisor", supervisor, role_description="Clinical supervisor — coordinates care team", priority=10)
        .add_agent("triage_agent", triage_agent, role_description="Triage nurse — vitals assessment", domain="triage")
        .add_agent("pharmacist_agent", pharma_agent, role_description="Clinical pharmacist — drug review", domain="pharmacy")
        .add_agent("diagnosis_agent", diagnosis_agent, role_description="Attending physician — diagnosis", domain="diagnosis")
        .with_coordination(CoordinationMode.HIERARCHICAL)
        .with_max_rounds(2)
        .with_message_bus(bus)
        .with_policy_check(lambda q, _: not pii_detector.has_pii(q))
        .build()
    )

    # ── 4. Patient Encounter ──────────────────────────────────────────────
    patient_query = (
        "Patient P001 presents with elevated blood pressure and fatigue. "
        "Currently on warfarin, aspirin, metformin, and lisinopril. "
        "Please perform triage assessment, drug interaction review, and clinical diagnosis."
    )

    # Validate & filter input
    validation = input_validator.validate(patient_query)
    if not validation.is_valid:
        print(f"INPUT REJECTED: {validation.errors}")
        return

    safety = content_filter.check(patient_query)
    if not safety.is_safe:
        print(f"CONTENT BLOCKED: {safety.flagged_categories}")
        return

    # Redact any PII before processing
    safe_query = pii_detector.redact(patient_query)

    # Track lineage
    source_id = lineage.add_source("patient_encounter", metadata={"patient_id": "P001"})
    classify_result = classifier.classify(safe_query)
    print(f"\n📋 Data Classification: {classify_result.level.value}")

    # Audit log
    audit.log("dr.smith", "patient_encounter", "P001", details={"query": safe_query[:100]})

    # ── 5. Execute Multi-Agent Pipeline ───────────────────────────────────
    print(f"\n🏥 Running clinical pipeline (mode: {pipeline.coordination.value})...")
    result = await pipeline.run(safe_query)

    # ── 6. Post-Processing ────────────────────────────────────────────────
    # Redact any PHI from output
    safe_output = pii_detector.redact(result.output)

    # Track cost
    cost_tracker.record(
        provider="openai", model="gpt-4o",
        input_tokens=result.tokens_used.input,
        output_tokens=result.tokens_used.output,
        user_id="dr.smith", project="cardiology_dept",
    )

    # Lineage
    process_id = lineage.add_transform("multi_agent_analysis", source_id, transform_desc="hierarchical orchestration")
    lineage.add_output("clinical_summary", process_id, metadata={"agents": list(result.agent_outputs.keys())})

    # Audit
    audit.log("system", "clinical_analysis_complete", "P001", details={
        "agents_used": list(result.agent_outputs.keys()),
        "tokens": result.tokens_used.total,
        "elapsed_seconds": result.elapsed_seconds,
    })

    # ── 7. Results ────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("CLINICAL ANALYSIS RESULT")
    print(f"{'─' * 60}")
    print(f"\n{safe_output}")
    print(f"\n📊 Agents involved: {list(result.agent_outputs.keys())}")
    print(f"⏱  Elapsed: {result.elapsed_seconds}s")
    print(f"🔢 Tokens: {result.tokens_used.total}")
    print(f"💰 Cost: ${cost_tracker.total_cost():.4f}")
    print(f"📨 Messages exchanged: {result.messages_exchanged}")

    # ── 8. Compliance Report ──────────────────────────────────────────────
    hipaa_check = await monitor.run_all()
    enc = await monitor.verify_encryption("patient_data", encrypted=True)
    phi_check = await monitor.verify_hipaa_phi_protection(pii_detector_enabled=True)

    print(f"\n🔒 HIPAA PHI Protection: {'✅' if phi_check.passed else '❌'}")
    print(f"🔐 Encryption Check: {'✅' if enc.passed else '❌'}")

    cert_matrix = exporter.get_certification_matrix()
    print(f"\n📜 Certification Matrix:")
    for cert in cert_matrix:
        print(f"   {cert['framework']}: {cert['status']} (target: {cert['target_date']})")

    # Audit trail
    trail = audit.query(resource="P001")
    print(f"\n📝 Audit Trail ({len(trail)} entries for P001)")

    # Individual agent outputs
    print(f"\n{'─' * 60}")
    print("INDIVIDUAL AGENT OUTPUTS")
    print(f"{'─' * 60}")
    for agent_name, output in result.agent_outputs.items():
        print(f"\n[{agent_name}]:")
        print(f"  {output[:200]}...")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(run_medical_pipeline())
