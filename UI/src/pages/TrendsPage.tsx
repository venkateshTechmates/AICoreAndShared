import { CheckCircle2, ChevronRight } from 'lucide-react';
import { SectionHeader, DataTable } from '../components/ui';

const TrendsPage = () => (
  <div className="space-y-16">
    <SectionHeader badge="Industry Trends" title="Enterprise AI Trends, Patterns & Pros" subtitle="2025-2026 landscape: RAG evolution, agentic AI, cost optimization, and security best practices." />

    {/* RAG Evolution */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">RAG Evolution: From Naive to Agentic</h3>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {[
          { gen: '1.0', name: 'Naive RAG', desc: 'Simple retrieve then generate', status: 'Baseline' },
          { gen: '2.0', name: 'Advanced RAG', desc: 'Hybrid search + reranking', status: 'Production' },
          { gen: '3.0', name: 'Modular RAG', desc: 'Pluggable components, A/B testing', status: 'Emerging' },
          { gen: '4.0', name: 'Agentic RAG', desc: 'LLM decides strategy at runtime', status: 'Cutting Edge' },
          { gen: '5.0', name: 'Self-Improving', desc: 'Pipeline self-optimizes via eval', status: 'Research' },
        ].map((item, i) => (
          <div key={i} className={'p-5 rounded-xl border ' + (i <= 1 ? 'bg-green-50 border-green-200' : i <= 2 ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200')}>
            <span className="text-xs font-mono font-bold">{item.gen}</span>
            <h4 className="font-bold text-zinc-900 mt-1">{item.name}</h4>
            <p className="text-xs text-zinc-600 mt-1">{item.desc}</p>
            <span className={'mt-2 inline-block text-[10px] font-medium px-2 py-0.5 rounded-full ' + (item.status === 'Production' ? 'bg-green-100 text-green-700' : item.status === 'Baseline' ? 'bg-zinc-100 text-zinc-600' : item.status === 'Emerging' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700')}>{item.status}</span>
          </div>
        ))}
      </div>
    </section>

    {/* AI Maturity Model */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Enterprise AI Maturity Model</h3>
      <div className="space-y-3">
        {[
          { level: 5, name: 'Self-Optimizing', desc: 'Automated pipeline optimization, cost governance', color: 'bg-purple-500' },
          { level: 4, name: 'Governed', desc: 'RBAC, audit trails, compliance, data governance', color: 'bg-blue-500' },
          { level: 3, name: 'Multi-Agent & Orchestrated', desc: 'Multi-agent systems, workflow automation', color: 'bg-green-500' },
          { level: 2, name: 'RAG + Agents', desc: 'Production RAG pipelines, basic agent workflows', color: 'bg-amber-500' },
          { level: 1, name: 'Experimentation', desc: 'Prompt engineering, basic LLM integration', color: 'bg-zinc-400' },
        ].map((item) => (
          <div key={item.level} className="flex items-center gap-4">
            <div className={item.color + ' w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg shrink-0'}>{item.level}</div>
            <div className="flex-1 p-4 bg-white border border-zinc-200 rounded-xl">
              <h4 className="font-semibold text-zinc-900">{item.name}</h4>
              <p className="text-sm text-zinc-500">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>

    {/* Token Cost */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Token Cost Reduction Strategies</h3>
      <DataTable headers={['Strategy', 'Savings', 'Complexity', 'Impact']} rows={[
        ['Semantic Caching', '25-40%', 'Low', 'Deduplicates similar queries'],
        ['Smart Model Routing', '30-50%', 'Medium', 'Routes simple queries to cheaper models'],
        ['Context Compression', '20-35%', 'Low', 'Reduces token input to LLM'],
        ['Batch Processing', '15-25%', 'Low', 'Aggregates requests for efficiency'],
        ['Prompt Optimization', '10-20%', 'Medium', 'Shorter, more effective prompts'],
        ['Query Deduplication', '5-15%', 'Low', 'Collapses identical concurrent queries'],
      ]} />
    </section>

    {/* Model Cost */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Model Cost Comparison (per 1M tokens)</h3>
      <DataTable headers={['Model', 'Input Cost', 'Output Cost', 'Speed', 'Quality']} rows={[
        ['GPT-4o', '$2.50', '$10.00', 'Fast', 'Excellent'],
        ['GPT-4o-mini', '$ .15', '$ .60', 'Very Fast', 'Good'],
        ['Claude 3.5 Sonnet', '$3.00', '$15.00', 'Fast', 'Excellent'],
        ['Claude 3 Haiku', '$ .25', '$1.25', 'Very Fast', 'Good'],
        ['Gemini 2.0 Flash', '$ .10', '$ .40', 'Fastest', 'Good'],
        ['Llama 3.1 70B', '$ .59', '$ .79', 'Very Fast', 'Good'],
        ['Llama 3.1 8B (Local)', '$ .00', '$ .00', 'Moderate', 'Fair'],
      ]} />
    </section>

    {/* Framework Guide */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Framework Selection Guide</h3>
      <DataTable headers={['Framework', 'Strength', 'Weakness', 'Best For']} rows={[
        ['LangChain', 'Ecosystem, chains', 'Complexity', 'RAG, chains'],
        ['LangGraph', 'Stateful graphs, cycles', 'Learning curve', 'Complex workflows'],
        ['CrewAI', 'Role-based teams', 'Limited customization', 'Team-based tasks'],
        ['AutoGen', 'Conversational agents', 'Verbose', 'Chat agents'],
        ['MCP', 'Standard protocol', 'New, limited adoption', 'Tool serving'],
        ['DSPy', 'Prompt optimization', 'Niche', 'Prompt tuning'],
        ['Haystack', 'Pipeline-centric', 'Smaller ecosystem', 'Document processing'],
      ]} />
    </section>

    {/* Technology Radar */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Technology Radar 2026</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { ring: 'ADOPT', color: 'bg-green-500', items: ['Hybrid RAG (dense + sparse)', 'Semantic chunking', 'Cohere reranking', 'Qdrant / Pinecone VDB', 'OpenTelemetry tracing'] },
          { ring: 'TRIAL', color: 'bg-blue-500', items: ['MCP protocol', 'Agentic RAG', 'DSPy prompt optimization', 'Multi-modal embeddings', 'LangGraph stateful agents'] },
          { ring: 'ASSESS', color: 'bg-amber-500', items: ['Self-improving RAG', 'Autonomous agent teams', 'Edge AI inference', 'Federated vector stores'] },
          { ring: 'HOLD', color: 'bg-red-500', items: ['Single-provider lock-in', 'Unmonitored LLM calls', 'Fixed chunking for production', 'No evaluation in pipeline'] },
        ].map((ring, i) => (
          <div key={i} className="p-6 bg-white border border-zinc-200 rounded-xl">
            <div className="flex items-center gap-2 mb-4">
              <div className={'w-3 h-3 rounded-full ' + ring.color} />
              <span className="font-bold text-zinc-900 text-sm">{ring.ring}</span>
            </div>
            <ul className="space-y-2">
              {ring.items.map((item, j) => <li key={j} className="text-sm text-zinc-600 flex items-start gap-2"><ChevronRight size={14} className="text-zinc-400 mt-0.5 shrink-0" />{item}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </section>

    {/* Security Layers */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Enterprise AI Security Layers</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[
          { layer: 'Input Security', items: ['Prompt injection detection', 'Input sanitization', 'PII detection (Presidio)', 'Content filtering'], color: 'border-red-200 bg-red-50' },
          { layer: 'Processing Security', items: ['Token budget enforcement', 'Rate limiting (per-user/team)', 'Model access control (RBAC)', 'Namespace isolation'], color: 'border-amber-200 bg-amber-50' },
          { layer: 'Output Security', items: ['Output content filtering', 'PII re-check on output', 'Hallucination detection', 'Citation verification'], color: 'border-blue-200 bg-blue-50' },
          { layer: 'Governance', items: ['Comprehensive audit trail', 'Cost governance & alerts', 'Data lineage tracking', 'Compliance (SOC2, GDPR)'], color: 'border-green-200 bg-green-50' },
        ].map((item, i) => (
          <div key={i} className={'p-6 border rounded-xl ' + item.color}>
            <h4 className="font-bold text-zinc-900 mb-3">Layer {i + 1}: {item.layer}</h4>
            <ul className="space-y-2">
              {item.items.map((it, j) => <li key={j} className="text-sm text-zinc-600 flex items-center gap-2"><CheckCircle2 size={14} className="text-green-500 shrink-0" />{it}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </section>

    {/* Compliance */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Compliance Roadmap</h3>
      <DataTable headers={['Certification', 'Status', 'Target', 'Key Evidence']} rows={[
        ['SOC 2 Type II', 'In Progress', 'Q3 2026', 'Audit logs, security controls'],
        ['ISO 27001', 'Planned', 'Q4 2026', 'Info security management'],
        ['GDPR', 'Implemented', 'Done', 'Data residency, right-to-erasure'],
        ['CCPA', 'Implemented', 'Done', 'Data deletion, opt-out'],
        ['HIPAA', 'Planned', 'Q1 2027', 'PHI handling, BAA'],
        ['FedRAMP', 'Planned', 'Q2 2027', 'Government cloud'],
      ]} />
    </section>
  </div>
);

export default TrendsPage;
