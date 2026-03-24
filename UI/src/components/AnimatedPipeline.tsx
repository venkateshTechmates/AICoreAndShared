import { useState, useEffect, useRef, Fragment } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Play, RotateCcw, CheckCircle2, Loader2, Clock, Zap } from 'lucide-react';

// ── Types ──────────────────────────────────────────────────────
export interface PipelineStep {
  id: string;
  label: string;
  emoji: string;
  subtitle: string;
  details: string[];
  metrics?: { label: string; value: string }[];
}

export interface PipelineConfig {
  title: string;
  description: string;
  steps: PipelineStep[];
}

// ── Preset Pipeline Configs ────────────────────────────────────
export const RAG_PIPELINE: PipelineConfig = {
  title: 'RAG Pipeline',
  description: 'End-to-end Retrieval-Augmented Generation with hybrid search, reranking, and streaming.',
  steps: [
    { id: 'validate', label: 'Validate', emoji: '🛡️', subtitle: 'Input security', details: ['Content filter check', 'PII detection (Presidio)', 'Rate limit enforcement', 'Prompt injection guard'], metrics: [{ label: 'Latency', value: '~5ms' }, { label: 'Block Rate', value: '0.3%' }] },
    { id: 'cache', label: 'Cache', emoji: '⚡', subtitle: 'Semantic lookup', details: ['Cosine similarity ≥ 0.97', 'Multi-layer: Redis → Memcached → Postgres', 'TTL: 3600s default', 'Hit ratio tracking'], metrics: [{ label: 'Hit Rate', value: '~35%' }, { label: 'Latency', value: '~2ms' }] },
    { id: 'transform', label: 'Transform', emoji: '🔄', subtitle: 'Query rewrite', details: ['Multi-Query expansion', 'HyDE hypothetical doc', 'Step-Back abstraction', 'Intent classification'], metrics: [{ label: 'Queries', value: '3-5x' }, { label: 'Tokens', value: '~200' }] },
    { id: 'embed', label: 'Embed', emoji: '🧬', subtitle: '3072-dim vector', details: ['text-embedding-3-large', '3072 dimensions', 'Batch size: 512', 'L2 normalization'], metrics: [{ label: 'Dims', value: '3072' }, { label: 'Cost', value: '$0.13/1M' }] },
    { id: 'search', label: 'Search', emoji: '🔍', subtitle: 'Hybrid retrieval', details: ['Dense ANN (weight 0.7)', 'Sparse BM25 (weight 0.3)', 'RRF fusion scoring', 'Top-K: 10 candidates'], metrics: [{ label: 'Strategy', value: 'Hybrid' }, { label: 'Top-K', value: '10' }] },
    { id: 'rerank', label: 'Rerank', emoji: '📊', subtitle: 'Cross-encoder', details: ['Cohere Reranker v3', 'Top-3 selection', 'Score threshold: 0.25', 'Diversity penalty'], metrics: [{ label: 'Model', value: 'Cohere' }, { label: 'Output', value: 'Top 3' }] },
    { id: 'assemble', label: 'Assemble', emoji: '📋', subtitle: 'Context build', details: ['Token budget fitting', 'Deduplication', 'Source ordering', 'Citation mapping'], metrics: [{ label: 'Max Tokens', value: '8000' }, { label: 'Strategy', value: 'Priority' }] },
    { id: 'generate', label: 'Generate', emoji: '✨', subtitle: 'LLM response', details: ['GPT-4o / Claude 3.5', 'Chain-of-Thought prompting', 'Streaming output', 'Citation injection'], metrics: [{ label: 'Model', value: 'GPT-4o' }, { label: 'Temp', value: '0.1' }] },
    { id: 'postprocess', label: 'Post', emoji: '✅', subtitle: 'Output checks', details: ['PII re-check on output', 'Content filter', 'Citation verification', 'Audit trail logging'], metrics: [{ label: 'Checks', value: '4' }, { label: 'Log', value: 'LangSmith' }] },
  ],
};

export const AGENT_PIPELINE: PipelineConfig = {
  title: 'Agent Pipeline',
  description: 'Multi-step autonomous agent with tool usage, reasoning, and self-reflection loops.',
  steps: [
    { id: 'parse', label: 'Parse', emoji: '📝', subtitle: 'Intent analysis', details: ['Task decomposition', 'Intent classification', 'Entity extraction', 'Context window setup'], metrics: [{ label: 'Method', value: 'LLM' }, { label: 'Tokens', value: '~150' }] },
    { id: 'plan', label: 'Plan', emoji: '🗺️', subtitle: 'Strategy build', details: ['Plan-and-Execute pattern', 'Sub-task generation', 'Tool selection', 'Dependency ordering'], metrics: [{ label: 'Steps', value: '3-8' }, { label: 'Pattern', value: 'PlanExec' }] },
    { id: 'tools', label: 'Tools', emoji: '🔧', subtitle: 'Tool dispatch', details: ['Web search', 'Code execution', 'API calls', 'Database queries'], metrics: [{ label: 'Registry', value: '12 tools' }, { label: 'Timeout', value: '30s' }] },
    { id: 'reason', label: 'Reason', emoji: '🧠', subtitle: 'ReAct loop', details: ['Thought → Action → Observe', 'Max 10 iterations', 'Early stopping', 'Confidence scoring'], metrics: [{ label: 'Max Iter', value: '10' }, { label: 'Type', value: 'ReAct' }] },
    { id: 'reflect', label: 'Reflect', emoji: '🪞', subtitle: 'Self-critique', details: ['Reflexion pattern', 'Output quality check', 'Retry with feedback', 'Hallucination guard'], metrics: [{ label: 'Pattern', value: 'Reflexion' }, { label: 'Retries', value: '≤3' }] },
    { id: 'respond', label: 'Respond', emoji: '💬', subtitle: 'Final output', details: ['Structured response', 'Source attribution', 'Confidence score', 'Memory update'], metrics: [{ label: 'Format', value: 'JSON' }, { label: 'Memory', value: 'Vector' }] },
  ],
};

export const ENTERPRISE_PIPELINE: PipelineConfig = {
  title: 'Enterprise Pipeline',
  description: 'Full enterprise flow with auth, compliance, cost tracking, caching, and audit trail.',
  steps: [
    { id: 'auth', label: 'Auth', emoji: '🔐', subtitle: 'JWT + RBAC', details: ['JWT token validation', 'Role-based access check', 'Namespace authorization', 'API key verification'], metrics: [{ label: 'Method', value: 'JWT' }, { label: 'RBAC', value: 'Yes' }] },
    { id: 'comply', label: 'Comply', emoji: '📜', subtitle: 'Policy engine', details: ['Rate limit enforcement', 'Content policy check', 'Data residency rules', 'GDPR compliance gate'], metrics: [{ label: 'Policies', value: '12' }, { label: 'Engine', value: 'OPA' }] },
    { id: 'budget', label: 'Budget', emoji: '💰', subtitle: 'Cost control', details: ['Token budget check', 'Monthly cost limit', 'Team quota enforcement', 'Model cost routing'], metrics: [{ label: 'Limit', value: '$10K/mo' }, { label: 'Alert', value: '75%' }] },
    { id: 'cache', label: 'Cache', emoji: '⚡', subtitle: 'Multi-layer', details: ['L1: Redis (1ms)', 'L2: Memcached (5ms)', 'L3: Postgres (50ms)', 'Semantic similarity'], metrics: [{ label: 'Layers', value: '3' }, { label: 'Hit', value: '~40%' }] },
    { id: 'pipeline', label: 'RAG', emoji: '🔍', subtitle: 'Core pipeline', details: ['Hybrid search + rerank', 'Circuit breaker wrapper', 'Retry with backoff', 'Fallback model chain'], metrics: [{ label: 'Search', value: 'Hybrid' }, { label: 'Breaker', value: 'Yes' }] },
    { id: 'filter', label: 'Filter', emoji: '🛡️', subtitle: 'Output security', details: ['PII redaction on output', 'Hallucination check', 'Content filter', 'Citation verification'], metrics: [{ label: 'Checks', value: '4' }, { label: 'Block', value: '< 1%' }] },
    { id: 'observe', label: 'Observe', emoji: '📡', subtitle: 'Telemetry', details: ['OpenTelemetry traces', 'Prometheus metrics', 'LangSmith logging', 'Cost attribution'], metrics: [{ label: 'Trace', value: 'OTel' }, { label: 'Metrics', value: 'Prom' }] },
    { id: 'audit', label: 'Audit', emoji: '📒', subtitle: 'Compliance log', details: ['Immutable audit trail', 'Elasticsearch backend', 'User attribution', 'Retention: 365 days'], metrics: [{ label: 'Backend', value: 'ES' }, { label: 'Retain', value: '365d' }] },
  ],
};

// ── AnimatedPipeline Component ─────────────────────────────────
export function AnimatedPipeline({ config }: { config: PipelineConfig }) {
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [elapsedMs, setElapsedMs] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const runPipeline = () => {
    if (running) return;
    setRunning(true);
    setCompletedSteps(new Set());
    setActiveStep(0);
    setElapsedMs(0);
    let step = 0;
    const timer = setInterval(() => setElapsedMs(t => t + 100), 100);
    intervalRef.current = timer;

    const advance = () => {
      if (step >= config.steps.length) {
        clearInterval(timer);
        intervalRef.current = null;
        setRunning(false);
        setActiveStep(null);
        return;
      }
      setActiveStep(step);
      setCompletedSteps(prev => new Set([...prev, step]));
      step++;
      setTimeout(advance, 600 + Math.random() * 400);
    };
    setTimeout(advance, 500);
  };

  const reset = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setRunning(false);
    setActiveStep(null);
    setCompletedSteps(new Set());
    setElapsedMs(0);
  };

  useEffect(() => () => { if (intervalRef.current) clearInterval(intervalRef.current); }, []);

  const progress = config.steps.length > 0 ? (completedSteps.size / config.steps.length) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h3 className="text-xl font-bold text-zinc-900">{config.title}</h3>
          <p className="text-sm text-zinc-500 mt-1">{config.description}</p>
        </div>
        <div className="flex items-center gap-3">
          {elapsedMs > 0 && (
            <span className="text-xs font-mono text-zinc-400 flex items-center gap-1">
              <Clock size={12} /> {(elapsedMs / 1000).toFixed(1)}s
            </span>
          )}
          <button onClick={reset} className="p-2 rounded-lg bg-zinc-100 text-zinc-500 hover:bg-zinc-200 transition-colors" title="Reset">
            <RotateCcw size={16} />
          </button>
          <button
            onClick={runPipeline}
            disabled={running}
            className={'px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 transition-all ' +
              (running ? 'bg-zinc-300 text-zinc-500 cursor-not-allowed' : 'bg-zinc-900 text-white hover:bg-zinc-800 shadow-lg shadow-zinc-900/20')}
          >
            {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {running ? 'Running...' : 'Run Pipeline'}
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-zinc-100 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 via-violet-500 to-emerald-500 rounded-full"
          animate={{ width: progress + '%' }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Pipeline nodes */}
      <div className="overflow-x-auto pb-4">
        <div className="flex items-center gap-0 min-w-max px-2 py-6">
          {config.steps.map((step, idx) => (
            <Fragment key={step.id}>
              {/* Node */}
              <motion.div
                className={'relative shrink-0 w-28 cursor-pointer rounded-2xl border-2 p-4 text-center transition-all ' + (
                  activeStep === idx
                    ? 'border-blue-500 bg-blue-50 shadow-lg shadow-blue-500/20 scale-110 z-10'
                    : completedSteps.has(idx)
                    ? 'border-emerald-400 bg-emerald-50 shadow-md'
                    : 'border-zinc-200 bg-white hover:border-zinc-400 hover:shadow-sm'
                )}
                whileHover={!running ? { y: -4 } : undefined}
                onClick={() => setActiveStep(activeStep === idx ? null : idx)}
              >
                {/* Status indicator */}
                {completedSteps.has(idx) && activeStep !== idx && (
                  <div className="absolute -top-2 -right-2 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center shadow-sm">
                    <CheckCircle2 size={12} className="text-white" />
                  </div>
                )}
                {activeStep === idx && running && (
                  <div className="absolute -top-2 -right-2 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center animate-pulse">
                    <Loader2 size={12} className="text-white animate-spin" />
                  </div>
                )}

                <div className="text-2xl mb-1.5">{step.emoji}</div>
                <div className="text-xs font-bold text-zinc-900 leading-tight">{step.label}</div>
                <div className="text-[9px] text-zinc-400 mt-0.5 leading-tight">{step.subtitle}</div>
              </motion.div>

              {/* Connection arrow */}
              {idx < config.steps.length - 1 && (
                <div className="shrink-0 w-10 flex items-center justify-center">
                  <svg width="40" height="16" className="overflow-visible">
                    <line
                      x1="0" y1="8" x2="32" y2="8"
                      stroke={completedSteps.has(idx) && (completedSteps.has(idx + 1) || activeStep === idx + 1) ? '#22c55e' : completedSteps.has(idx) ? '#3b82f6' : '#d4d4d8'}
                      strokeWidth="2"
                      strokeDasharray="6 4"
                      className={completedSteps.has(idx) ? 'animate-dash-flow' : ''}
                    />
                    <polygon
                      points="30,3 38,8 30,13"
                      fill={completedSteps.has(idx) && (completedSteps.has(idx + 1) || activeStep === idx + 1) ? '#22c55e' : completedSteps.has(idx) ? '#3b82f6' : '#d4d4d8'}
                    />
                  </svg>
                </div>
              )}
            </Fragment>
          ))}
        </div>
      </div>

      {/* Details panel */}
      <AnimatePresence mode="wait">
        {activeStep !== null && (
          <motion.div
            key={activeStep}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="p-6 bg-white border border-zinc-200 rounded-2xl shadow-sm"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{config.steps[activeStep].emoji}</span>
                <div>
                  <h4 className="text-lg font-bold text-zinc-900">{config.steps[activeStep].label}</h4>
                  <p className="text-sm text-zinc-500">{config.steps[activeStep].subtitle}</p>
                </div>
              </div>
              <span className="px-2.5 py-1 bg-zinc-100 text-zinc-500 rounded-full text-[10px] font-mono uppercase">
                Step {activeStep + 1}/{config.steps.length}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h5 className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-3">Details</h5>
                <ul className="space-y-2">
                  {config.steps[activeStep].details.map((d, i) => (
                    <li key={i} className="flex items-center gap-2.5 text-sm text-zinc-600">
                      <Zap size={12} className="text-amber-500 shrink-0" />
                      {d}
                    </li>
                  ))}
                </ul>
              </div>
              {config.steps[activeStep].metrics && (
                <div>
                  <h5 className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-3">Metrics</h5>
                  <div className="grid grid-cols-2 gap-3">
                    {config.steps[activeStep].metrics!.map((m, i) => (
                      <div key={i} className="p-3 bg-zinc-50 rounded-xl">
                        <div className="text-[10px] text-zinc-400 uppercase tracking-wider">{m.label}</div>
                        <div className="text-sm font-bold text-zinc-900 mt-0.5">{m.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
