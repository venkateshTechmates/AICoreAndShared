import { ArrowRight, CheckCircle2, ChevronRight } from 'lucide-react';
import { SectionHeader, DataTable } from '../components/ui';

const ArchitecturePage = () => (
  <div className="space-y-16">
    <SectionHeader badge="Architecture" title="System Architecture & Workflows" subtitle="Deep dive into architecture patterns, RAG workflows, agentic patterns, and enterprise integration." />

    {/* High-Level Architecture */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">High-Level Architecture</h3>
      <div className="bg-zinc-900 rounded-2xl p-8 overflow-x-auto">
        <pre className="text-zinc-300 font-mono text-xs leading-relaxed whitespace-pre">{'┌─────────────────────────────────────────────────────────────────────────┐\n│                        ai-core-lib (Python Package)                     │\n│                                                                         │\n│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │\n│  │   RAG    │  │  Agents  │  │ Prompts  │  │   Eval   │  │  Cost  │  │\n│  │  Engine  │  │  Layer   │  │  Engine  │  │  Suite   │  │  Mgmt  │  │\n│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘  │\n│       └──────────────┴──────────────┴──────────────┴────────────┘       │\n│                              │                                          │\n│       ┌──────────────────────▼──────────────────────────────┐          │\n│       │           Shared Core / Utilities                    │          │\n│       │  Config │ Logging │ Tracing │ Auth │ Cache │ Memory  │          │\n│       └──────────────────────┬──────────────────────────────┘          │\n│                              │                                          │\n│    ┌─────────────────────────┼─────────────────────────┐               │\n│    │                         │                         │                │\n│    ▼                         ▼                         ▼                │\n│  Framework Adapters    Vector Store Layer      LLM Provider Layer      │\n│  (LangChain, CrewAI,   (Qdrant, Pinecone,     (OpenAI, Anthropic,    │\n│   AutoGen, MCP, ...)    Weaviate, Chroma...)    Azure, Bedrock...)    │\n└─────────────────────────────────────────────────────────────────────────┘'}</pre>
      </div>
    </section>

    {/* Design Patterns */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Design Patterns</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          { pattern: 'Factory', desc: 'Swap providers via config (VectorStoreFactory, LLMFactory)', benefit: 'Zero vendor lock-in' },
          { pattern: 'Strategy', desc: 'Runtime algorithm selection (search, chunking, prompts)', benefit: 'Experiment without redeploy' },
          { pattern: 'Adapter', desc: 'Unified interface across frameworks (LangChain, CrewAI, ...)', benefit: 'Framework-neutral code' },
          { pattern: 'Builder', desc: 'Fluent API for complex setups (CrewBuilder, GraphBuilder)', benefit: 'Self-documenting config' },
          { pattern: 'Registry', desc: 'Centralized management (Prompts, Tools, Plugins)', benefit: 'Single source of truth' },
          { pattern: 'Observer', desc: 'Pipeline hooks and event system for tracing', benefit: 'Non-invasive monitoring' },
        ].map((item, i) => (
          <div key={i} className="p-6 bg-white border border-zinc-200 rounded-xl">
            <h4 className="font-bold text-zinc-900 mb-2">{item.pattern} Pattern</h4>
            <p className="text-sm text-zinc-500 mb-3">{item.desc}</p>
            <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">{item.benefit}</span>
          </div>
        ))}
      </div>
    </section>

    {/* RAG Pipeline Steps */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Complete RAG Pipeline Workflow</h3>
      <div className="bg-white border border-zinc-200 rounded-2xl p-8">
        <div className="space-y-4">
          {[
            { step: '01', title: 'Input Validation', desc: 'Content filter, PII check, rate limit enforcement', color: 'bg-red-50 text-red-600' },
            { step: '02', title: 'Cache Lookup', desc: 'Semantic cache check (0.97 similarity threshold)', color: 'bg-amber-50 text-amber-600' },
            { step: '03', title: 'Query Transform', desc: 'Multi-Query, HyDE, or Step-Back abstraction', color: 'bg-blue-50 text-blue-600' },
            { step: '04', title: 'Query Embedding', desc: 'text-embedding-3-large = 3072-dim vector', color: 'bg-purple-50 text-purple-600' },
            { step: '05', title: 'Vector Search', desc: 'Hybrid (Dense 0.7 + Sparse 0.3) then RRF fusion', color: 'bg-green-50 text-green-600' },
            { step: '06', title: 'Re-Ranking', desc: 'Cohere Reranker with Top-3 most relevant', color: 'bg-cyan-50 text-cyan-600' },
            { step: '07', title: 'Context Assembly', desc: 'Token budget fitting, deduplication', color: 'bg-indigo-50 text-indigo-600' },
            { step: '08', title: 'Prompt Rendering', desc: 'Template + strategy (CoT, Few-Shot, etc.)', color: 'bg-rose-50 text-rose-600' },
            { step: '09', title: 'LLM Generation', desc: 'GPT-4o / Claude 3.5 with streaming', color: 'bg-emerald-50 text-emerald-600' },
            { step: '10', title: 'Post-Processing', desc: 'Citation mapping, PII check, content filter', color: 'bg-zinc-100 text-zinc-600' },
            { step: '11', title: 'Audit & Trace', desc: 'Log to LangSmith/Langfuse, audit trail', color: 'bg-zinc-100 text-zinc-600' },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-4">
              <span className={'w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold ' + item.color}>{item.step}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-zinc-900 text-sm">{item.title}</span>
                  {i < 10 && <ArrowRight size={14} className="text-zinc-300" />}
                </div>
                <p className="text-xs text-zinc-500">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>

    {/* SOLID Principles */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">SOLID Principles Applied</h3>
      <DataTable headers={['Principle', 'Application']} rows={[
        ['Single Responsibility', 'Each module has one clear purpose (RAG, Agents, Prompts, Eval)'],
        ['Open/Closed', 'Plugin system allows extension without modifying core'],
        ['Liskov Substitution', 'All vector stores, LLMs, embeddings are interchangeable via interface'],
        ['Interface Segregation', 'Small, focused interfaces (VectorStore, LLM, Embedder)'],
        ['Dependency Inversion', 'Modules depend on abstractions (Factory pattern), not concrete providers'],
      ]} />
    </section>

    {/* Phased Delivery */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Phased Delivery Roadmap</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[
          { phase: 'Phase 1', title: 'Foundation', weeks: 'Weeks 1-6', items: ['Core utilities (config, logging, tracing)', 'LLM abstraction (OpenAI, Anthropic, Azure)', 'Vector store (Pinecone, Qdrant, Chroma)', 'Basic RAG pipeline + prompt templates', 'CI/CD + unit tests'] },
          { phase: 'Phase 2', title: 'Enrichment', weeks: 'Weeks 7-12', items: ['Semantic chunking + all search strategies', 'Full prompt module (CoT, ReAct, ToT)', 'LangChain + LangGraph adapters', 'Agent framework + tool registry', 'Semantic cache + eval suite'] },
          { phase: 'Phase 3', title: 'Multi-Framework', weeks: 'Weeks 13-18', items: ['CrewAI + AutoGen + MCP adapters', 'Vertex AI + Bedrock adapters', 'All remaining vector stores', 'Multi-tenant RBAC + audit logging', 'Full observability integration'] },
          { phase: 'Phase 4', title: 'Enterprise Hardening', weeks: 'Weeks 19-24', items: ['Data governance + PII detection', 'Cost governance + alerting', 'Model lifecycle + A/B testing', 'Multi-region + DR', 'Compliance (SOC2, GDPR)'] },
        ].map((p, i) => (
          <div key={i} className="p-6 bg-white border border-zinc-200 rounded-xl">
            <div className="flex items-center gap-3 mb-4">
              <span className="px-3 py-1 bg-zinc-900 text-white rounded-full text-xs font-bold">{p.phase}</span>
              <span className="text-xs text-zinc-400 font-mono">{p.weeks}</span>
            </div>
            <h4 className="font-bold text-zinc-900 mb-3">{p.title}</h4>
            <ul className="space-y-2">
              {p.items.map((item, j) => <li key={j} className="flex items-start gap-2 text-sm text-zinc-500"><CheckCircle2 size={14} className="text-green-500 mt-0.5 shrink-0" />{item}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </section>

    {/* Data Flow */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Data Flow Architecture</h3>
      <div className="bg-zinc-900 rounded-2xl p-8 overflow-x-auto">
        <pre className="text-zinc-300 font-mono text-xs leading-relaxed whitespace-pre">{'  User Query                                                        Response\n      │                                                                ▲\n      ▼                                                                │\n┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐\n│  Input    │───▶│  Cache   │───▶│  Search  │───▶│  Rerank  │───▶│ Generate │\n│ Validate  │    │  Layer   │    │  Engine  │    │  Module  │    │   LLM    │\n└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘\n      │              │                │               │               │\n      ▼              ▼                ▼               ▼               ▼\n┌──────────────────────────────────────────────────────────────────────────┐\n│                    Observability & Audit Trail                          │\n│        OpenTelemetry  │  LangSmith  │  Prometheus  │  Cost Tracker     │\n└──────────────────────────────────────────────────────────────────────────┘'}</pre>
      </div>
    </section>
  </div>
);

export default ArchitecturePage;
