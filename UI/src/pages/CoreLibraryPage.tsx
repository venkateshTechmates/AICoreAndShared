import { Database, Server, Search, Layers, Terminal, Users, Puzzle, FlaskConical } from 'lucide-react';
import { SectionHeader, CodeBlock, DataTable } from '../components/ui';

const CoreLibraryPage = () => (
  <div className="space-y-16">
    <SectionHeader badge="Core Modules" title="AI Core Library Module Reference" subtitle="Complete API reference for all 8 core modules of the ai-core-lib Python package." />

    {/* 1. RAG Engine */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg"><Database size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">1. RAG Engine</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.rag</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">End-to-end retrieval-augmented generation with ingestion pipelines, hybrid search, reranking, streaming, citation tracking, and multi-index RAG.</p>
      <CodeBlock code={'from ai_core.rag import RAGPipeline, RAGConfig\n\nconfig = RAGConfig(\n    vector_db=\"qdrant\",\n    embedding_model=\"text-embedding-3-large\",\n    llm_model=\"gpt-4o\",\n    chunking_strategy=\"semantic\",\n    search_strategy=\"hybrid\",\n    reranker=\"cohere\",\n    top_k=10,\n    top_k_after_rerank=3,\n    citation_tracking=True,\n    streaming=True,\n)\n\nrag = RAGPipeline(config)\nawait rag.ingest(documents=docs, namespace=\"finance-q4\")\n\nresponse = await rag.query(\n    query=\"What were the Q4 revenue drivers?\",\n    namespace=\"finance-q4\",\n    prompt_strategy=\"chain_of_thought\",\n    include_sources=True,\n)\n\nasync for chunk in rag.stream(query=\"Summarize the risk factors\"):\n    print(chunk.text, end=\"\", flush=True)'} />
      <DataTable headers={['Parameter', 'Type', 'Options']} rows={[
        ['vector_db', 'str', 'pinecone, weaviate, qdrant, chroma, milvus, pgvector, redis'],
        ['embedding_model', 'str', 'Any supported provider model'],
        ['search_strategy', 'str', 'dense, sparse, hybrid, mmr, multi_query, hyde, self_query'],
        ['chunking_strategy', 'str', 'fixed, recursive, semantic, sentence, agentic, document_aware'],
        ['reranker', 'str', 'cohere, bge, cross_encoder, llm_reranker, none'],
        ['prompt_strategy', 'str', 'zero_shot, few_shot, chain_of_thought, react, rag + 10 more'],
      ]} />
    </section>

    {/* 2. Vector DB */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-purple-50 text-purple-600 rounded-lg"><Server size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">2. Vector Database Abstraction</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.vectorstore</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">Unified interface for 9 vector database providers. Swap backends with configuration only.</p>
      <CodeBlock code={'from ai_core.vectorstore import VectorStoreFactory, VectorDocument\n\nstore = VectorStoreFactory.create(\n    provider=\"qdrant\",\n    collection=\"knowledge_base\",\n    config={\"url\": \"http://localhost:6333\"},\n)\n\nawait store.upsert(documents=[\n    VectorDocument(\n        id=\"doc_001\",\n        text=\"Revenue increased 15% YoY...\",\n        metadata={\"department\": \"finance\", \"year\": 2025},\n        namespace=\"finance\",\n    )\n])\n\nresults = await store.search(\n    query=SearchQuery(text=\"Q4 revenue\", top_k=10, strategy=\"hybrid\")\n)'} />
      <DataTable headers={['Provider', 'Type', 'Key Feature', 'Best For']} rows={[
        ['Pinecone', 'Managed Cloud', 'Serverless + pods', 'Production SaaS'],
        ['Qdrant', 'Open Source/Cloud', 'Rust core, gRPC', 'Performance-critical'],
        ['Weaviate', 'Open Source/Cloud', 'GraphQL, modules', 'Complex queries'],
        ['Chroma', 'Open Source', 'Simple API', 'Local dev / prototyping'],
        ['Milvus / Zilliz', 'Open Source/Cloud', 'GPU acceleration', 'Large-scale'],
        ['PgVector', 'Postgres Extension', 'SQL-integrated', 'Existing Postgres'],
        ['Redis VSS', 'In-Memory', 'Sub-millisecond', 'Real-time / caching'],
        ['OpenSearch', 'AWS Managed', 'kNN plugin', 'AWS-centric'],
        ['Azure AI Search', 'Managed Cloud', 'Cognitive skills', 'Azure ecosystem'],
      ]} />
    </section>

    {/* 3. Search Strategies */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-green-50 text-green-600 rounded-lg"><Search size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">3. Vector Search Strategies</h3>
      </div>
      <DataTable headers={['Strategy', 'Latency', 'Relevance', 'Best For']} rows={[
        ['Dense (ANN)', 'Low', 'High', 'Semantic similarity'],
        ['Sparse (BM25)', 'Low', 'Medium', 'Keyword / exact match'],
        ['Hybrid (RRF)', 'Medium', 'Very High', 'General production use'],
        ['MMR', 'Medium', 'High', 'Diverse context coverage'],
        ['Multi-Query', 'High', 'Very High', 'Complex / ambiguous queries'],
        ['HyDE', 'High', 'High', 'Low-recall embedding spaces'],
        ['Self-Query', 'Medium', 'High', 'Filtered search'],
        ['Parent-Child', 'Medium', 'High', 'Hierarchical documents'],
        ['Step-Back', 'High', 'Very High', 'Reasoning-heavy queries'],
        ['Contextual Compression', 'Medium', 'High', 'Token budget management'],
      ]} />
    </section>

    {/* 4. Chunking Engine */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-amber-50 text-amber-600 rounded-lg"><Layers size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">4. Chunking Engine</h3>
      </div>
      <CodeBlock code={'from ai_core.chunking import ChunkingEngine, ChunkingConfig\n\nengine = ChunkingEngine(\n    strategy=\"semantic\",\n    config=ChunkingConfig(\n        embedding_model=\"text-embedding-3-small\",\n        breakpoint_threshold=0.75,\n        min_chunk_size=100,\n        max_chunk_size=1000,\n    )\n)\nchunks = engine.chunk(documents)'} />
      <DataTable headers={['Strategy', 'Speed', 'Quality', 'Use Case']} rows={[
        ['Fixed-Size', 'Fastest', 'Low', 'Quick prototyping'],
        ['Recursive Character', 'Fast', 'Medium', 'General text'],
        ['Sentence', 'Fast', 'Medium', 'NLP pipelines'],
        ['Semantic', 'Slow', 'Very High', 'Production RAG'],
        ['Document-Aware', 'Medium', 'High', 'Structured docs'],
        ['Agentic (LLM)', 'Slowest', 'Highest', 'Critical content'],
        ['Code-Aware', 'Fast', 'High', 'Source code'],
        ['Markdown/HTML', 'Fast', 'High', 'Web content'],
      ]} />
    </section>

    {/* 5. Prompt Engineering */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-rose-50 text-rose-600 rounded-lg"><Terminal size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">5. Prompt Engineering</h3>
      </div>
      <DataTable headers={['Strategy', 'Description', 'Best For']} rows={[
        ['Zero-Shot', 'Instruction only', 'Simple tasks'],
        ['Few-Shot', 'Multiple curated examples', 'Complex domain tasks'],
        ['Chain-of-Thought', '"Think step by step" reasoning', 'Math / logic'],
        ['Self-Consistency', 'N paths + majority vote', 'Reliability-critical'],
        ['Tree-of-Thought', 'Multi-branch exploration', 'Planning / creative'],
        ['ReAct', 'Reason + Act with tools', 'Agent tasks'],
        ['Reflexion', 'Self-critique loop', 'Quality improvement'],
        ['Program-of-Thought', 'Code gen + execute', 'Quantitative tasks'],
        ['Role Prompting', 'Expert persona', 'Domain expertise'],
        ['RAG Prompting', 'Context injection', 'Knowledge-grounded'],
        ['Skeleton-of-Thought', 'Parallel sub-answers', 'Latency reduction'],
        ['Meta Prompting', 'LLM designs own prompt', 'Prompt discovery'],
      ]} />
    </section>

    {/* 6. Agents */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg"><Users size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">6. Agentic AI Framework</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.agents</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">Enterprise multi-agent orchestration with six coordination modes, pub/sub MessageBus, fluent AgentPipelineBuilder, and structured OrchestrationResult.</p>
      <CodeBlock code={'from ai_core.agents import MultiAgentSystem, AgentPipelineBuilder\nfrom ai_core.schemas import CoordinationMode\n\n# Six coordination modes\nsystem = MultiAgentSystem(\n    agents=[research_agent, analysis_agent, writer_agent],\n    mode=CoordinationMode.SEQUENTIAL,     # or PARALLEL, DEBATE, HIERARCHICAL, SWARM, SUPERVISOR\n)\nresult = await system.run("Summarise the Q4 earnings report.")\n\n# Debate mode — structured critique over 3 rounds\ndebate = MultiAgentSystem(\n    agents=[bull_agent, bear_agent, moderator_agent],\n    mode=CoordinationMode.DEBATE,\n    rounds=3,\n)\nresult = await debate.run("What is the fair value of this asset?")\nprint(result.consensus)     # final agreed answer\n\n# Fluent pipeline builder\npipeline = (\n    AgentPipelineBuilder()\n    .add_stage("intake",  intake_agent)\n    .add_stage("analyse", analysis_agent)\n    .add_stage("report",  writer_agent)\n    .with_mode(CoordinationMode.SEQUENTIAL)\n    .build()\n)\nresult = await pipeline.run("Generate compliance report")'} />
      <DataTable headers={['Coordination Mode', 'Pattern', 'Best For']} rows={[
        ['SEQUENTIAL', 'A → B → C', 'Report generation, data pipelines'],
        ['PARALLEL', 'A + B + C → merge', 'Intelligence gathering, risk scoring'],
        ['DEBATE', 'A ↔ B (N rounds)', 'Valuation, adversarial review'],
        ['HIERARCHICAL', 'Supervisor → workers', 'Medical triage, compliance workflows'],
        ['SWARM', 'Shared workspace', 'Knowledge graph construction'],
        ['SUPERVISOR', 'Coordinator → dynamic dispatch', 'Loan underwriting, approvals'],
      ]} />
    </section>

    {/* 7. Multi-Framework */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-cyan-50 text-cyan-600 rounded-lg"><Puzzle size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">7. Multi-Framework Orchestration</h3>
      </div>
      <CodeBlock code={'from ai_core.frameworks import FrameworkAdapter\n\nadapter = FrameworkAdapter.for_framework(\"crewai\")\nresult = await adapter.run(spec, inputs={\"topic\": \"market analysis\"})\n\n# MCP Server\nfrom ai_core.frameworks.mcp import MCPServer\n\nserver = MCPServer(name=\"enterprise-rag-server\")\n\n@server.tool()\nasync def search_kb(query: str, namespace: str) -> list[str]:\n    return await rag.query(query, namespace=namespace)\n\nserver.run(transport=\"stdio\")'} />
    </section>

    {/* 8. Evaluation */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg"><FlaskConical size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">8. Evaluation Suite</h3>
      </div>
      <CodeBlock code={'from ai_core.eval import RAGEvaluator\n\nevaluator = RAGEvaluator(\n    metrics=[\"faithfulness\", \"answer_relevancy\",\n             \"context_recall\", \"context_precision\",\n             \"hallucination\"],\n    llm_judge=\"gpt-4o\",\n)\n\nreport = await evaluator.evaluate(\n    questions=test_set,\n    pipeline=rag,\n    ground_truth=golden_answers,\n)\n\nreport.save(\"eval_results.json\")\nreport.export_html(\"eval_report.html\")'} />
    </section>
  </div>
);

export default CoreLibraryPage;
