import { useState, type ReactNode } from 'react';
import { SectionHeader } from '../components/ui';
import { AnimatedPipeline, RAG_PIPELINE, AGENT_PIPELINE, ENTERPRISE_PIPELINE } from '../components/AnimatedPipeline';
import type { PipelineConfig } from '../components/AnimatedPipeline';
import { Workflow, Bot, Building2 } from 'lucide-react';

const presets: { key: string; label: string; icon: ReactNode; config: PipelineConfig }[] = [
  { key: 'rag', label: 'RAG Pipeline', icon: <Workflow size={16} />, config: RAG_PIPELINE },
  { key: 'agent', label: 'Agent Pipeline', icon: <Bot size={16} />, config: AGENT_PIPELINE },
  { key: 'enterprise', label: 'Enterprise Pipeline', icon: <Building2 size={16} />, config: ENTERPRISE_PIPELINE },
];

const PipelinesPage = () => {
  const [active, setActive] = useState('rag');
  const selected = presets.find(p => p.key === active)!;

  return (
    <div className="space-y-8">
      <SectionHeader
        badge="Visualizations"
        title="Pipeline Flows"
        subtitle="Interactive, animated pipeline visualizations — click nodes for details and press Run to simulate execution."
      />

      {/* Preset tabs */}
      <div className="flex flex-wrap gap-2">
        {presets.map(p => (
          <button
            key={p.key}
            onClick={() => setActive(p.key)}
            className={
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ' +
              (active === p.key
                ? 'bg-zinc-900 text-white shadow-md'
                : 'bg-white border border-zinc-200 text-zinc-600 hover:border-zinc-400')
            }
          >
            {p.icon}
            {p.label}
          </button>
        ))}
      </div>

      {/* Pipeline canvas */}
      <div className="bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm">
        <AnimatedPipeline config={selected.config} />
      </div>

      {/* Overview legend */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-3 h-3 rounded-full bg-zinc-300" />
            <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Idle</span>
          </div>
          <p className="text-sm text-zinc-600">Step is configured and waiting for execution.</p>
        </div>
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-xs font-medium text-blue-600 uppercase tracking-wider">Running</span>
          </div>
          <p className="text-sm text-blue-700">Step is currently processing data.</p>
        </div>
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-xs font-medium text-emerald-600 uppercase tracking-wider">Complete</span>
          </div>
          <p className="text-sm text-emerald-700">Step finished successfully.</p>
        </div>
      </div>

      {/* How it works */}
      <div className="p-6 bg-zinc-50 border border-zinc-200 rounded-2xl space-y-4">
        <h3 className="font-semibold text-zinc-900">How Pipeline Execution Works</h3>
        <div className="grid md:grid-cols-2 gap-6 text-sm text-zinc-600">
          <div className="space-y-2">
            <p><strong className="text-zinc-800">Sequential Flow:</strong> Each step processes its input and passes output to the next step through typed channels.</p>
            <p><strong className="text-zinc-800">Error Handling:</strong> Failed steps trigger configurable retry policies (exponential backoff, dead-letter queues).</p>
          </div>
          <div className="space-y-2">
            <p><strong className="text-zinc-800">Observability:</strong> Every step emits latency, token count, and cost metrics through the shared observability layer.</p>
            <p><strong className="text-zinc-800">Caching:</strong> Embedding and search results are cached with configurable TTLs to reduce redundant computation.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelinesPage;
