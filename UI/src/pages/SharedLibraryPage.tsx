import { SectionHeader, CodeBlock, Accordion, DataTable } from '../components/ui';

const sharedModules = [
  {
    title: 'Auth, JWT & RBAC',
    module: 'ai_shared.auth',
    desc: 'JWT validation, API key management, role-based access control (RBAC), and a unified AuthManager. Permissions include fine-grained actions like rag.query, rag.ingest, eval.*, admin.*.',
    code: `from ai_shared.auth import JWTValidator, APIKeyManager, RBAC, AuthManager, Permission

# JWT validation
validator = JWTValidator(secret="your-secret", algorithm="HS256")
result = validator.validate(token)
print(result.valid, result.user_id, result.roles, result.expires_at)

# API key management
key_mgr = APIKeyManager()
key = key_mgr.create(user_id="u1", roles=["data_scientist"], expires_days=90)
record = key_mgr.validate(key)          # returns _KeyRecord or None
key_mgr.revoke(key)

# RBAC — fine-grained permission model
rbac = RBAC()
rbac.add_role("data_scientist", permissions=[
    Permission.RAG_QUERY, Permission.RAG_INGEST, Permission.EVAL_RUN,
])
rbac.add_role("viewer", permissions=[Permission.RAG_QUERY])
rbac.add_user("alice", roles=["data_scientist"])
rbac.check(user_id="alice", permission=Permission.RAG_INGEST)  # True

# AuthManager — combined entry point
auth = AuthManager(jwt_validator=validator, key_manager=key_mgr, rbac=rbac)
result = auth.authenticate(token=bearer_token)
result = auth.authenticate(api_key=api_key)
auth.authorize(result.user_id, Permission.RAG_INGEST)`,
  },
  {
    title: 'Caching (Exact · Semantic · Redis · Multi-Layer)',
    module: 'ai_shared.cache',
    desc: 'Four cache backends: in-memory exact match, semantic similarity cache with configurable threshold, Redis-backed persistent cache, and a multi-layer cache that tries each layer in sequence.',
    code: `from ai_shared.cache import ExactCache, SemanticCache, RedisCache, MultiLayerCache

# ── Exact cache (in-memory, hash-keyed) ──
exact = ExactCache(max_size=1000, ttl_seconds=3600)
await exact.set("my_key", "cached_value")
hit = await exact.get("my_key")          # "cached_value" or None
await exact.delete("my_key")
exact.clear()

# ── Semantic cache (embedding-similarity lookup) ──
sem = SemanticCache(
    embedding_fn=embedder.embed,
    similarity_threshold=0.97,
    ttl_seconds=3600,
    max_size=500,
)
hit = await sem.get("What is RAG?")      # returns cached answer or None
await sem.set("What is RAG?", answer)

# ── Redis cache (persistent, distributed) ──
redis_cache = RedisCache(url="redis://localhost:6379", ttl_seconds=3600, prefix="ai:")
await redis_cache.set("key", {"answer": "..."})
val = await redis_cache.get("key")

# ── Multi-layer cache (L1=exact → L2=semantic → L3=redis) ──
cache = MultiLayerCache(layers=[exact, sem, redis_cache])
result = await cache.get(query)
if result is None:
    result = await rag.query(query)
    await cache.set(query, result)       # writes through to all layers`,
  },
  {
    title: 'Compliance (HIPAA · GDPR · SOC2 · PCI-DSS)',
    module: 'ai_shared.compliance',
    desc: 'Real verification checks for HIPAA, GDPR, SOC2/ISO27001, FedRAMP, and PCI-DSS. Generates exportable audit packages and compliance reports.',
    code: `from ai_shared.compliance import (
    HIPAACompliance, GDPRCompliance, SOC2Compliance,
    FedRAMPCompliance, PCIDSSCompliance, ComplianceExporter,
)

# HIPAA verification
hipaa = HIPAACompliance()
result = hipaa.verify_phi_handling(record)    # checks 18 PHI identifiers
result = hipaa.verify_encryption(data_store)  # AES-256, TLS 1.2+
result = hipaa.verify_access_controls(system)

# GDPR checks
gdpr = GDPRCompliance()
result = gdpr.verify_consent(user_record)
result = gdpr.check_data_minimization(collected_fields, required_fields)
result = gdpr.verify_right_to_erasure(user_id)

# SOC2 controls
soc2 = SOC2Compliance()
result = soc2.verify_availability(sla_config)
result = soc2.verify_confidentiality(encryption_config)

# PCI-DSS
pci = PCIDSSCompliance()
result = pci.verify_card_data_protection(storage_config)
result = pci.verify_network_security(firewall_config)

# Export audit package
exporter = ComplianceExporter(frameworks=[hipaa, gdpr, soc2])
package = exporter.export(output_dir="./audit/2026-Q1")
report  = exporter.generate_report()`,
  },
  {
    title: 'Cost Tracking & Optimization',
    module: 'ai_shared.cost',
    desc: 'Per-call cost recording with model pricing table, budget optimization suggestions, and quota management per user/team with configurable time windows.',
    code: `from ai_shared.cost import CostTracker, CostOptimizer, QuotaManager, QuotaConfig, estimate_cost

# ── Cost tracking ──
tracker = CostTracker()
tracker.record(
    model="gpt-4o", provider="openai",
    input_tokens=1200, output_tokens=400,
    request_id="req_001", user_id="alice", tags={"pipeline": "rag"},
)
print(tracker.total_cost())            # total $
print(tracker.cost_by_model())         # dict[model → $]
print(tracker.cost_by_user())          # dict[user → $]
records = tracker.filter(model="gpt-4o", since=yesterday)

# ── Cost optimization suggestions ──
optimizer = CostOptimizer(tracker)
suggestions = optimizer.suggest()
# e.g. OptimizationSuggestion(action="switch_model", from_model="gpt-4o",
#      to_model="gpt-4o-mini", estimated_savings=0.82, justification="...")

# ── Quota management ──
quota_mgr = QuotaManager()
quota_mgr.set_quota("alice", QuotaConfig(
    max_cost_usd=50.0, max_requests=1000, period_hours=24
))
status = quota_mgr.check("alice")      # QuotaStatus(within_limits, cost_used, requests_used)
quota_mgr.enforce("alice")             # raises QuotaExceededError if over limit

# ── Standalone cost estimation ──
cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=200)`,
  },
  {
    title: 'Feature Flags & A/B Experiments',
    module: 'ai_shared.experiments',
    desc: 'Percentage-based feature flags with per-user overrides, multi-variant experiment management, result recording, and statistical analytics for significance testing.',
    code: `from ai_shared.experiments import FeatureFlags, ExperimentManager, ExperimentAnalytics

# ── Feature flags with percentage rollout ──
flags = FeatureFlags()
flags.define("new_rag_pipeline", enabled=True, rollout_pct=20.0)
flags.define("gpt4o_responses",  enabled=True, allowed_users=["alice","bob"])
if flags.is_enabled("new_rag_pipeline", user_id=user.id):
    result = await new_pipeline.query(q)

flags.toggle("new_rag_pipeline", enabled=False)

# ── Multi-variant experiments ──
mgr = ExperimentManager()
exp = mgr.create(
    "rag_reranker_test",
    variants=[
        {"name": "control",  "config": {"reranker": "none"},   "weight": 1.0},
        {"name": "cohere",   "config": {"reranker": "cohere"},  "weight": 1.0},
        {"name": "bge",      "config": {"reranker": "bge"},     "weight": 1.0},
    ],
    description="Compare reranker impact on answer quality",
)
mgr.start(exp.experiment_id)
variant = mgr.assign(exp.experiment_id, user_id="u42")  # deterministic assignment
mgr.record_result(exp.experiment_id, user_id="u42",
    variant_id=variant.variant_id, metric="relevancy", value=0.91)
mgr.stop(exp.experiment_id)

# ── Analytics ──
analytics = ExperimentAnalytics(mgr)
report = analytics.summary(exp.experiment_id)
winner = analytics.best_variant(exp.experiment_id, metric="relevancy")`,
  },
  {
    title: 'Governance (Data Classification · Lineage · Policy · Audit · GDPR)',
    module: 'ai_shared.governance',
    desc: 'Data classification (PUBLIC→TOP_SECRET), full lineage tracking DAG, policy engine with rule evaluation, immutable audit logger, retention policies, and GDPR right-to-erasure.',
    code: `from ai_shared.governance import (
    DataClassifier, ClassificationLevel, DataLineageTracker,
    PolicyEngine, Policy, AuditLogger, RetentionManager, GDPRManager,
)

# ── Data classification ──
classifier = DataClassifier()
result = classifier.classify(text="SSN: 123-45-6789, salary: $120k")
print(result.level)          # ClassificationLevel.CONFIDENTIAL
print(result.reasons)        # ["contains_ssn", "contains_salary"]

# ── Data lineage DAG ──
lineage = DataLineageTracker()
lineage.add_node("raw_docs",   node_type="source",    metadata={"format": "pdf"})
lineage.add_node("chunks",     node_type="transform", metadata={"strategy": "semantic"})
lineage.add_node("embeddings", node_type="transform", metadata={"model": "text-embedding-3-large"})
lineage.add_edge("raw_docs", "chunks")
lineage.add_edge("chunks",   "embeddings")
lineage.get_lineage("embeddings")        # upstream path
lineage.export_graph()                   # dict suitable for visualization

# ── Policy engine ──
engine = PolicyEngine()
engine.add_policy(Policy(
    name="no_pii_in_logs",
    condition=lambda ctx: ctx.get("has_pii", False),
    action="block",
    severity="high",
))
result = engine.evaluate(context={"has_pii": True})
print(result.allowed, result.violated_policies)

# ── Immutable audit logger ──
audit = AuditLogger()
audit.log(user_id="alice", action="rag.query", resource="finance-q4",
          outcome="success", metadata={"tokens": 1200})
records = audit.query(user_id="alice", since=yesterday)

# ── Retention & GDPR ──
retention = RetentionManager()
retention.add_policy(RetentionPolicy(data_type="query_logs", retain_days=90))
actions = retention.enforce()            # list of records to delete/archive

gdpr = GDPRManager(audit_logger=audit)
gdpr.erase_user_data(user_id="alice", cascade=True)
export = gdpr.export_user_data(user_id="alice")`,
  },
  {
    title: 'Structured Logging',
    module: 'ai_shared.logging_utils',
    desc: 'JSON-formatted structured logging with contextual metadata binding, module-scoped loggers, log-level configuration, and an execution-timing decorator.',
    code: `from ai_shared.logging_utils import get_logger, LogContext, log_execution, JSONFormatter
import logging

# ── Module-scoped logger (JSON output) ──
logger = get_logger("rag.pipeline", level=logging.INFO, json=True)
logger.info("Query started", extra={"query": q, "namespace": ns, "user": user_id})
logger.warning("Slow retrieval", extra={"latency_ms": 2300, "strategy": "hybrid"})
logger.error("LLM failure",    extra={"model": "gpt-4o", "error": str(e)})

# ── Contextual metadata binding ──
with LogContext(logger, request_id="req_001", tenant="acme"):
    logger.info("Processing")       # all log lines inherit request_id + tenant
    await pipeline.run(query)

# ── Execution timing decorator ──
@log_execution(logger, level=logging.DEBUG)
async def run_pipeline(query: str) -> str:
    ...
# logs: "run_pipeline started", "run_pipeline completed in 1.23 s"`,
  },
  {
    title: 'Memory & Conversation State',
    module: 'ai_shared.memory',
    desc: '6 pluggable memory backends — Buffer, Summary (LLM-compressed), Vector (semantic recall), Redis (distributed), Postgres (queryable+audit), and Entity (named-entity tracking). MemoryFactory creates any backend by name.',
    code: `from ai_shared.memory import (
    ConversationBufferMemory, ConversationSummaryMemory,
    VectorMemory, RedisMemory, PostgresMemory, EntityMemory, MemoryFactory,
)

# ── Buffer memory (simple in-memory window) ──
buf = ConversationBufferMemory(max_messages=20)
buf.add_user("What is RAG?")
buf.add_assistant("RAG is retrieval-augmented generation...")
history = buf.get_history()              # list[{"role", "content"}]

# ── Summary memory (LLM compresses old turns) ──
summary = ConversationSummaryMemory(llm=llm, max_tokens=500)
await summary.add_user("Explain transformers in detail.")
await summary.add_assistant(long_explanation)
# older turns auto-summarized once token budget exceeded

# ── Vector memory (semantic recall) ──
vec_mem = VectorMemory(store=vector_store, top_k=5)
await vec_mem.save({"role": "user", "content": query})
relevant = await vec_mem.search("previous discussion about RAG")

# ── Redis memory (distributed sessions) ──
redis_mem = RedisMemory(url="redis://localhost:6379", session_id="sess_001", ttl=3600)
await redis_mem.add_user("Follow-up question...")

# ── Entity memory (tracks named entities) ──
entity_mem = EntityMemory(llm=llm)
await entity_mem.add_turn("Alice works at Acme Corp as a data scientist.")
entities = entity_mem.get_entities()     # {"Alice": {...}, "Acme Corp": {...}}

# ── MemoryFactory ──
mem = MemoryFactory.create("redis", url="redis://localhost:6379", session_id="s1")`,
  },
  {
    title: 'Model Registry & A/B Testing',
    module: 'ai_shared.models',
    desc: 'Versioned model registry with metadata, multi-variant A/B testing framework with traffic splitting and result recording, and a rollback manager for safe deployments.',
    code: `from ai_shared.models import ModelRegistry, ABTestingFramework, ABTestConfig, RollbackManager

# ── Model registry ──
registry = ModelRegistry()
registry.register(
    name="rag-pipeline-v2",
    version="2.1.0",
    provider="openai",
    model_id="gpt-4o",
    metadata={"latency_p99_ms": 1800, "cost_per_1k": 0.005},
)
v = registry.get("rag-pipeline-v2", version="2.1.0")
all_versions = registry.list_versions("rag-pipeline-v2")
latest = registry.get_latest("rag-pipeline-v2")

# ── A/B testing with traffic splitting ──
ab = ABTestingFramework()
config = ABTestConfig(
    experiment_id="gpt4o_vs_mini",
    variants={"control": 0.5, "treatment": 0.5},   # traffic weights
    metric="answer_quality",
)
ab.create(config)
variant = ab.assign(config.experiment_id, user_id="u1")  # "control" or "treatment"
ab.record(config.experiment_id, user_id="u1", variant=variant, score=0.88)
results = ab.analyze(config.experiment_id)   # statistical summary

# ── Safe rollback ──
rollback = RollbackManager(registry)
rollback.set_active("rag-pipeline-v2", version="2.1.0")
rollback.rollback("rag-pipeline-v2")         # reverts to previous version
rollback.history("rag-pipeline-v2")          # deployment history`,
  },
  {
    title: 'Observability & Tracing',
    module: 'ai_shared.observability',
    desc: 'Hierarchical span-based tracing with LangSmith, Langfuse, and OpenTelemetry exporters, a @trace decorator, and a MetricsCollector for counters, gauges, and histograms.',
    code: `from ai_shared.observability import (
    Tracer, get_tracer, trace, MetricsCollector,
    LangSmithExporter, LangfuseExporter, OpenTelemetryExporter,
)

# ── Tracer with exporters ──
tracer = Tracer()
tracer.add_exporter(LangSmithExporter(api_key=os.getenv("LANGSMITH_API_KEY")))
tracer.add_exporter(LangfuseExporter(public_key="pk-...", secret_key="sk-..."))
tracer.add_exporter(OpenTelemetryExporter(endpoint="http://otel-collector:4318"))

# ── Span-based tracing ──
with tracer.span("rag.query", attributes={"query": q, "namespace": ns}) as span:
    docs = await retriever.search(q)
    span.add_event("retrieval_complete", {"doc_count": len(docs)})
    answer = await llm.generate(prompt)
    span.set_attribute("tokens_used", answer.usage.total)

# ── @trace decorator ──
@trace("pipeline.full_run", track_tokens=True, track_cost=True)
async def run_pipeline(query: str) -> str:
    ...

# ── Metrics ──
metrics = MetricsCollector()
metrics.counter("rag.queries.total", tags={"namespace": ns}).increment()
metrics.histogram("rag.latency_ms").record(latency)
metrics.gauge("vector_store.docs").set(doc_count)
snapshot = metrics.snapshot()           # {"rag.queries.total": 1024, ...}`,
  },
  {
    title: 'Plugin System',
    module: 'ai_shared.plugins',
    desc: 'Central PluginRegistry for registering, discovering, and lifecycle-managing plugins. Supports dynamic module loading, a hook/event system, and a @plugin class decorator for metadata.',
    code: `from ai_shared.plugins import PluginRegistry, PluginMetadata, plugin

# ── @plugin decorator ──
@plugin("custom_vectorstore", version="1.0.0", category="vectorstore",
        description="Internal Weaviate cluster wrapper")
class InternalVectorStore:
    name = "custom_vectorstore"
    def initialize(self, config: dict) -> None: ...
    def shutdown(self) -> None: ...
    async def upsert(self, docs): ...
    async def search(self, query): ...

# ── Registry ──
registry = PluginRegistry()
registry.register(
    InternalVectorStore,
    metadata=InternalVectorStore._plugin_metadata,
    config={"url": "http://weaviate:8080"},
)

# Dynamic loading from a module path
registry.register_from_module("mycompany.plugins.llm_cache")

# Lookup & lifecycle
store = registry.get("custom_vectorstore")
plugins = registry.list_plugins()         # list[PluginMetadata]
registry.unregister("custom_vectorstore") # calls shutdown()

# ── Hook / event system ──
registry.add_hook("before_query", lambda ctx: log_query(ctx))
registry.add_hook("after_query",  lambda ctx: track_cost(ctx))
registry.emit("before_query", {"query": q, "user": uid})

registry.shutdown_all()                   # graceful teardown`,
  },
  {
    title: 'Resilience (Retry · Circuit Breaker · Rate Limiter · Timeout)',
    module: 'ai_shared.resilience',
    desc: 'Production-grade resilience primitives: configurable retry with exponential/jitter backoff, async circuit breaker with CLOSED→OPEN→HALF_OPEN state machine, token-bucket rate limiter, and async timeout decorator.',
    code: `from ai_shared.resilience import (
    retry, RetryConfig, BackoffStrategy,
    CircuitBreaker, CircuitState, CircuitOpenError,
    RateLimiter, with_timeout,
)

# ── Retry decorator with configurable backoff ──
@retry(RetryConfig(
    max_retries=4,
    initial_delay=0.5,
    backoff=BackoffStrategy.EXPONENTIAL_JITTER,  # exponential | linear | constant | exponential_jitter
    retry_on=(ConnectionError, TimeoutError),
))
async def call_llm(prompt: str) -> str:
    return await llm.generate(prompt)

# ── Circuit breaker (CLOSED → OPEN → HALF_OPEN) ──
breaker = CircuitBreaker(
    failure_threshold=5,       # opens after 5 failures
    recovery_timeout=30,       # seconds before HALF_OPEN
    success_threshold=2,       # successes needed to close
)
try:
    async with breaker:
        result = await external_api.call()
except CircuitOpenError:
    result = fallback_response()
print(breaker.state)           # CircuitState.OPEN / CLOSED / HALF_OPEN

# ── Token-bucket rate limiter ──
limiter = RateLimiter(rate=100, per_seconds=1.0, burst=20)
async with limiter:
    await llm.generate(prompt)

# ── Async timeout ──
@with_timeout(seconds=30.0)
async def slow_operation() -> str: ...`,
  },
  {
    title: 'Security (PII · Content Filter · Input Validation)',
    module: 'ai_shared.security',
    desc: 'PII detection and redaction (email, phone, SSN, credit card, IP, person, location, org), multi-category content filtering, and robust input validation against injection and prompt-injection attacks.',
    code: `from ai_shared.security import (
    PIIDetector, PIIType, PIIMatch,
    ContentFilter, ContentCategory, FilterResult,
    InputValidator, ValidationResult,
)

# ── PII detection & redaction ──
detector = PIIDetector()
matches: list[PIIMatch] = detector.detect("Call John at 555-1234 or john@example.com")
# [PIIMatch(type=PIIType.PHONE, text="555-1234", start=13, end=21),
#  PIIMatch(type=PIIType.EMAIL, text="john@example.com", ...)]

redacted = detector.redact(text)
# "Call John at [PHONE] or [EMAIL]"

# Custom redaction labels
redacted = detector.redact(text, replacements={
    PIIType.EMAIL: "<EMAIL_REDACTED>",
    PIIType.SSN: "<SSN_REDACTED>",
})
pii_types = detector.classify(text)      # set[PIIType]

# ── Content filtering ──
filter = ContentFilter(
    blocked=[ContentCategory.VIOLENCE, ContentCategory.HATE_SPEECH,
             ContentCategory.SELF_HARM, ContentCategory.SEXUAL],
)
result: FilterResult = await filter.check(user_input)
print(result.safe, result.categories_detected, result.score)

# ── Input validation (injection prevention) ──
validator = InputValidator(
    max_length=8192,
    block_patterns=["DROP TABLE", "<script>", "{{", "{%"],
    allow_html=False,
)
result: ValidationResult = validator.validate(user_input)
if not result.valid:
    raise ValueError(result.reason)`,
  },
  {
    title: 'Token Budget & Cost Estimation',
    module: 'ai_shared.tokens',
    desc: 'Token counting (tiktoken), budget allocation across prompt sections using GREEDY/PROPORTIONAL/PRIORITY/FIXED strategies, and per-model cost estimation.',
    code: `from ai_shared.tokens import (
    TokenBudget, BudgetStrategy,
    count_tokens, count_messages_tokens, estimate_cost,
)

# ── Token counting ──
n = count_tokens("Hello, world!", model="gpt-4o")          # 4
n = count_messages_tokens(messages, model="gpt-4o-mini")   # full thread count

# ── Per-model cost estimation ──
cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=200)

# ── Token budget (section-based allocation) ──
budget = TokenBudget(
    max_tokens=8192,
    model="gpt-4o",
    strategy=BudgetStrategy.PRIORITY,   # GREEDY | PROPORTIONAL | PRIORITY | FIXED
    reserve_output=1024,
)
budget.add_section("system",   content=system_prompt,   priority=3, min_tokens=100)
budget.add_section("context",  content=retrieved_docs,  priority=2)
budget.add_section("history",  content=chat_history,    priority=1)
budget.add_section("question", content=user_query,      priority=3, min_tokens=50)

fitted: dict[str, str] = budget.fit()
# {"system": "...", "context": "...(truncated)...", "history": "...", "question": "..."}
final_prompt = "\\n\\n".join(fitted.values())`,
  },
];

const SharedLibraryPage = () => (
  <div className="space-y-16">
    <SectionHeader
      badge="Shared Components"
      title="Shared Library — Full Module Reference"
      subtitle="14 cross-cutting utility modules consumed by all core components. Each module is fully independent with no circular dependencies."
    />

    {/* Module coverage table */}
    <DataTable
      headers={['Module', 'Package', 'Key Classes']}
      rows={[
        ['Auth & RBAC',        'ai_shared.auth',         'JWTValidator, APIKeyManager, RBAC, AuthManager'],
        ['Caching',            'ai_shared.cache',        'ExactCache, SemanticCache, RedisCache, MultiLayerCache'],
        ['Compliance',         'ai_shared.compliance',   'HIPAACompliance, GDPRCompliance, SOC2Compliance, PCIDSSCompliance'],
        ['Cost Tracking',      'ai_shared.cost',         'CostTracker, CostOptimizer, QuotaManager'],
        ['Feature Flags & A/B','ai_shared.experiments',  'FeatureFlags, ExperimentManager, ExperimentAnalytics'],
        ['Governance',         'ai_shared.governance',   'DataClassifier, DataLineageTracker, PolicyEngine, AuditLogger, GDPRManager'],
        ['Logging',            'ai_shared.logging_utils','get_logger, LogContext, log_execution, JSONFormatter'],
        ['Memory',             'ai_shared.memory',       'BufferMemory, SummaryMemory, VectorMemory, RedisMemory, PostgresMemory, EntityMemory'],
        ['Model Registry',     'ai_shared.models',       'ModelRegistry, ABTestingFramework, RollbackManager'],
        ['Observability',      'ai_shared.observability','Tracer, trace, MetricsCollector, LangSmithExporter'],
        ['Plugins',            'ai_shared.plugins',      'PluginRegistry, plugin() decorator'],
        ['Resilience',         'ai_shared.resilience',   'retry, CircuitBreaker, RateLimiter, with_timeout'],
        ['Security',           'ai_shared.security',     'PIIDetector, ContentFilter, InputValidator'],
        ['Token Budget',       'ai_shared.tokens',       'TokenBudget, count_tokens, estimate_cost, BudgetStrategy'],
      ]}
    />

    <div className="space-y-4">
      {sharedModules.map((m, i) => (
        <Accordion key={i} title={`${i + 1}. ${m.title}`} defaultOpen={i === 0}>
          <div className="space-y-4">
            <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">{m.module}</span>
            <p className="text-sm text-zinc-500">{m.desc}</p>
            <CodeBlock code={m.code} />
          </div>
        </Accordion>
      ))}
    </div>
  </div>
);

export default SharedLibraryPage;
