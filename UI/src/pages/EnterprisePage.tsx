import { ShieldCheck, DollarSign, Workflow, Globe, Server, Database, FlaskConical, Activity, GitBranch, Shield, Lock, FileText } from 'lucide-react';
import { SectionHeader, CodeBlock, DataTable, FeatureCard } from '../components/ui';

const EnterprisePage = () => (
  <div className="space-y-16">
    <SectionHeader badge="Enterprise" title="Enterprise Operations & Governance" subtitle="Data governance, cost management, model lifecycle, multi-region deployment, and disaster recovery." />

    {/* Data Governance */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg"><ShieldCheck size={20} /></div>
        <h3 className="text-xl font-bold text-zinc-900">Data Governance</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FeatureCard icon={<GitBranch size={20} />} title="Data Lineage" description="Track document provenance: Source to Chunks to Embeddings to Queries" tags={['Traceability', 'Compliance']} />
        <FeatureCard icon={<Shield size={20} />} title="Data Classification" description="Auto-classify PII, sensitive, and public data during ingestion" tags={['PII Detection', 'Auto-Classify']} />
        <FeatureCard icon={<Lock size={20} />} title="Access Control" description="Hybrid RBAC + ABAC model enforced at retrieval time" tags={['RBAC', 'ABAC', 'Namespace']} />
        <FeatureCard icon={<FileText size={20} />} title="Audit Trail" description="Immutable audit logs for all operations with cost and compliance evidence" tags={['Immutable', 'Elasticsearch']} />
      </div>
      <CodeBlock code={'from ai_core.governance import DataLineageTracker, AuditLogger\n\ntracker = DataLineageTracker()\n\n@tracker.trace(stage=\"ingestion\")\nasync def ingest(doc):\n    chunks = await chunker.chunk(doc)\n    for chunk in chunks:\n        chunk.provenance = ProvenanceMetadata(\n            source_uri=doc.source_uri,\n            processing_steps=[\"chunking\", \"embedding\", \"indexing\"]\n        )\n    return chunks\n\naudit = AuditLogger(backend=\"elasticsearch\", retention_days=365)\n\n@audit.log(event_type=AuditEventType.QUERY, include_cost=True)\nasync def query_rag(user, query):\n    return await rag.query(query)'} />
    </section>

    {/* Cost Management */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-green-50 text-green-600 rounded-lg"><DollarSign size={20} /></div>
        <h3 className="text-xl font-bold text-zinc-900">Cost Management & Optimization</h3>
      </div>
      <CodeBlock code={'from ai_core.cost import CostTracker, QuotaManager\n\ntracker = CostTracker(\n    backends=[\"openai\", \"anthropic\", \"pinecone\"],\n    budget_limit_per_month=10000,\n    alert_thresholds=[0.5, 0.75, 0.9, 0.95],\n)\n\ntracker.track(model=\"gpt-4o\", input_tokens=500, output_tokens=200)\n\nif tracker.check_budget_exceeded():\n    llm.set_fallback_model(\"gpt-4o-mini\")\n\nquota = QuotaManager(backend=\"redis\")\nawait quota.set_quota(\"data_science_team\", quotas=[\n    Quota(name=\"daily_tokens\", limit=1_000_000, period=\"day\"),\n    Quota(name=\"monthly_cost\", limit=5000, period=\"month\"),\n])'} />
    </section>

    {/* Model Lifecycle */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-purple-50 text-purple-600 rounded-lg"><Workflow size={20} /></div>
        <h3 className="text-xl font-bold text-zinc-900">Model Lifecycle Management</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <FeatureCard icon={<Database size={20} />} title="Model Registry" description="Version, stage (dev > staging > production), metrics tracking, and artifact storage" tags={['Versioning', 'Stages']} />
        <FeatureCard icon={<FlaskConical size={20} />} title="A/B Testing" description="Traffic splitting, consistent user bucketing, automatic metric tracking" tags={['Traffic Split', 'Experiments']} />
        <FeatureCard icon={<Activity size={20} />} title="Auto-Rollback" description="Real-time performance monitoring with automatic rollback on degradation" tags={['Monitoring', 'Recovery']} />
      </div>
    </section>

    {/* Multi-Region */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-amber-50 text-amber-600 rounded-lg"><Globe size={20} /></div>
        <h3 className="text-xl font-bold text-zinc-900">Multi-Region & Edge Deployment</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { region: 'US-East-1', role: 'Primary', llm: 'AWS Bedrock', flag: '🇺🇸' },
          { region: 'EU-West-1', role: 'GDPR', llm: 'Anthropic EU', flag: '🇪🇺' },
          { region: 'AP-Southeast-1', role: 'Asia Pacific', llm: 'Azure OpenAI', flag: '🇸🇬' },
        ].map((r, i) => (
          <div key={i} className="p-6 bg-white border border-zinc-200 rounded-xl">
            <div className="text-2xl mb-2">{r.flag}</div>
            <h4 className="font-bold text-zinc-900">{r.region}</h4>
            <p className="text-sm text-zinc-500 mt-1">Role: {r.role}</p>
            <p className="text-sm text-zinc-500">LLM: {r.llm}</p>
          </div>
        ))}
      </div>
    </section>

    {/* DR */}
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-red-50 text-red-600 rounded-lg"><Server size={20} /></div>
        <h3 className="text-xl font-bold text-zinc-900">Disaster Recovery & High Availability</h3>
      </div>
      <DataTable headers={['Metric', 'Target', 'Strategy']} rows={[
        ['Recovery Point Objective', '60 seconds', 'Async replication across regions'],
        ['Recovery Time Objective', '15 minutes', 'Auto-failover with circuit breaker'],
        ['Replication Factor', '3 nodes', 'Qdrant cluster with read replicas'],
        ['LLM Failover', '4-provider chain', 'OpenAI > Anthropic > Azure > Bedrock'],
        ['Cache Layers', '3 layers', 'Redis (1ms) > Memcached (5ms) > Postgres (50ms)'],
        ['Backup Schedule', 'Daily', 'S3 encrypted + compressed backups'],
        ['DR Testing', 'Weekly', 'Automated chaos engineering tests'],
      ]} />
    </section>

    {/* NFR */}
    <section className="space-y-6">
      <h3 className="text-xl font-bold text-zinc-900">Non-Functional Requirements</h3>
      <DataTable headers={['Requirement', 'Target', 'Measurement']} rows={[
        ['RAG Query Latency (p99)', '< 3 seconds', 'End-to-end tracing'],
        ['Throughput', '100+ concurrent', 'Load testing'],
        ['Embedding Batch', '10K chunks/min', 'Batch benchmarks'],
        ['Test Coverage', '>= 90%', 'pytest-cov'],
        ['Type Safety', '100% typed', 'mypy strict'],
        ['Python Version', '3.11+', 'pyproject.toml'],
        ['Package Size', 'Core < 5MB', 'Build metrics'],
        ['Cold Start', '< 500ms', 'Import timing'],
        ['Availability', '99.9%', 'Uptime monitoring'],
      ]} />
    </section>
  </div>
);

export default EnterprisePage;
