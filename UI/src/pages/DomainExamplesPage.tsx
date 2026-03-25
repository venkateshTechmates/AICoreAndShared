import { useState } from 'react';
import { SectionHeader, CodeBlock } from '../components/ui';
import { Stethoscope, ShoppingCart, Home, Landmark, ChevronRight, Shield, Zap, GitBranch } from 'lucide-react';

// ── Data ─────────────────────────────────────────────────────

const DOMAINS = [
  {
    key: 'medical',
    icon: Stethoscope,
    color: 'blue',
    title: 'Medical Records AI',
    subtitle: 'HIPAA-compliant hierarchical multi-agent system',
    file: 'examples/07_medical_domain.py',
    mode: 'Hierarchical',
    compliance: ['HIPAA', 'PHI Protection', 'Audit Logging'],
    agents: ['TriageAgent', 'DiagnosticsAgent', 'MedicationAgent', 'RecordsAgent', 'SupervisorAgent'],
    description:
      'Processes patient records through a hierarchical coordinator that routes tasks to specialised clinical agents. All PHI is detected, redacted, and audit-logged before any LLM call. HIPAA encryption and RBAC verification run on pipeline entry.',
    useCases: ['Electronic Health Record analysis', 'Clinical decision support', 'Medication interaction checks', 'Patient intake triage'],
    archSteps: [
      { label: 'Intake', detail: 'Patient data ingested; PII/PHI scanned' },
      { label: 'Compliance', detail: 'HIPAA verify_encryption + verify_rbac_enforcement' },
      { label: 'Triage', detail: 'TriageAgent classifies urgency and routes task' },
      { label: 'Specialists', detail: 'DiagnosticsAgent / MedicationAgent run in parallel' },
      { label: 'Supervisor', detail: 'RecordsAgent consolidates; SupervisorAgent QA check' },
      { label: 'Audit', detail: 'Full audit trail written; response returned' },
    ],
    code: `from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode
from ai_shared.compliance import ComplianceManager, Framework
from ai_shared.security import PIIDetector
from ai_shared.governance import AuditLogger

# ── Compliance gate ───────────────────────────────────────────
mgr = ComplianceManager()
await mgr.verify_encryption(resource="patient-db", encrypted=True)
await mgr.verify_rbac_enforcement(roles_configured=True)

# ── PII guard ────────────────────────────────────────────────
detector = PIIDetector()
phi_matches = detector.detect(patient_note)
safe_text   = detector.redact(patient_note)

# ── Multi-agent system ────────────────────────────────────────
system = MultiAgentSystem(
    agents=[triage, diagnostics, medication, records],
    mode=CoordinationMode.HIERARCHICAL,
)
result = await system.run(
    f"Analyse patient record: {safe_text}",
    context={"patient_id": "P-2024-001", "department": "cardiology"},
)

# ── Audit trail ──────────────────────────────────────────────
audit = AuditLogger(service="medical-ai", log_level="INFO")
await audit.log_event(
    event_type="phi_access",
    user_id="dr.smith",
    resource="patient_record",
    action="read",
    outcome="redacted_and_processed",
)`,
  },
  {
    key: 'ecommerce',
    icon: ShoppingCart,
    color: 'emerald',
    title: 'E-commerce Intelligence',
    subtitle: 'Parallel + swarm agents for order and inventory management',
    file: 'examples/08_ecommerce_domain.py',
    mode: 'Parallel + Swarm',
    compliance: ['SOC2', 'Data Residency', 'Rate Limiting'],
    agents: ['PricingAgent', 'InventoryAgent', 'ReviewAgent', 'RecommendationAgent', 'FraudAgent'],
    description:
      'Runs five specialised agents in parallel across pricing, inventory, reviews, recommendations, and fraud detection. A swarm coordination phase merges the parallel outputs into a unified product-intelligence brief.',
    useCases: ['Real-time product pricing', 'Inventory optimisation', 'Personalised recommendations', 'Fraud detection at checkout'],
    archSteps: [
      { label: 'Order Event', detail: 'Order or product query arrives via API' },
      { label: 'Parallel Fan-out', detail: '5 agents start simultaneously' },
      { label: 'PricingAgent', detail: 'Dynamic price model with competitor data' },
      { label: 'InventoryAgent', detail: 'Stock levels + reorder thresholds' },
      { label: 'ReviewAgent', detail: 'Sentiment scoring on recent reviews' },
      { label: 'Swarm Merge', detail: 'Results combined into product brief' },
    ],
    code: `from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

# ── Phase 1: Parallel intelligence gathering ──────────────────
parallel_system = MultiAgentSystem(
    agents=[pricing_agent, inventory_agent, review_agent, fraud_agent],
    mode=CoordinationMode.PARALLEL,
)
parallel_result = await parallel_system.run(
    f"Evaluate product SKU-{sku} for customer order",
    context={"customer_tier": "premium", "cart_value": 349.99},
)

# ── Phase 2: Swarm consensus on recommendations ───────────────
swarm_system = MultiAgentSystem(
    agents=[recommendation_agent, pricing_agent],
    mode=CoordinationMode.SWARM,
)
final = await swarm_system.run(
    "Combine intel and generate personalised offer",
    context={"parallel_outputs": parallel_result.results},
)

print(f"Recommended price : {final.results['price']}")
print(f"Stock status      : {final.results['inventory']}")
print(f"Fraud risk        : {final.results['fraud_score']}")`,
  },
  {
    key: 'realestate',
    icon: Home,
    color: 'amber',
    title: 'Real Estate Valuation',
    subtitle: 'Debate coordination for multi-perspective property appraisal',
    file: 'examples/09_real_estate_domain.py',
    mode: 'Debate',
    compliance: ['RESPA', 'Fair-Lending', 'Data Privacy'],
    agents: ['BullishAppraiserAgent', 'BearishAppraiserAgent', 'MarketAnalystAgent', 'RegulatoryAgent'],
    description:
      'Two opposing appraiser agents debate the property value across three rounds. A market analyst moderates, and a regulatory agent validates fair-lending compliance before the final consensus estimate is returned.',
    useCases: ['Automated property valuation (AVM)', 'Investment risk assessment', 'Mortgage appraisal support', 'Portfolio stress testing'],
    archSteps: [
      { label: 'Property Data', detail: 'Comps, zoning, market trends ingested via RAG' },
      { label: 'Round 1', detail: 'Bull/Bear agents give independent valuations' },
      { label: 'Round 2', detail: 'Each agent critiques the other\'s reasoning' },
      { label: 'Round 3', detail: 'Agents narrow to a negotiated range' },
      { label: 'Moderation', detail: 'MarketAnalystAgent arbitrates consensus' },
      { label: 'Compliance', detail: 'RegulatoryAgent checks fair-lending rules' },
    ],
    code: `from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

# ── Debate system — 3 rounds of structured argumentation ──────
debate_system = MultiAgentSystem(
    agents=[bullish_appraiser, bearish_appraiser, market_analyst],
    mode=CoordinationMode.DEBATE,
    rounds=3,
)

property_context = {
    "address":    "123 Oak Street, Austin TX",
    "bedrooms":   4,
    "sqft":       2850,
    "lot_size":   0.35,
    "year_built": 2008,
    "recent_comps": [680000, 725000, 695000],
}

result = await debate_system.run(
    "Provide a fair market value estimate with confidence interval",
    context=property_context,
)

print(f"Consensus value : {result.consensus}")
print(f"Bull estimate   : {result.results['bullish_appraiser']}")
print(f"Bear estimate   : {result.results['bearish_appraiser']}")
print(f"Debate rounds   : {result.metadata['rounds_completed']}")`,
  },
  {
    key: 'loan',
    icon: Landmark,
    color: 'purple',
    title: 'Loan Underwriting',
    subtitle: 'Supervisor coordination for automated credit decisioning',
    file: 'examples/10_loan_processing_domain.py',
    mode: 'Supervisor',
    compliance: ['PCI-DSS', 'FCRA', 'ECOA', 'BSA/AML'],
    agents: ['IntakeAgent', 'CreditAgent', 'IncomeAgent', 'PropertyAgent', 'AMLAgent', 'UnderwiterAgent'],
    description:
      'A supervisor LLM orchestrates the full mortgage underwriting pipeline, dynamically routing each application stage to the appropriate specialist agent. AML screening, income verification, and credit scoring run independently; the underwriter agent makes the final decision.',
    useCases: ['Mortgage pre-qualification', 'Credit risk scoring', 'AML / fraud screening', 'Automated loan decisioning'],
    archSteps: [
      { label: 'Application', detail: 'Loan application submitted with supporting docs' },
      { label: 'PCI-DSS Gate', detail: 'Payment data encrypted; SSN/account masked' },
      { label: 'Supervisor', detail: 'Coordinator analyses and assigns sub-tasks' },
      { label: 'Credit Check', detail: 'CreditAgent queries bureau data' },
      { label: 'Income + AML', detail: 'IncomeAgent and AMLAgent run concurrently' },
      { label: 'Decision', detail: 'UnderwriterAgent issues approve / deny / refer' },
    ],
    code: `from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode
from ai_shared.compliance import ComplianceManager
from ai_shared.security import PIIDetector, InputValidator

# ── PCI-DSS compliance gate ────────────────────────────────────
mgr = ComplianceManager()
await mgr.verify_encryption(resource="loan-db", encrypted=True)

# ── Sanitise sensitive fields ─────────────────────────────────
validator = InputValidator()
result = validator.validate(application_json)
if not result.is_valid:
    raise ValueError(f"Invalid input: {result.errors}")

detector = PIIDetector()
safe_application = detector.redact(str(application_json))

# ── Supervisor orchestration ──────────────────────────────────
underwriting_system = MultiAgentSystem(
    agents=[intake, credit, income, property_agent, aml, underwriter],
    mode=CoordinationMode.SUPERVISOR,
)
decision = await underwriting_system.run(
    f"Process loan application: {safe_application}",
    context={
        "loan_amount": 450000,
        "loan_type":   "30yr-fixed",
        "ltv_ratio":   0.80,
    },
)

print(f"Decision  : {decision.results['decision']}")     # APPROVE / DENY / REFER
print(f"Rate      : {decision.results['rate']}")
print(f"Reasoning : {decision.results['reasoning']}")`,
  },
] as const;

// ── Colour helpers ────────────────────────────────────────────

const colorMap: Record<string, { bg: string; badge: string; ring: string; icon: string }> = {
  blue:    { bg: 'bg-blue-50',    badge: 'bg-blue-100 text-blue-700',    ring: 'ring-blue-300',   icon: 'text-blue-600' },
  emerald: { bg: 'bg-emerald-50', badge: 'bg-emerald-100 text-emerald-700', ring: 'ring-emerald-300', icon: 'text-emerald-600' },
  amber:   { bg: 'bg-amber-50',   badge: 'bg-amber-100 text-amber-700',  ring: 'ring-amber-300',  icon: 'text-amber-600' },
  purple:  { bg: 'bg-purple-50',  badge: 'bg-purple-100 text-purple-700', ring: 'ring-purple-300', icon: 'text-purple-600' },
};

// ── Sub-components ────────────────────────────────────────────

const ArchFlowStep = ({ step, index }: { step: { label: string; detail: string }; index: number }) => (
  <div className="flex items-start gap-3">
    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-zinc-900 text-white text-[10px] font-bold flex items-center justify-center mt-0.5">
      {index + 1}
    </div>
    <div>
      <span className="text-sm font-semibold text-zinc-800">{step.label}</span>
      <span className="text-xs text-zinc-500 ml-2">{step.detail}</span>
    </div>
  </div>
);

const ModeBadge = ({ mode }: { mode: string }) => (
  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-zinc-900 text-white text-[11px] font-mono">
    <GitBranch className="w-3 h-3" />{mode}
  </span>
);

// ── Main page ─────────────────────────────────────────────────

const DomainExamplesPage = () => {
  const [active, setActive] = useState<string>('medical');
  const domain = DOMAINS.find(d => d.key === active)!;
  const c = colorMap[domain.color];
  const Icon = domain.icon;

  return (
    <div className="space-y-8">
      <SectionHeader
        badge="Real-World"
        title="Domain Examples"
        subtitle="Production-grade multi-agent pipelines for regulated industries. Each example ships as a runnable Python script."
      />

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Domains', value: '4', icon: <Zap className="w-4 h-4 text-zinc-500" /> },
          { label: 'Coordination Modes', value: '6', icon: <GitBranch className="w-4 h-4 text-zinc-500" /> },
          { label: 'Compliance Frameworks', value: '8+', icon: <Shield className="w-4 h-4 text-zinc-500" /> },
          { label: 'Example Agents', value: '20+', icon: <ChevronRight className="w-4 h-4 text-zinc-500" /> },
        ].map(stat => (
          <div key={stat.label} className="p-4 bg-white border border-zinc-200 rounded-xl flex items-center gap-3">
            {stat.icon}
            <div>
              <div className="text-xl font-bold text-zinc-900">{stat.value}</div>
              <div className="text-xs text-zinc-500">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Domain selector tabs */}
      <div className="flex flex-wrap gap-2">
        {DOMAINS.map(d => {
          const Ic = d.icon;
          const cc = colorMap[d.color];
          return (
            <button
              key={d.key}
              onClick={() => setActive(d.key)}
              className={
                'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all border ' +
                (active === d.key
                  ? `${cc.bg} border-transparent ring-1 ${cc.ring} text-zinc-900`
                  : 'bg-white border-zinc-200 text-zinc-600 hover:border-zinc-400')
              }
            >
              <Ic className={`w-4 h-4 ${active === d.key ? cc.icon : 'text-zinc-400'}`} />
              {d.title}
            </button>
          );
        })}
      </div>

      {/* Domain detail card */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Left: overview */}
        <div className="space-y-5">
          <div className={`p-6 ${c.bg} rounded-2xl border border-transparent`}>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-white shadow-sm flex items-center justify-center shrink-0">
                <Icon className={`w-6 h-6 ${c.icon}`} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-zinc-900">{domain.title}</h3>
                <p className="text-sm text-zinc-600 mt-0.5">{domain.subtitle}</p>
                <div className="mt-2">
                  <ModeBadge mode={domain.mode} />
                </div>
              </div>
            </div>
            <p className="mt-4 text-sm text-zinc-700 leading-relaxed">{domain.description}</p>
          </div>

          {/* Compliance badges */}
          <div>
            <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Compliance Frameworks</h4>
            <div className="flex flex-wrap gap-2">
              {domain.compliance.map(f => (
                <span key={f} className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium ${c.badge}`}>
                  <Shield className="w-3 h-3" />{f}
                </span>
              ))}
            </div>
          </div>

          {/* Agents */}
          <div>
            <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Agents</h4>
            <div className="flex flex-wrap gap-2">
              {domain.agents.map(a => (
                <span key={a} className="px-2.5 py-1 bg-white border border-zinc-200 rounded-lg text-xs font-mono text-zinc-700">{a}</span>
              ))}
            </div>
          </div>

          {/* Use cases */}
          <div>
            <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Use Cases</h4>
            <ul className="space-y-1">
              {domain.useCases.map(uc => (
                <li key={uc} className="flex items-center gap-2 text-sm text-zinc-600">
                  <ChevronRight className="w-3.5 h-3.5 text-zinc-400 shrink-0" />{uc}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right: architecture flow + code */}
        <div className="space-y-5">
          <div className="p-5 bg-white border border-zinc-200 rounded-xl">
            <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4">Pipeline Architecture</h4>
            <div className="space-y-3">
              {domain.archSteps.map((step, i) => (
                <div key={i}>
                  <ArchFlowStep step={step} index={i} />
                  {i < domain.archSteps.length - 1 && (
                    <div className="ml-3 mt-1 h-4 border-l-2 border-dashed border-zinc-200" />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Code Sample</h4>
              <code className="text-[10px] text-zinc-400 font-mono">{domain.file}</code>
            </div>
            <CodeBlock code={domain.code} />
          </div>
        </div>
      </div>

      {/* Coordination modes reference */}
      <div className="p-6 bg-zinc-50 border border-zinc-200 rounded-2xl">
        <h3 className="text-sm font-semibold text-zinc-900 mb-4">Coordination Modes — Quick Reference</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { mode: 'Sequential',   desc: 'Agents run one after another; each builds on prior output.',         icon: '→' },
            { mode: 'Parallel',     desc: 'All agents start at once; results merged at a fan-in step.',         icon: '⇉' },
            { mode: 'Debate',       desc: 'Agents argue over N rounds until consensus emerges.',                 icon: '⇌' },
            { mode: 'Hierarchical', desc: 'Supervisor routes tasks to specialist workers dynamically.',          icon: '⬡' },
            { mode: 'Swarm',       desc: 'Agents collaborate in a shared workspace with fluid coordination.',   icon: '✦' },
            { mode: 'Supervisor',   desc: 'One coordinator manages agents; owns final decision authority.',      icon: '⊛' },
          ].map(item => (
            <div key={item.mode} className="p-4 bg-white border border-zinc-200 rounded-xl">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-base font-mono text-zinc-400">{item.icon}</span>
                <span className="text-sm font-semibold text-zinc-900">{item.mode}</span>
              </div>
              <p className="text-xs text-zinc-500 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DomainExamplesPage;
