import { useState, type ReactNode } from 'react';
import { SectionHeader } from '../components/ui';
import { WorkflowRenderer, RAG_WORKFLOW, CAPA_WORKFLOW, AGENT_WORKFLOW, DEVIATION_WORKFLOW } from '../components/WorkflowRenderer';
import type { WorkflowConfig } from '../components/WorkflowRenderer';
import { GitBranch, ShieldCheck, Bot, AlertTriangle } from 'lucide-react';

const presets: { key: string; label: string; icon: ReactNode; description: string; config: WorkflowConfig }[] = [
  { key: 'rag', label: 'RAG Workflow', icon: <GitBranch size={16} />, description: 'Retrieval-Augmented Generation with caching, hybrid search, and citation tracking.', config: RAG_WORKFLOW },
  { key: 'capa', label: 'CAPA Workflow', icon: <ShieldCheck size={16} />, description: 'Corrective & Preventive Action — a 10-stage quality management process.', config: CAPA_WORKFLOW },
  { key: 'agent', label: 'Agent Orchestration', icon: <Bot size={16} />, description: 'Multi-agent pipeline with planning, parallel execution, and consensus.', config: AGENT_WORKFLOW },
  { key: 'deviation', label: 'Deviation Workflow', icon: <AlertTriangle size={16} />, description: 'Quality deviation management with AI validation and multi-level review.', config: DEVIATION_WORKFLOW },
];

const WorkflowsPage = () => {
  const [active, setActive] = useState('rag');
  const selected = presets.find(p => p.key === active)!;

  return (
    <div className="space-y-8">
      <SectionHeader
        badge="Visualizations"
        title="Workflow Patterns"
        subtitle="Explore dynamic workflow graphs with branching, conditions, and approval gates — click Simulate to watch execution flow."
      />

      {/* Preset selector */}
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

      {/* Description */}
      <p className="text-sm text-zinc-500">{selected.description}</p>

      {/* Workflow canvas */}
      <div className="bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm overflow-x-auto">
        <WorkflowRenderer config={selected.config} />
      </div>

      {/* Node type legend */}
      <div className="p-6 bg-zinc-50 border border-zinc-200 rounded-2xl">
        <h3 className="font-semibold text-zinc-900 mb-4">Node Types</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { type: 'start', emoji: '🚀', label: 'Start', color: 'bg-emerald-100 text-emerald-700' },
            { type: 'action', emoji: '⚙️', label: 'Action', color: 'bg-blue-100 text-blue-700' },
            { type: 'condition', emoji: '❓', label: 'Condition', color: 'bg-amber-100 text-amber-700' },
            { type: 'approval', emoji: '✅', label: 'Approval', color: 'bg-violet-100 text-violet-700' },
            { type: 'parallel', emoji: '🔀', label: 'Parallel', color: 'bg-cyan-100 text-cyan-700' },
            { type: 'error', emoji: '⚠️', label: 'Error', color: 'bg-red-100 text-red-700' },
            { type: 'end', emoji: '🏁', label: 'End', color: 'bg-zinc-100 text-zinc-700' },
          ].map(n => (
            <div key={n.type} className="flex items-center gap-3">
              <span className={'w-8 h-8 flex items-center justify-center rounded-lg text-sm ' + n.color}>{n.emoji}</span>
              <span className="text-sm text-zinc-700 font-medium">{n.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Workflow patterns explanation */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="p-5 bg-white border border-zinc-200 rounded-xl space-y-2">
          <h4 className="text-sm font-semibold text-zinc-900">Sequential Execution</h4>
          <p className="text-xs text-zinc-500 leading-relaxed">Nodes execute in strict order. Each node waits for the previous node to complete before starting. Ideal for linear processes like document approval.</p>
        </div>
        <div className="p-5 bg-white border border-zinc-200 rounded-xl space-y-2">
          <h4 className="text-sm font-semibold text-zinc-900">Conditional Branching</h4>
          <p className="text-xs text-zinc-500 leading-relaxed">Condition nodes evaluate an expression and route execution to one of multiple branches. Only the matching branch executes.</p>
        </div>
        <div className="p-5 bg-white border border-zinc-200 rounded-xl space-y-2">
          <h4 className="text-sm font-semibold text-zinc-900">Parallel Execution</h4>
          <p className="text-xs text-zinc-500 leading-relaxed">Parallel nodes fork execution into multiple concurrent branches. All branches must complete before the workflow continues past the join point.</p>
        </div>
        <div className="p-5 bg-white border border-zinc-200 rounded-xl space-y-2">
          <h4 className="text-sm font-semibold text-zinc-900">Approval Gates</h4>
          <p className="text-xs text-zinc-500 leading-relaxed">Approval nodes pause execution until a designated approver (single, all-must-approve, or any-can-approve) takes action.</p>
        </div>
      </div>
    </div>
  );
};

export default WorkflowsPage;
