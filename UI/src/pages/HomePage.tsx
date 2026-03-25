import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import {
  Database, Users, Brain, Puzzle, FlaskConical, ShieldCheck,
  DollarSign, Eye, Blocks, ArrowRight, BookOpen, Sparkles,
  Layers, Workflow, GitBranch,
} from 'lucide-react';
import { FeatureCard, StatCard, SectionHeader, CodeBlock } from '../components/ui';

const HomePage = () => (
  <div className="space-y-24">
    {/* Hero */}
    <section className="text-center py-16">
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600 mb-8">
          <Sparkles size={14} /> Enterprise AI Core Library v1.0.0
        </div>
        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-zinc-900 tracking-tight mb-6 leading-[1.1]">
          Unified AI Engineering<br /><span className="text-zinc-400">Platform for Enterprise</span>
        </h1>
        <p className="text-xl text-zinc-500 max-w-2xl mx-auto mb-10 leading-relaxed">
          Production-grade Python library unifying RAG pipelines, agentic workflows, 9+ framework adapters, and enterprise governance through a single, pluggable interface.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link to="/core" className="px-6 py-3 bg-zinc-900 text-white rounded-xl text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2">Explore Core Library <ArrowRight size={16} /></Link>
          <Link to="/pipelines" className="px-6 py-3 border border-zinc-300 text-zinc-700 rounded-xl text-sm font-medium hover:bg-zinc-50 transition-colors flex items-center gap-2">View Pipelines <Workflow size={16} /></Link>
          <Link to="/architecture" className="px-6 py-3 border border-zinc-300 text-zinc-700 rounded-xl text-sm font-medium hover:bg-zinc-50 transition-colors flex items-center gap-2">Architecture <BookOpen size={16} /></Link>
        </div>
      </motion.div>
    </section>

    {/* Stats */}
    <section className="grid grid-cols-2 md:grid-cols-4 gap-6">
      <StatCard value="8+" label="Core Modules" icon={<Blocks size={24} />} />
      <StatCard value="6" label="Coordination Modes" icon={<Puzzle size={24} />} />
      <StatCard value="9" label="Vector DB Providers" icon={<Database size={24} />} />
      <StatCard value="247" label="Tests Passing" icon={<Brain size={24} />} />
    </section>

    {/* Capabilities */}
    <section>
      <SectionHeader badge="Capabilities" title="Everything You Need for Enterprise AI" subtitle="From RAG pipelines to multi-agent orchestration, built for production at scale." />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <FeatureCard icon={<Database size={22} />} title="RAG Engine" description="End-to-end retrieval-augmented generation with hybrid search, reranking, citation tracking, and streaming." tags={['Hybrid Search', 'Reranking', 'Streaming']} />
        <FeatureCard icon={<Layers size={22} />} title="Vector DB Abstraction" description="Unified interface for 9+ vector databases. Swap providers with a config change." tags={['Pinecone', 'Qdrant', 'Weaviate', 'Chroma']} />
        <FeatureCard icon={<Brain size={22} />} title="Prompt Engineering" description="15+ prompt strategies from zero-shot to tree-of-thought with versioned template registry." tags={['CoT', 'ReAct', 'Few-Shot', 'ToT']} />
        <FeatureCard icon={<Users size={22} />} title="Multi-Agent Orchestration" description="Six coordination modes: Sequential, Parallel, Debate, Hierarchical, Swarm, Supervisor — with MessageBus and AgentPipelineBuilder." tags={['Sequential', 'Parallel', 'Debate', 'Supervisor']} />
        <FeatureCard icon={<Puzzle size={22} />} title="Multi-Framework" description="Unified adapter layer for LangChain, LangGraph, CrewAI, AutoGen, MCP, and more." tags={['LangChain', 'CrewAI', 'AutoGen', 'MCP']} />
        <FeatureCard icon={<FlaskConical size={22} />} title="Evaluation Suite" description="RAGAS-integrated evaluation with faithfulness, relevancy, recall, and precision metrics." tags={['RAGAS', 'DeepEval', 'TruLens']} />
        <FeatureCard icon={<ShieldCheck size={22} />} title="Data Governance" description="PII detection, data classification, RBAC/ABAC access control, audit trails, and data retention." tags={['PII', 'RBAC', 'Audit', 'GDPR']} />
        <FeatureCard icon={<DollarSign size={22} />} title="Cost Management" description="Per-call cost tracking, budget alerts, smart model routing, semantic caching, quota enforcement." tags={['Budgets', 'Quotas', 'Routing']} />
        <FeatureCard icon={<Eye size={22} />} title="Observability" description="Integrated with LangSmith, Langfuse, OpenTelemetry, Prometheus, and Datadog." tags={['Traces', 'Metrics', 'Alerts']} />
      </div>
    </section>

    {/* Quick Start */}
    <section>
      <SectionHeader badge="Quick Start" title="From Zero to RAG in Minutes" subtitle="Install the library and run your first RAG pipeline with just a few lines of Python." />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <h3 className="text-sm font-mono text-zinc-400 uppercase tracking-widest font-medium">1. Install</h3>
          <CodeBlock code={'pip install ai-core-lib[all]'} language="bash" />
          <h3 className="text-sm font-mono text-zinc-400 uppercase tracking-widest font-medium mt-6">2. Configure</h3>
          <CodeBlock code={'# ai-core.yml\nllm:\n  provider: openai\n  model: gpt-4o\nvector_store:\n  provider: qdrant\n  url: http://localhost:6333\nrag:\n  chunking: semantic\n  search: hybrid\n  reranker: cohere'} language="yaml" />
        </div>
        <div className="space-y-4">
          <h3 className="text-sm font-mono text-zinc-400 uppercase tracking-widest font-medium">3. Build Pipeline</h3>
          <CodeBlock code={'from ai_core.rag import RAGPipeline, RAGConfig\n\nconfig = RAGConfig(\n    vector_db=\"qdrant\",\n    embedding_model=\"text-embedding-3-large\",\n    llm_model=\"gpt-4o\",\n    search_strategy=\"hybrid\",\n    reranker=\"cohere\",\n)\n\nrag = RAGPipeline(config)\n\n# Ingest documents\nawait rag.ingest(docs, namespace=\"knowledge-base\")\n\n# Query with citations\nresponse = await rag.query(\n    query=\"What were the Q4 drivers?\",\n    prompt_strategy=\"chain_of_thought\",\n)\n\nprint(response.answer)\nprint(response.citations)'} />
        </div>
      </div>
    </section>

    {/* Integrations */}
    <section>
      <SectionHeader badge="Integrations" title="Works With Your Stack" subtitle="First-class adapters for all major AI frameworks. No vendor lock-in." />
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          { name: 'LangChain', status: 'Full' }, { name: 'LangGraph', status: 'Full' }, { name: 'CrewAI', status: 'Full' },
          { name: 'AutoGen', status: 'Full' }, { name: 'MCP', status: 'Full' }, { name: 'Vertex AI', status: 'Full' },
          { name: 'Bedrock', status: 'Full' }, { name: 'Haystack', status: 'Adapter' }, { name: 'DSPy', status: 'Adapter' },
          { name: 'Semantic Kernel', status: 'Adapter' },
        ].map((fw, i) => (
          <div key={i} className="p-4 bg-white border border-zinc-200 rounded-xl text-center hover:border-zinc-400 transition-all">
            <div className="font-semibold text-zinc-900 text-sm mb-1">{fw.name}</div>
            <span className={'text-[10px] font-medium px-2 py-0.5 rounded-full ' + (fw.status === 'Full' ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600')}>{fw.status}</span>
          </div>
        ))}
      </div>
    </section>

    {/* Visual Architecture Preview */}
    <section>
      <SectionHeader badge="Architecture" title="Layered Enterprise Architecture" subtitle="Modular design with clean separation — swap any provider without touching business logic." />
      <div className="bg-zinc-900 rounded-2xl p-8 overflow-x-auto">
        <pre className="text-zinc-300 font-mono text-[11px] leading-relaxed whitespace-pre">{'┌──────────────────────────────────────────────────────────────────────────┐\n│                      ai-core-lib (Python Package)                        │\n│                                                                          │\n│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │\n│  │   RAG    │  │  Agents  │  │ Prompts  │  │   Eval   │  │  Cost   │  │\n│  │  Engine  │  │  Layer   │  │  Engine  │  │  Suite   │  │  Mgmt   │  │\n│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │\n│       └──────────────┴──────────────┴──────────────┴─────────────┘       │\n│                              │                                           │\n│  ┌───────────────────────────▼─────────────────────────────────────────┐ │\n│  │              Shared Core / Utilities                                │ │\n│  │  Config │ Logging │ Tracing │ Auth │ Cache │ Memory │ Resilience   │ │\n│  └───────────────────────────┬─────────────────────────────────────────┘ │\n│                              │                                           │\n│    ┌─────────────────────────┼─────────────────────────┐                │\n│    ▼                         ▼                         ▼                │\n│  Framework Adapters    Vector Store Layer      LLM Provider Layer       │\n│  (LangChain, CrewAI,   (Qdrant, Pinecone,     (OpenAI, Anthropic,     │\n│   AutoGen, MCP, ...)    Weaviate, Chroma...)    Azure, Bedrock...)     │\n└──────────────────────────────────────────────────────────────────────────┘'}</pre>
      </div>
    </section>

    {/* CTA */}
    <section className="text-center py-12 px-8 bg-zinc-900 rounded-3xl">
      <h2 className="text-3xl font-bold text-white mb-4">Ready to Build Enterprise AI?</h2>
      <p className="text-zinc-400 mb-8 max-w-lg mx-auto">Explore the full documentation, interactive pipeline visualizations, and workflow patterns.</p>
      <div className="flex items-center justify-center gap-4 flex-wrap">
        <Link to="/core" className="px-6 py-3 bg-white text-zinc-900 rounded-xl text-sm font-medium hover:bg-zinc-100 transition-colors">Core Library Docs</Link>
        <Link to="/pipelines" className="px-6 py-3 border border-zinc-700 text-white rounded-xl text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2"><Workflow size={16} /> Pipelines & Flows</Link>
        <Link to="/workflows" className="px-6 py-3 border border-zinc-700 text-white rounded-xl text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2"><GitBranch size={16} /> Workflows</Link>
      </div>
    </section>
  </div>
);

export default HomePage;
