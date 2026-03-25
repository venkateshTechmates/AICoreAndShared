import { useState } from 'react';
import { SectionHeader, CodeBlock } from '../components/ui';
import { GitBranch, Zap, Users, CheckCircle2 } from 'lucide-react';

const PlaygroundPage = () => {
  const [view, setView] = useState<'rag' | 'prompt' | 'agents'>('rag');
  const tabs = [
    { key: 'rag',    label: 'RAG Pipeline Designer' },
    { key: 'prompt', label: 'Prompt Lab' },
    { key: 'agents', label: 'Multi-Agent Studio' },
  ] as const;
  return (
    <div className="space-y-8">
      <SectionHeader badge="Interactive" title="Playground — Try It Live" subtitle="Interactive RAG pipeline designer, prompt engineering lab, and multi-agent coordinator." />
      <div className="flex flex-wrap gap-2">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setView(t.key)} className={'px-4 py-2 rounded-lg text-sm font-medium transition-colors ' + (view === t.key ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200')}>{t.label}</button>
        ))}
      </div>
      {view === 'rag' ? <RAGDesigner /> : view === 'prompt' ? <PromptLab /> : <MultiAgentStudio />}
    </div>
  );
};

// ── RAG Designer ──────────────────────────────────────────────
const RAGDesigner = () => {
  const [selectedStep, setSelectedStep] = useState(0);
  const steps = [
    { step: '01', title: 'Ingestion', desc: 'PDF, CSV, JSON, Web, SQL', details: 'Configure connectors for document sources with auto-sync.' },
    { step: '02', title: 'Chunking', desc: 'Semantic, Recursive, Fixed', details: 'Semantic boundary detection with 512 token window.' },
    { step: '03', title: 'Embedding', desc: 'OpenAI, Cohere, HuggingFace', details: 'text-embedding-3-large with 3072 dimensions.' },
    { step: '04', title: 'Vector Store', desc: 'Qdrant, Pinecone, Weaviate', details: 'Qdrant cluster with HNSW indexing enabled.' },
    { step: '05', title: 'Search', desc: 'Hybrid, MMR, Reranking', details: 'Hybrid search (Alpha: 0.5) with Cohere reranker.' },
    { step: '06', title: 'Generation', desc: 'GPT-4o, Claude 3, Llama 3', details: 'GPT-4o with Chain-of-Thought prompting.' },
  ];
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {steps.map((item, i) => (
          <div key={i} onClick={() => setSelectedStep(i)} className={'p-5 bg-white border rounded-xl cursor-pointer transition-all ' + (selectedStep === i ? 'border-zinc-900 ring-1 ring-zinc-900' : 'border-zinc-200 hover:border-zinc-400')}>
            <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">{item.step}</span>
            <h4 className="font-semibold text-zinc-900 mt-1">{item.title}</h4>
            <p className="text-xs text-zinc-500 mt-1">{item.desc}</p>
          </div>
        ))}
      </div>
      <div className="p-6 bg-zinc-50 border border-zinc-200 rounded-xl">
        <h4 className="font-semibold text-zinc-900 mb-2">{steps[selectedStep].title} Configuration</h4>
        <p className="text-sm text-zinc-600">{steps[selectedStep].details}</p>
      </div>
      <CodeBlock code={'from ai_core import AICore\n\nai = AICore.from_yaml(\"config.yml\")\n\nawait ai.ingest(documents=[\"docs/report.pdf\"], chunking=\"semantic\", namespace=\"finance\")\n\nresponse = await ai.query(\n    query=\"What were the Q4 revenue drivers?\",\n    search_strategy=\"hybrid\",\n    prompt_technique=\"chain_of_thought\",\n)\nprint(response.answer)\nprint(response.citations)'} />
    </div>
  );
};

// ── Prompt Lab ────────────────────────────────────────────────
const PromptLab = () => {
  const [technique, setTechnique] = useState('chain_of_thought');
  const techniques = [
    { key: 'chain_of_thought', label: 'Chain of Thought', desc: 'Step-by-step reasoning for complex problems' },
    { key: 'few_shot', label: 'Few-Shot', desc: 'Provide examples for consistent formatting' },
    { key: 'react', label: 'ReAct', desc: 'Reason + Act: multi-step agent prompts' },
    { key: 'tree_of_thought', label: 'Tree of Thought', desc: 'Explore multiple reasoning branches' },
    { key: 'self_consistency', label: 'Self-Consistency', desc: 'Sample multiple paths and aggregate' },
    { key: 'role_based', label: 'Role Prompting', desc: 'Set expert persona for the model' },
    { key: 'meta', label: 'Meta Prompting', desc: 'Prompt that generates optimized prompts' },
    { key: 'rag_fusion', label: 'RAG Fusion', desc: 'Multi-query retrieval with reciprocal rank fusion' },
  ];
  const selectedTech = techniques.find(t => t.key === technique)!;
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {techniques.map(t => (
          <button key={t.key} onClick={() => setTechnique(t.key)} className={'px-3 py-1.5 rounded-full text-xs font-medium transition-all ' + (technique === t.key ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200')}>{t.label}</button>
        ))}
      </div>
      <div className="p-6 bg-zinc-50 border border-zinc-200 rounded-xl space-y-4">
        <h4 className="font-semibold text-zinc-900">{selectedTech.label}</h4>
        <p className="text-sm text-zinc-600">{selectedTech.desc}</p>
        <div className="space-y-3">
          <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider">System Prompt</label>
          <textarea readOnly className="w-full h-24 text-sm p-3 bg-white border border-zinc-200 rounded-lg font-mono resize-none" value={'You are a senior data analyst. Use ' + selectedTech.label + ' to analyze the context and provide structured answers.'} />
          <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider">User Query</label>
          <textarea readOnly className="w-full h-16 text-sm p-3 bg-white border border-zinc-200 rounded-lg font-mono resize-none" value="What were the key revenue drivers in Q4? Provide a breakdown by business unit." />
        </div>
      </div>
      <CodeBlock code={'from ai_core.prompt_engine import PromptEngine\n\nengine = PromptEngine()\n\nprompt = engine.build(\n    technique=\"' + technique + '\",\n    system=\"Senior data analyst persona\",\n    query=\"Q4 revenue drivers analysis\",\n    context=retrieved_chunks,\n)\n\nresult = await engine.execute(prompt, model=\"gpt-4o\")\nprint(result.answer)\nprint(f\"Tokens: {result.usage.total_tokens}\")'} />
    </div>
  );
};

// ── Multi-Agent Studio ────────────────────────────────────────

const COORDINATION_MODES = [
  {
    key: 'sequential',
    label: 'Sequential',
    icon: '→',
    desc: 'Agents run one after another; each stage receives prior output.',
    color: 'bg-blue-50 border-blue-200',
    active: 'bg-blue-900 text-white',
  },
  {
    key: 'parallel',
    label: 'Parallel',
    icon: '⇉',
    desc: 'All agents start simultaneously; results fan in at the merge step.',
    color: 'bg-emerald-50 border-emerald-200',
    active: 'bg-emerald-900 text-white',
  },
  {
    key: 'debate',
    label: 'Debate',
    icon: '⇌',
    desc: 'Agents exchange critique over N rounds until consensus.',
    color: 'bg-amber-50 border-amber-200',
    active: 'bg-amber-900 text-white',
  },
  {
    key: 'hierarchical',
    label: 'Hierarchical',
    icon: '⬡',
    desc: 'Supervisor delegates tasks to specialist workers dynamically.',
    color: 'bg-violet-50 border-violet-200',
    active: 'bg-violet-900 text-white',
  },
  {
    key: 'swarm',
    label: 'Swarm',
    icon: '✦',
    desc: 'Agents collaborate in a shared workspace with fluid coordination.',
    color: 'bg-rose-50 border-rose-200',
    active: 'bg-rose-900 text-white',
  },
  {
    key: 'supervisor',
    label: 'Supervisor',
    icon: '⊛',
    desc: 'One coordinator manages all agents; owns the final decision.',
    color: 'bg-teal-50 border-teal-200',
    active: 'bg-teal-900 text-white',
  },
] as const;

type ModeKey = typeof COORDINATION_MODES[number]['key'];

const MODE_AGENTS: Record<ModeKey, { name: string; role: string }[]> = {
  sequential:   [{ name: 'ResearchAgent', role: 'Gather raw information' }, { name: 'AnalysisAgent', role: 'Structure findings' }, { name: 'WriterAgent', role: 'Draft final report' }],
  parallel:     [{ name: 'PricingAgent', role: 'Dynamic pricing model' }, { name: 'InventoryAgent', role: 'Stock levels' }, { name: 'FraudAgent', role: 'Risk scoring' }, { name: 'ReviewAgent', role: 'Sentiment analysis' }],
  debate:       [{ name: 'BullAgent', role: 'Argue positive thesis' }, { name: 'BearAgent', role: 'Argue negative thesis' }, { name: 'ModeratorAgent', role: 'Arbitrate consensus' }],
  hierarchical: [{ name: 'SupervisorAgent', role: 'Route and coordinate' }, { name: 'TriageAgent', role: 'Classify urgency' }, { name: 'SpecialistAgent', role: 'Domain expert' }],
  swarm:        [{ name: 'ExtractorAgent', role: 'Pull key entities' }, { name: 'ValidatorAgent', role: 'Cross-check facts' }, { name: 'MapperAgent', role: 'Build knowledge graph' }],
  supervisor:   [{ name: 'CoordinatorAgent', role: 'Plan and dispatch' }, { name: 'UnderwriterAgent', role: 'Risk assessment' }, { name: 'ComplianceAgent', role: 'Regulatory check' }],
};

const MODE_CODE: Record<ModeKey, string> = {
  sequential:
`from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

system = MultiAgentSystem(
    agents=[research_agent, analysis_agent, writer_agent],
    mode=CoordinationMode.SEQUENTIAL,
)
result = await system.run("Summarise the Q4 earnings report.")
print(result.final_answer)`,

  parallel:
`from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

system = MultiAgentSystem(
    agents=[pricing_agent, inventory_agent, fraud_agent, review_agent],
    mode=CoordinationMode.PARALLEL,
)
result = await system.run("Evaluate order #ORD-2024-8821")
# result.results contains all agent outputs
for agent_name, output in result.results.items():
    print(f"{agent_name}: {output}")`,

  debate:
`from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

system = MultiAgentSystem(
    agents=[bull_agent, bear_agent, moderator_agent],
    mode=CoordinationMode.DEBATE,
    rounds=3,
)
result = await system.run("Estimate fair value for TSLA Dec 2024")
print(f"Consensus  : {result.consensus}")
print(f"Confidence : {result.metadata['confidence']}")`,

  hierarchical:
`from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

system = MultiAgentSystem(
    agents=[supervisor_agent, triage_agent, specialist_agent],
    mode=CoordinationMode.HIERARCHICAL,
)
result = await system.run(
    "Process patient intake for cardiology",
    context={"priority": "urgent"},
)
print(result.final_answer)`,

  swarm:
`from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

system = MultiAgentSystem(
    agents=[extractor_agent, validator_agent, mapper_agent],
    mode=CoordinationMode.SWARM,
)
result = await system.run("Build a knowledge graph from this document")
print(result.metadata['workspace'])`,

  supervisor:
`from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

system = MultiAgentSystem(
    agents=[coordinator, underwriter, compliance_agent],
    mode=CoordinationMode.SUPERVISOR,
)
result = await system.run(
    "Process loan application #L-2024-5521",
    context={"loan_amount": 350000, "credit_score": 720},
)
print(f"Decision   : {result.results['decision']}")
print(f"Rate offer : {result.results['rate']}")`,
};

const MultiAgentStudio = () => {
  const [mode, setMode] = useState<ModeKey>('sequential');
  const selected = COORDINATION_MODES.find(m => m.key === mode)!;
  const agents = MODE_AGENTS[mode];

  return (
    <div className="space-y-6">
      {/* Mode selector grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {COORDINATION_MODES.map(m => (
          <button
            key={m.key}
            onClick={() => setMode(m.key)}
            className={
              'p-4 text-left border rounded-xl transition-all ' +
              (mode === m.key ? 'border-zinc-900 ring-1 ring-zinc-900 bg-white' : `border-zinc-200 hover:border-zinc-400 ${m.color}`)
            }
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg font-mono">{m.icon}</span>
              <span className="text-sm font-semibold text-zinc-900">{m.label}</span>
            </div>
            <p className="text-xs text-zinc-500 leading-snug">{m.desc}</p>
          </button>
        ))}
      </div>

      {/* Agent team visual */}
      <div className="p-5 bg-zinc-50 border border-zinc-200 rounded-xl space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-zinc-900">
            <Users className="w-4 h-4 inline mr-1.5 text-zinc-500" />
            Agent Team — {selected.label} Mode
          </h4>
          <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest flex items-center gap-1">
            <GitBranch className="w-3 h-3" /> CoordinationMode.{mode.toUpperCase()}
          </span>
        </div>
        <div className="flex flex-wrap gap-3">
          {agents.map((a, i) => (
            <div key={a.name} className="flex items-start gap-2 p-3 bg-white border border-zinc-200 rounded-lg min-w-[160px]">
              <div className="w-5 h-5 rounded-full bg-zinc-900 text-white text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                {i + 1}
              </div>
              <div>
                <div className="text-xs font-semibold text-zinc-900 font-mono">{a.name}</div>
                <div className="text-[11px] text-zinc-500">{a.role}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2 pt-1 text-xs text-emerald-600">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>All agents share a MessageBus with pub/sub routing and dead-letter queues.</span>
        </div>
      </div>

      {/* Mode features */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Message Bus', value: 'Pub/Sub + Dead Letters', icon: <Zap className="w-4 h-4 text-zinc-400" /> },
          { label: 'State', value: 'AgentState per agent', icon: <GitBranch className="w-4 h-4 text-zinc-400" /> },
          { label: 'Results', value: 'OrchestrationResult', icon: <CheckCircle2 className="w-4 h-4 text-zinc-400" /> },
        ].map(f => (
          <div key={f.label} className="p-3 bg-white border border-zinc-200 rounded-xl flex items-center gap-2">
            {f.icon}
            <div>
              <div className="text-[10px] text-zinc-400 uppercase tracking-wider">{f.label}</div>
              <div className="text-xs font-semibold text-zinc-800 font-mono">{f.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Code sample */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Code — {selected.label}</h4>
          <span className="text-[10px] text-zinc-400 font-mono">ai_core/agents.py</span>
        </div>
        <CodeBlock code={MODE_CODE[mode]} />
      </div>
    </div>
  );
};

export default PlaygroundPage;
