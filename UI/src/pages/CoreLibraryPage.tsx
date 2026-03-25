import { Database, Server, Search, Layers, Terminal, Users, Puzzle, FlaskConical, Globe, ShieldCheck, Zap } from 'lucide-react';
import { SectionHeader, CodeBlock, DataTable } from '../components/ui';

const CoreLibraryPage = () => (
  <div className="space-y-16">
    <SectionHeader badge="Core Modules" title="AI Core Library â€” Full Module Reference" subtitle="Complete API reference for all 11 core modules of the ai_core package." />

    {/* Module overview */}
    <DataTable
      headers={['Module', 'Package', 'Key Classes']}
      rows={[
        ['RAG Engine',              'ai_core.rag',         'RAGPipeline, RAGConfig'],
        ['Vector DB Abstraction',   'ai_core.vectorstore', 'VectorStoreFactory, VectorDocument'],
        ['Search Strategies',       'ai_core.search',      '10 strategies via SearchQuery'],
        ['Chunking Engine',         'ai_core.chunking',    'ChunkingEngine, ChunkingConfig'],
        ['Prompt Engineering',      'ai_core.prompts',     'PromptEngine, PromptRegistry, DynamicExampleSelector'],
        ['Agentic AI Framework',    'ai_core.agents',      'BaseAgent, MultiAgentSystem, AgentPipelineBuilder, AgentExecutor'],
        ['Multi-Framework',         'ai_core.frameworks',  'FrameworkAdapter, LangChainAdapter, MCPAdapter'],
        ['Evaluation Suite',        'ai_core.eval',        'RAGEvaluator, RAGASEvaluator, DeepEvalEvaluator, PipelineEvaluator'],
        ['Deployment & Geo-Route',  'ai_core.deployment',  'GeoRouter, EdgeDeployment, HybridCloudManager, DeploymentOrchestrator'],
        ['Recovery & DR',           'ai_core.recovery',    'BackupManager, FailoverChain, DRTest, ChaosEngineering'],
        ['Configuration',           'ai_core.config',      'LibConfig'],
      ]}
    />

    {/* 1. RAG Engine */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg"><Database size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">1. RAG Engine</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.rag</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">End-to-end retrieval-augmented generation with ingestion, hybrid search, reranking, streaming, citation tracking, cost limits, and pre/post hooks.</p>
      <CodeBlock code={`from ai_core.rag import RAGPipeline, RAGConfig
from ai_core.schemas import ChunkingStrategy, SearchStrategy

config = RAGConfig(
    llm_provider="openai",
    llm_model="gpt-4o",
    embedding_provider="openai",
    embedding_model="text-embedding-3-large",
    vector_store_provider="qdrant",
    collection="knowledge_base",
    chunking_strategy=ChunkingStrategy.SEMANTIC,
    search_strategy=SearchStrategy.HYBRID,
    reranker="cohere",
    top_k=10,
    top_k_after_rerank=3,
    citation_tracking=True,
    streaming=True,
    cost_limit_usd=0.10,          # hard stop if cost exceeds limit
)

rag = RAGPipeline(config)

# â”€â”€ Ingestion â”€â”€
await rag.ingest(documents=docs, namespace="finance-q4")

# â”€â”€ Query with sources â”€â”€
response = await rag.query(
    query="What were the Q4 revenue drivers?",
    namespace="finance-q4",
    prompt_strategy="chain_of_thought",
    include_sources=True,
)
print(response.answer, response.sources, response.cost_usd, response.latency_ms)

# â”€â”€ Streaming â”€â”€
async for chunk in rag.stream("Summarize the risk factors", namespace="finance-q4"):
    print(chunk.text, end="", flush=True)

# â”€â”€ Hooks (pre/post ingest, pre/post query) â”€â”€
rag.add_pre_query_hook(lambda q, ns: audit_log(q, ns))
rag.add_post_query_hook(lambda q, r: track_cost(r.cost_usd))`} />
      <DataTable headers={['Parameter', 'Type', 'Options']} rows={[
        ['vector_store_provider', 'str', 'pinecone, qdrant, weaviate, chroma, milvus, pgvector, redis'],
        ['chunking_strategy', 'ChunkingStrategy', 'FIXED, RECURSIVE, SEMANTIC, SENTENCE, DOCUMENT_AWARE, AGENTIC, CODE, MARKDOWN'],
        ['search_strategy', 'SearchStrategy', 'DENSE, SPARSE, HYBRID, MMR, MULTI_QUERY, HYDE, SELF_QUERY, PARENT_CHILD, STEP_BACK, CONTEXTUAL_COMPRESSION'],
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
      <p className="text-zinc-500 leading-relaxed">Unified interface for 9 vector database providers. Swap backends with a single config change.</p>
      <CodeBlock code={`from ai_core.vectorstore import VectorStoreFactory, VectorDocument
from ai_core.schemas import SearchQuery

store = VectorStoreFactory.create(
    provider="qdrant",
    collection="knowledge_base",
    config={"url": "http://localhost:6333"},
)

await store.upsert(documents=[
    VectorDocument(
        id="doc_001",
        text="Revenue increased 15% YoY...",
        metadata={"department": "finance", "year": 2025},
        namespace="finance",
    )
])

results = await store.search(
    SearchQuery(text="Q4 revenue", top_k=10, strategy="hybrid")
)
for r in results:
    print(r.id, r.score, r.text[:80])`} />
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
        <h3 className="text-2xl font-bold text-zinc-900">3. Search Strategies</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.search</span>
      </div>
      <DataTable headers={['Strategy', 'Latency', 'Relevance', 'Best For']} rows={[
        ['Dense (ANN)',              'Low',    'High',      'Semantic similarity'],
        ['Sparse (BM25)',            'Low',    'Medium',    'Keyword / exact match'],
        ['Hybrid (RRF)',             'Medium', 'Very High', 'General production use'],
        ['MMR',                     'Medium', 'High',      'Diverse context coverage'],
        ['Multi-Query',             'High',   'Very High', 'Complex / ambiguous queries'],
        ['HyDE',                    'High',   'High',      'Low-recall embedding spaces'],
        ['Self-Query',              'Medium', 'High',      'Filtered/structured search'],
        ['Parent-Child',            'Medium', 'High',      'Hierarchical documents'],
        ['Step-Back',               'High',   'Very High', 'Reasoning-heavy queries'],
        ['Contextual Compression',  'Medium', 'High',      'Token budget management'],
      ]} />
    </section>

    {/* 4. Chunking Engine */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-amber-50 text-amber-600 rounded-lg"><Layers size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">4. Chunking Engine</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.chunking</span>
      </div>
      <CodeBlock code={`from ai_core.chunking import ChunkingEngine, ChunkingConfig
from ai_core.schemas import ChunkingStrategy

engine = ChunkingEngine(
    strategy=ChunkingStrategy.SEMANTIC,
    config=ChunkingConfig(
        embedding_model="text-embedding-3-small",
        breakpoint_threshold=0.75,
        min_chunk_size=100,
        max_chunk_size=1000,
        overlap=50,
    )
)

chunks = engine.chunk(documents)
for c in chunks:
    print(c.text, c.index, c.metadata)`} />
      <DataTable headers={['Strategy', 'Speed', 'Quality', 'Use Case']} rows={[
        ['Fixed-Size',           'Fastest',  'Low',     'Quick prototyping'],
        ['Recursive Character',  'Fast',     'Medium',  'General text'],
        ['Sentence',             'Fast',     'Medium',  'NLP pipelines'],
        ['Semantic',             'Slow',     'Highest', 'Production RAG'],
        ['Document-Aware',       'Medium',   'High',    'Structured docs'],
        ['Agentic (LLM)',        'Slowest',  'Highest', 'Critical content'],
        ['Code-Aware',           'Fast',     'High',    'Source code'],
        ['Markdown/HTML',        'Fast',     'High',    'Web content'],
      ]} />
    </section>

    {/* 5. Prompt Engineering */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-rose-50 text-rose-600 rounded-lg"><Terminal size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">5. Prompt Engineering</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.prompts</span>
      </div>
      <CodeBlock code={`from ai_core.prompts import PromptEngine, PromptRegistry, DynamicExampleSelector
from ai_core.schemas import PromptStrategy

# â”€â”€ PromptEngine â”€â”€
engine = PromptEngine(llm=llm)
prompt = engine.build(
    strategy=PromptStrategy.CHAIN_OF_THOUGHT,
    task="Analyse the financial risk of this loan application.",
    context=retrieved_docs,
    examples=few_shot_examples,   # optional
)
response = await llm.generate(prompt)

# â”€â”€ PromptRegistry â€” named, versioned prompt templates â”€â”€
registry = PromptRegistry()
registry.register(
    name="rag_qa",
    template="Context:\\n{context}\\n\\nQuestion: {question}\\nAnswer:",
    version="1.2",
    metadata={"owner": "ai-team", "tested": True},
)
template = registry.get("rag_qa", version="1.2")
final   = template.format(context=docs, question=query)

# â”€â”€ DynamicExampleSelector â€” semantic few-shot selection â”€â”€
selector = DynamicExampleSelector(
    examples=example_pool,
    strategy="semantic",          # semantic | random | mmr | bm25 | maximal_marginal
    k=3,
    embedding_model="text-embedding-3-small",
)
few_shot_prompt = selector.select_and_render(query=user_input)`} />
      <DataTable headers={['Strategy', 'Description', 'Best For']} rows={[
        ['ZERO_SHOT',           'Instruction only, no examples',           'Simple tasks'],
        ['ONE_SHOT',            'Single example',                          'Format clarification'],
        ['FEW_SHOT',            'Multiple curated examples',               'Complex domain tasks'],
        ['CHAIN_OF_THOUGHT',    '"Think step by step" reasoning',          'Math / logic'],
        ['ZERO_SHOT_COT',       'CoT without examples',                    'Reasoning'],
        ['SELF_CONSISTENCY',    'N paths + majority vote',                 'Reliability-critical'],
        ['TREE_OF_THOUGHT',     'Multi-branch exploration',                'Planning / creative'],
        ['REACT',               'Reason + Act with tools',                 'Agent tasks'],
        ['REFLEXION',           'Self-critique loop',                      'Quality improvement'],
        ['PROGRAM_OF_THOUGHT',  'Code gen + execute',                      'Quantitative tasks'],
        ['ROLE',                'Expert persona',                          'Domain expertise'],
        ['META',                'LLM designs own prompt',                  'Prompt discovery'],
        ['SKELETON',            'Parallel sub-answers',                    'Latency reduction'],
        ['RAG',                 'Retrieved context injection',             'Knowledge-grounded'],
        ['DIRECTIONAL_STIMULUS','Guided hint / steering token',            'Guided generation'],
      ]} />
    </section>

    {/* 6. Agents */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg"><Users size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">6. Agentic AI Framework</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.agents</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">Enterprise multi-agent orchestration: 5 agent types, 6 coordination modes, pub/sub MessageBus, fluent AgentPipelineBuilder, and OrchestrationResult with consensus + metadata.</p>
      <CodeBlock code={`from ai_core.agents import (
    AgentExecutor, Tool, ToolRegistry, tool,
    MultiAgentSystem, AgentPipelineBuilder, AgentRole, MessageBus,
)
from ai_core.schemas import AgentType, CoordinationMode, AgentState

# â”€â”€ Tool registration â”€â”€
@tool("sql_query", description="Execute SQL against the data warehouse.")
async def sql_query(query: str, database: str = "analytics") -> str:
    return run_sql(query, database)

@ToolRegistry.register
class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for current information"
    input_schema = {"query": {"type": "string"}}
    async def run(self, query: str) -> str: ...

# â”€â”€ Create agents by type â”€â”€
react_agent     = AgentExecutor.create(AgentType.REACT,         llm=llm, tools=[...])
plan_agent      = AgentExecutor.create(AgentType.PLAN_EXECUTE,  llm=llm, tools=[...])
reflexion_agent = AgentExecutor.create(AgentType.REFLEXION,     llm=llm)
fc_agent        = AgentExecutor.create(AgentType.FUNCTION_CALL, llm=llm, tools=[...])
struct_agent    = AgentExecutor.create(AgentType.STRUCTURED,    llm=llm)

result = await react_agent.run("What were AAPL earnings last quarter?")
print(result.output, result.steps, result.tool_calls, result.tokens_used)

# â”€â”€ FunctionCallAgent â€” OpenAI structured tool schema â”€â”€
result = await fc_agent.run("Find quarterly revenue trends.")
for tc in result.tool_calls:  # [{"tool": ..., "args": {...}, "result": "..."}]
    print(f"{tc['tool']}({tc['args']}) â†’ {tc['result']}")

# â”€â”€ StructuredOutputAgent â€” Pydantic validation â”€â”€
from pydantic import BaseModel
class RiskReport(BaseModel):
    risk_level: str
    confidence: float
    factors: list[str]
result = await struct_agent.run("Assess loan #L-001.", output_schema=RiskReport)

# â”€â”€ Six coordination modes â”€â”€
system = MultiAgentSystem(
    agents=[research_agent, analysis_agent, writer_agent],
    mode=CoordinationMode.SEQUENTIAL,
)
result = await system.run("Summarise Q4 earnings.")
print(result.final_answer, result.metadata["stages_completed"], result.cost)

debate = MultiAgentSystem(
    agents=[bull_agent, bear_agent], mode=CoordinationMode.DEBATE, rounds=3
)
result = await debate.run("Fair value of this asset?")
print(result.consensus)          # synthesised consensus answer

# â”€â”€ Fluent pipeline builder â”€â”€
pipeline = (
    AgentPipelineBuilder()
    .add_stage("intake",   intake_agent)
    .add_stage("analyse",  analysis_agent)
    .add_stage("report",   writer_agent)
    .with_mode(CoordinationMode.SEQUENTIAL)
    .with_cost_limit(1.00)
    .build()
)
result = await pipeline.run("Generate compliance report")

# â”€â”€ MessageBus â€” pub/sub between agents â”€â”€
bus = MessageBus()
bus.subscribe("analysis.ready", lambda msg: route_to_writer(msg))
bus.publish(AgentMessage(sender="analyst", content="Analysis done", msg_type="info"))`} />
      <DataTable headers={['Agent Type', 'Strategy', 'Best For']} rows={[
        ['ReAct',           'Reason + Act loop',         'General tool use, search & answer'],
        ['PlanExecute',     'Plan then execute steps',   'Multi-step complex tasks'],
        ['Reflexion',       'Answer â†’ Reflect â†’ Correct','Quality improvement, self-correction'],
        ['FunctionCall',    'OpenAI structured tool API','API orchestration, structured args'],
        ['Structured',      'JSON/Pydantic output',      'Data extraction, form filling'],
      ]} />
      <DataTable headers={['Coordination Mode', 'Pattern', 'Best For']} rows={[
        ['SEQUENTIAL',   'A â†’ B â†’ C',                   'Report generation, data pipelines'],
        ['PARALLEL',     'A + B + C â†’ merge',           'Intelligence gathering, risk scoring'],
        ['DEBATE',       'A â†” B (N rounds)',            'Valuation, adversarial review'],
        ['HIERARCHICAL', 'Supervisor â†’ workers',        'Medical triage, compliance workflows'],
        ['SWARM',        'Shared workspace',            'Knowledge graph construction'],
        ['SUPERVISOR',   'Coordinator â†’ dynamic route', 'Loan underwriting, approvals'],
      ]} />
    </section>

    {/* 7. Multi-Framework */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-cyan-50 text-cyan-600 rounded-lg"><Puzzle size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">7. Multi-Framework Orchestration</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.frameworks</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">Unified adapters for LangChain, LangGraph, CrewAI, AutoGen, and MCP. Use <code>FrameworkAdapter.for_framework(name)</code> as the single entry point.</p>
      <CodeBlock code={`from ai_core.frameworks import FrameworkAdapter

# â”€â”€ LangChain â”€â”€
lc = FrameworkAdapter.for_framework("langchain")
chain = lc.build_rag_chain({"llm_model": "gpt-4o", "collection": "docs"})
result = await chain.ainvoke({"question": "What is RAG?"})

# â”€â”€ LangGraph (stateful workflow) â”€â”€
lg = FrameworkAdapter.for_framework("langgraph")
workflow = lg.build_workflow({"llm_model": "gpt-4o"})
result = await workflow.ainvoke({"question": "Summarize this document."})

# â”€â”€ CrewAI (collaborative agents) â”€â”€
crew = FrameworkAdapter.for_framework("crewai")
crew_obj = crew.build_crew({"verbose": True})
result = crew_obj.kickoff(inputs={"query": "Analyse AI market trends 2026"})

# â”€â”€ AutoGen (group chat) â”€â”€
ag = FrameworkAdapter.for_framework("autogen")
chat = ag.build_group_chat({"llm_model": "gpt-4o", "max_rounds": 5})
chat["user_proxy"].initiate_chat(chat["assistant"], message="Explain quantum computing.")

# â”€â”€ MCP (Model Context Protocol) â”€â”€
mcp = FrameworkAdapter.for_framework("mcp")   # MCPAdapter instance

@mcp.tool("search_kb")
async def search_kb(query: str, namespace: str) -> list[str]:
    """Search the enterprise knowledge base."""
    return await rag.query(query, namespace=namespace)

@mcp.resource("file://company-docs")
async def get_docs() -> str:
    return load_documents()

tools    = mcp.list_tools()        # [{"name": "search_kb", "description": "..."}]
resources = mcp.list_resources()   # ["file://company-docs"]`} />
      <DataTable headers={['Framework', 'Adapter Class', 'Key Method', 'Best For']} rows={[
        ['LangChain', 'LangChainAdapter', 'build_rag_chain(config)',    'LCEL pipelines'],
        ['LangGraph',  'LangGraphAdapter', 'build_workflow(config)',     'Stateful agent graphs'],
        ['CrewAI',     'CrewAIAdapter',    'build_crew(config)',         'Multi-role teams'],
        ['AutoGen',    'AutoGenAdapter',   'build_group_chat(config)',   'Conversational multi-agent'],
        ['MCP',        'MCPAdapter',       '@mcp.tool() + .list_tools()','Tool/resource exposure'],
      ]} />
    </section>

    {/* 8. Evaluation */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg"><FlaskConical size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">8. Evaluation Suite</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.eval</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">Four evaluator classes: built-in LLM-judge metrics, RAGAS framework, DeepEval framework, and a PipelineEvaluator wrapper. EvalReport exposes a .summary() dict.</p>
      <CodeBlock code={`from ai_core.eval import (
    RAGEvaluator, RAGASEvaluator, DeepEvalEvaluator, PipelineEvaluator
)
from ai_core.schemas import EvalReport

# â”€â”€ Built-in RAG evaluator (LLM-judge) â”€â”€
evaluator = RAGEvaluator(
    metrics=["faithfulness", "answer_relevancy", "context_recall",
             "context_precision", "hallucination"],
    llm_judge="gpt-4o",
)
report: EvalReport = await evaluator.evaluate(
    questions=test_questions,
    contexts=retrieved_docs_list,
    answers=generated_answers,
    ground_truths=golden_answers,
)
print(report.summary())    # {"faithfulness": 0.91, "hallucination": 0.04, ...}
for m in report.metrics:
    print(m.name, m.score, m.passed, m.details)

# â”€â”€ RAGAS framework â”€â”€
ragas_eval = RAGASEvaluator(metrics=["faithfulness", "answer_relevancy"])
report = await ragas_eval.evaluate(questions=qs, contexts=ctxs,
                                   answers=ans, ground_truths=gt)

# â”€â”€ DeepEval framework â”€â”€
deepeval = DeepEvalEvaluator(metrics=["hallucination", "answer_relevancy"])
report = await deepeval.evaluate(questions=qs, contexts=ctxs,
                                 answers=ans, ground_truths=gt)

# â”€â”€ PipelineEvaluator â€” eval against a live RAGPipeline â”€â”€
pipeline_eval = PipelineEvaluator(evaluator=evaluator, pipeline=rag)
report = await pipeline_eval.evaluate(
    questions=test_set, ground_truths=golden_answers,
)
print(report.summary())`} />
      <DataTable headers={['Evaluator', 'Backend', 'Key Metrics']} rows={[
        ['RAGEvaluator',      'Built-in (LLM judge)',  'faithfulness, answer_relevancy, context_recall, context_precision, hallucination'],
        ['RAGASEvaluator',    'RAGAS framework',       'faithfulness, answer_relevancy + all RAGAS metrics'],
        ['DeepEvalEvaluator', 'DeepEval framework',    'hallucination, answer_relevancy + all DeepEval metrics'],
        ['PipelineEvaluator', 'Wraps any evaluator',   'Evaluates against a live RAGPipeline'],
      ]} />
    </section>

    {/* 9. Deployment */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-sky-50 text-sky-600 rounded-lg"><Globe size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">9. Deployment & Geo-Routing</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.deployment</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">Multi-region geo-routing with latency-aware failover, edge deployment for ultra-low latency inference, hybrid cloud / on-prem management, and a unified DeploymentOrchestrator.</p>
      <CodeBlock code={`from ai_core.deployment import (
    GeoRouter, RegionConfig, RoutingStrategy,
    EdgeDeployment, EdgeConfig,
    HybridCloudManager, HybridConfig, ReplicationStrategy,
    DeploymentOrchestrator,
)

# â”€â”€ Geo Router â€” route to lowest-latency healthy region â”€â”€
router = GeoRouter(
    regions=[
        RegionConfig(name="us-east-1", primary=True,  weight=1.0),
        RegionConfig(name="eu-west-1", primary=False, weight=0.8),
        RegionConfig(name="ap-south-1",primary=False, weight=0.5),
    ],
    strategy=RoutingStrategy.GEO_LATENCY,  # GEO_LATENCY | ROUND_ROBIN | WEIGHTED | USER_LOCATION
    failover=True,
)
router.update_latency("us-east-1", latency_ms=45.0)
region = await router.route(user_location="London")
router.mark_unhealthy("us-east-1")      # triggers failover to eu-west-1

# â”€â”€ Edge deployment â”€â”€
edge = EdgeDeployment(EdgeConfig(
    locations=["nyc-edge-1", "lon-edge-2"],
    cache_strategy="semantic",
    cache_ttl_seconds=3600,
    model_quantization="fp16",
))
node = edge.deploy("nyc-edge-1", model_id="llama-3-8b-q4")
nearest = edge.get_nearest(user_location="New York")
print(edge.get_stats())     # total_nodes, active_nodes, total_requests, cache_hits

# â”€â”€ Hybrid cloud / on-prem â”€â”€
hybrid = HybridCloudManager(HybridConfig(
    cloud_provider="aws",
    cloud_vector_store="pinecone",
    on_prem_enabled=True,
    on_prem_vector_store="qdrant",
    fallback_strategy="on-prem-first",
    fallback_conditions=["on_prem_load>80", "on_prem_latency>1000ms"],
))
hybrid.update_on_prem_metrics(load=90.0, latency_ms=1200)
store = hybrid.get_vector_store()       # "pinecone" (fell back to cloud)

# â”€â”€ Orchestrator â€” single entry point â”€â”€
orchestrator = DeploymentOrchestrator(
    regions=[...], edge_config=EdgeConfig(...), hybrid_config=HybridConfig(...),
    routing_strategy=RoutingStrategy.GEO_LATENCY,
)
health = await orchestrator.health_check()  # edge stats + hybrid routing info`} />
      <DataTable headers={['Class', 'Routing Strategies']} rows={[
        ['GeoRouter',            'GEO_LATENCY, ROUND_ROBIN, WEIGHTED, USER_LOCATION'],
        ['EdgeDeployment',       'deploy(), get_nearest(), decommission(), get_stats()'],
        ['HybridCloudManager',   'cloud-first, on-prem-first + condition-based fallback'],
        ['DeploymentOrchestrator','Unified: router + edge + hybrid + health_check()'],
      ]} />
    </section>

    {/* 10. Recovery & DR */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-orange-50 text-orange-600 rounded-lg"><ShieldCheck size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">10. Recovery & Disaster Recovery</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.recovery</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">FailoverChain for automatic provider failover, BackupManager with S3/local backends, DRTest for automated failover testing, and ChaosEngineering for fault injection.</p>
      <CodeBlock code={`from ai_core.recovery import (
    FailoverChain, HAConfig,
    BackupManager, S3BackupBackend, LocalBackupBackend,
    DRTest, ChaosEngineering,
)

# â”€â”€ FailoverChain â€” automatic provider failover â”€â”€
chain = FailoverChain(
    providers=["openai", "anthropic", "azure_openai"],
    config=HAConfig(
        failure_threshold=3,
        recovery_timeout=60,
        health_check_interval=30,
    ),
)
active = chain.get_active_provider()          # "openai" (healthy)
chain.record_failure("openai")
chain.record_failure("openai")
chain.record_failure("openai")                # threshold reached â†’ opens circuit
active = chain.get_active_provider()          # "anthropic" (failover)
chain.record_success("openai")               # starts recovery

# â”€â”€ BackupManager â€” S3 or local backends â”€â”€
mgr = BackupManager(
    backend=S3BackupBackend(bucket="ai-backups", region="us-east-1"),
    auto_verify=True,
)
rec = await mgr.backup(
    data=pickle.dumps(vector_index),
    component="vector_index",
    tags={"env": "prod", "version": "2.1.0"},
)
print(rec.id, rec.size_bytes, rec.checksum)
data = await mgr.restore(rec.id)
ok   = await mgr.verify(rec.id)             # True if checksum matches
records = await mgr.list(component="vector_index")

# â”€â”€ DRTest â€” automated failover + backup verification â”€â”€
dr = DRTest()
result = await dr.run_failover_test(chain, simulate_provider="openai")
print(result.success, result.metrics["failover_seconds"])

result = await dr.run_backup_verify_test(mgr)
print(result.success, result.metrics)

# â”€â”€ ChaosEngineering â€” fault injection â”€â”€
chaos = ChaosEngineering()
sim_id = chaos.simulate_failure(
    service="vector_store", region="us-east-1",
    failure_type="latency_spike", duration_seconds=120,
)
affected = chaos.is_service_affected("vector_store", region="us-east-1")  # True
chaos.stop_simulation(sim_id)`} />
    </section>

    {/* 11. Configuration */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-zinc-100 text-zinc-600 rounded-lg"><Zap size={20} /></div>
        <h3 className="text-2xl font-bold text-zinc-900">11. Configuration</h3>
        <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">ai_core.config</span>
      </div>
      <p className="text-zinc-500 leading-relaxed">Hierarchical config loading from .env, YAML, HashiCorp Vault, and AWS Secrets Manager with a clear override precedence chain.</p>
      <CodeBlock code={`from ai_core.config import LibConfig

# Load from different sources â€” last one wins
config = LibConfig.from_env()               # reads .env + process env vars
config = LibConfig.from_yaml("ai.yml")      # YAML file
config = LibConfig.from_vault("kv/ai")      # HashiCorp Vault KV
config = LibConfig.from_aws("ai/prod")      # AWS Secrets Manager

# Override precedence (lowest â†’ highest):
# built-in defaults â†’ yaml â†’ .env file â†’ process env vars â†’ runtime overrides

# Access config values
llm_provider   = config.llm_provider        # "openai"
embedding_model= config.embedding_model     # "text-embedding-3-large"
vector_store   = config.vector_store_provider

# Runtime override
config.set("llm_model", "gpt-4o-mini")     # overrides for this session`} />
    </section>
  </div>
);

export default CoreLibraryPage;
