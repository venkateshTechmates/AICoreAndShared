import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Play, RotateCcw, Loader2, CheckCircle2, XCircle, Clock, ArrowRight } from 'lucide-react';

// ── Types ──────────────────────────────────────────────────────
export interface WFNode {
  id: string;
  label: string;
  type: 'start' | 'action' | 'condition' | 'approval' | 'parallel' | 'end' | 'error';
  row: number;
  col: number;
  description?: string;
}

export interface WFEdge {
  from: string;
  to: string;
  label?: string;
  type?: 'success' | 'failure' | 'default';
}

export interface WorkflowConfig {
  title: string;
  description: string;
  nodes: WFNode[];
  edges: WFEdge[];
}

// ── Preset Workflows ──────────────────────────────────────────
export const RAG_WORKFLOW: WorkflowConfig = {
  title: 'RAG Query Workflow',
  description: 'Complete retrieval-augmented generation workflow with caching and fallback.',
  nodes: [
    { id: 'start', label: 'User Query', type: 'start', row: 0, col: 2 },
    { id: 'validate', label: 'Input Validation', type: 'action', row: 1, col: 2, description: 'PII check, content filter, rate limit' },
    { id: 'cache_check', label: 'Cache Hit?', type: 'condition', row: 2, col: 2, description: 'Semantic cache lookup (threshold ≥ 0.97)' },
    { id: 'cache_return', label: 'Return Cached', type: 'action', row: 3, col: 0, description: 'Return cached response instantly' },
    { id: 'transform', label: 'Query Transform', type: 'action', row: 3, col: 3, description: 'Multi-query, HyDE, or Step-Back' },
    { id: 'embed', label: 'Embed Query', type: 'action', row: 4, col: 3, description: 'text-embedding-3-large → 3072d vector' },
    { id: 'search', label: 'Hybrid Search', type: 'parallel', row: 5, col: 3, description: 'Dense (0.7) + Sparse BM25 (0.3) + RRF' },
    { id: 'rerank', label: 'Rerank Top-K', type: 'action', row: 6, col: 3, description: 'Cohere cross-encoder → Top 3' },
    { id: 'generate', label: 'LLM Generate', type: 'action', row: 7, col: 2, description: 'GPT-4o with CoT prompting + streaming' },
    { id: 'postcheck', label: 'Quality OK?', type: 'condition', row: 8, col: 2, description: 'Hallucination check, PII re-check' },
    { id: 'audit', label: 'Audit & Cache', type: 'action', row: 9, col: 2, description: 'Log to LangSmith, store in cache' },
    { id: 'end', label: 'Response', type: 'end', row: 10, col: 2 },
    { id: 'fallback', label: 'Fallback Model', type: 'error', row: 9, col: 4, description: 'Switch to backup LLM and retry' },
  ],
  edges: [
    { from: 'start', to: 'validate' },
    { from: 'validate', to: 'cache_check' },
    { from: 'cache_check', to: 'cache_return', label: 'Hit', type: 'success' },
    { from: 'cache_check', to: 'transform', label: 'Miss', type: 'default' },
    { from: 'cache_return', to: 'end', type: 'success' },
    { from: 'transform', to: 'embed' },
    { from: 'embed', to: 'search' },
    { from: 'search', to: 'rerank' },
    { from: 'rerank', to: 'generate' },
    { from: 'generate', to: 'postcheck' },
    { from: 'postcheck', to: 'audit', label: 'Pass', type: 'success' },
    { from: 'postcheck', to: 'fallback', label: 'Fail', type: 'failure' },
    { from: 'fallback', to: 'generate', type: 'default' },
    { from: 'audit', to: 'end' },
  ],
};

export const CAPA_WORKFLOW: WorkflowConfig = {
  title: 'CAPA Quality Workflow',
  description: 'Corrective & Preventive Action workflow with multi-stage approval gates.',
  nodes: [
    { id: 'start', label: 'CAPA Initiated', type: 'start', row: 0, col: 2 },
    { id: 'rca', label: 'Root Cause Analysis', type: 'action', row: 1, col: 2, description: 'Investigate root cause using 5-Why, Fishbone' },
    { id: 'plan', label: 'Action Planning', type: 'action', row: 2, col: 2, description: 'Define corrective and preventive actions' },
    { id: 'dept_review', label: 'Department Review', type: 'approval', row: 3, col: 2, description: 'Department head reviews and approves plan' },
    { id: 'approved1', label: 'Approved?', type: 'condition', row: 4, col: 2 },
    { id: 'qa_review', label: 'QA Review', type: 'approval', row: 5, col: 2, description: 'Quality Assurance validates the approach' },
    { id: 'implement', label: 'Implement Actions', type: 'action', row: 6, col: 2, description: 'Execute corrective and preventive actions' },
    { id: 'effectiveness', label: 'Effectiveness OK?', type: 'condition', row: 7, col: 2, description: 'Verify actions resolved the issue' },
    { id: 'closure', label: 'CAPA Closure', type: 'action', row: 8, col: 2, description: 'Final documentation and sign-off' },
    { id: 'end', label: 'Complete', type: 'end', row: 9, col: 2 },
    { id: 'rework', label: 'Revise Plan', type: 'error', row: 4, col: 4, description: 'Update action plan based on feedback' },
    { id: 'reopen', label: 'Reopen Investigation', type: 'error', row: 7, col: 4, description: 'Actions ineffective, re-investigate' },
  ],
  edges: [
    { from: 'start', to: 'rca' },
    { from: 'rca', to: 'plan' },
    { from: 'plan', to: 'dept_review' },
    { from: 'dept_review', to: 'approved1' },
    { from: 'approved1', to: 'qa_review', label: 'Yes', type: 'success' },
    { from: 'approved1', to: 'rework', label: 'No', type: 'failure' },
    { from: 'rework', to: 'plan', type: 'default' },
    { from: 'qa_review', to: 'implement' },
    { from: 'implement', to: 'effectiveness' },
    { from: 'effectiveness', to: 'closure', label: 'Effective', type: 'success' },
    { from: 'effectiveness', to: 'reopen', label: 'Ineffective', type: 'failure' },
    { from: 'reopen', to: 'rca', type: 'default' },
    { from: 'closure', to: 'end' },
  ],
};

export const AGENT_WORKFLOW: WorkflowConfig = {
  title: 'Multi-Agent Orchestration',
  description: 'Autonomous multi-agent system with parallel execution and debate consensus.',
  nodes: [
    { id: 'start', label: 'Task Input', type: 'start', row: 0, col: 2 },
    { id: 'planner', label: 'Planner Agent', type: 'action', row: 1, col: 2, description: 'Decomposes task into sub-tasks' },
    { id: 'parallel', label: 'Parallel Dispatch', type: 'parallel', row: 2, col: 2, description: 'Fan-out to specialist agents' },
    { id: 'researcher', label: 'Researcher', type: 'action', row: 3, col: 0, description: 'Web search, knowledge retrieval' },
    { id: 'analyst', label: 'Analyst', type: 'action', row: 3, col: 2, description: 'Data analysis, calculations' },
    { id: 'writer', label: 'Writer', type: 'action', row: 3, col: 4, description: 'Content drafting, formatting' },
    { id: 'merge', label: 'Merge Results', type: 'parallel', row: 4, col: 2, description: 'Combine outputs from all agents' },
    { id: 'debate', label: 'Quality Debate', type: 'condition', row: 5, col: 2, description: 'Agents critique and vote on quality' },
    { id: 'refine', label: 'Refine Output', type: 'action', row: 6, col: 2, description: 'Incorporate feedback, improve' },
    { id: 'consensus', label: 'Consensus?', type: 'condition', row: 7, col: 2 },
    { id: 'end', label: 'Final Output', type: 'end', row: 8, col: 2 },
    { id: 'retry', label: 'Retry Agents', type: 'error', row: 7, col: 4, description: 'Re-dispatch with updated context' },
  ],
  edges: [
    { from: 'start', to: 'planner' },
    { from: 'planner', to: 'parallel' },
    { from: 'parallel', to: 'researcher' },
    { from: 'parallel', to: 'analyst' },
    { from: 'parallel', to: 'writer' },
    { from: 'researcher', to: 'merge', type: 'success' },
    { from: 'analyst', to: 'merge', type: 'success' },
    { from: 'writer', to: 'merge', type: 'success' },
    { from: 'merge', to: 'debate' },
    { from: 'debate', to: 'refine', type: 'default' },
    { from: 'refine', to: 'consensus' },
    { from: 'consensus', to: 'end', label: 'Agreed', type: 'success' },
    { from: 'consensus', to: 'retry', label: 'Disagreed', type: 'failure' },
    { from: 'retry', to: 'parallel', type: 'default' },
  ],
};

export const DEVIATION_WORKFLOW: WorkflowConfig = {
  title: 'Deviation Management',
  description: '10-stage quality deviation workflow from initiation through QA closure.',
  nodes: [
    { id: 'start', label: 'Deviation Report', type: 'start', row: 0, col: 2 },
    { id: 'initiate', label: 'Initiation', type: 'action', row: 1, col: 2, description: 'Create deviation event with details' },
    { id: 'ai_check', label: 'AI Validation', type: 'action', row: 2, col: 2, description: 'Automated AI-powered risk assessment' },
    { id: 'qa_review', label: 'QA Review', type: 'approval', row: 3, col: 2, description: 'Quality Assurance initial review' },
    { id: 'critical', label: 'Critical?', type: 'condition', row: 4, col: 2 },
    { id: 'hod_review', label: 'HOD Review', type: 'approval', row: 5, col: 1, description: 'Head of Department review' },
    { id: 'plant_head', label: 'Plant Head', type: 'approval', row: 5, col: 3, description: 'Plant Head review for critical deviations' },
    { id: 'action', label: 'Action Execution', type: 'action', row: 6, col: 2, description: 'Implement corrective actions' },
    { id: 'verify', label: 'HOD Verification', type: 'approval', row: 7, col: 2, description: 'HOD verifies action completion' },
    { id: 'qa_close', label: 'QA Closure', type: 'action', row: 8, col: 2, description: 'Final QA closure and documentation' },
    { id: 'end', label: 'Closed', type: 'end', row: 9, col: 2 },
  ],
  edges: [
    { from: 'start', to: 'initiate' },
    { from: 'initiate', to: 'ai_check' },
    { from: 'ai_check', to: 'qa_review' },
    { from: 'qa_review', to: 'critical' },
    { from: 'critical', to: 'hod_review', label: 'Minor', type: 'default' },
    { from: 'critical', to: 'plant_head', label: 'Critical', type: 'failure' },
    { from: 'hod_review', to: 'action', type: 'success' },
    { from: 'plant_head', to: 'action', type: 'success' },
    { from: 'action', to: 'verify' },
    { from: 'verify', to: 'qa_close' },
    { from: 'qa_close', to: 'end' },
  ],
};

// ── Node Styling ──────────────────────────────────────────────
const nodeStyles: Record<WFNode['type'], { bg: string; border: string; text: string; shape: string }> = {
  start: { bg: 'bg-emerald-50', border: 'border-emerald-400', text: 'text-emerald-700', shape: 'rounded-full' },
  action: { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-700', shape: 'rounded-xl' },
  condition: { bg: 'bg-amber-50', border: 'border-amber-400', text: 'text-amber-700', shape: 'rounded-xl rotate-0' },
  approval: { bg: 'bg-purple-50', border: 'border-purple-300', text: 'text-purple-700', shape: 'rounded-xl' },
  parallel: { bg: 'bg-cyan-50', border: 'border-cyan-400', text: 'text-cyan-700', shape: 'rounded-xl' },
  end: { bg: 'bg-zinc-100', border: 'border-zinc-400', text: 'text-zinc-700', shape: 'rounded-full' },
  error: { bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-600', shape: 'rounded-xl' },
};

const nodeIcons: Record<WFNode['type'], string> = {
  start: '🚀', action: '⚙️', condition: '❓', approval: '✅', parallel: '🔀', end: '🏁', error: '⚠️',
};

// ── WorkflowRenderer Component ────────────────────────────────
export function WorkflowRenderer({ config }: { config: WorkflowConfig }) {
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [visitedNodes, setVisitedNodes] = useState<Set<string>>(new Set());
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const CELL_W = 160;
  const CELL_H = 80;
  const NODE_W = 140;
  const NODE_H = 56;
  const PADDING = 30;

  const maxRow = Math.max(...config.nodes.map(n => n.row));
  const maxCol = Math.max(...config.nodes.map(n => n.col));
  const svgW = (maxCol + 1) * CELL_W + PADDING * 2;
  const svgH = (maxRow + 1) * CELL_H + PADDING * 2;

  const nodePos = (node: WFNode) => ({
    x: PADDING + node.col * CELL_W + (CELL_W - NODE_W) / 2,
    y: PADDING + node.row * CELL_H + (CELL_H - NODE_H) / 2,
    cx: PADDING + node.col * CELL_W + CELL_W / 2,
    cy: PADDING + node.row * CELL_H + CELL_H / 2,
  });

  // Build execution order (BFS from start)
  const getExecutionOrder = (): string[] => {
    const order: string[] = [];
    const visited = new Set<string>();
    const queue = config.nodes.filter(n => n.type === 'start').map(n => n.id);
    while (queue.length > 0) {
      const id = queue.shift()!;
      if (visited.has(id)) continue;
      visited.add(id);
      order.push(id);
      const outEdges = config.edges.filter(e => e.from === id);
      for (const edge of outEdges) {
        if (!visited.has(edge.to)) queue.push(edge.to);
      }
    }
    return order;
  };

  const runWorkflow = () => {
    if (running) return;
    setRunning(true);
    setVisitedNodes(new Set());
    setCurrentNode(null);
    const order = getExecutionOrder();
    let i = 0;

    const advance = () => {
      if (i >= order.length) {
        setRunning(false);
        setCurrentNode(null);
        return;
      }
      setCurrentNode(order[i]);
      setVisitedNodes(prev => new Set([...prev, order[i]]));
      i++;
      intervalRef.current = setTimeout(advance, 500 + Math.random() * 300);
    };
    advance();
  };

  const reset = () => {
    if (intervalRef.current) clearTimeout(intervalRef.current);
    setRunning(false);
    setCurrentNode(null);
    setVisitedNodes(new Set());
    setActiveNode(null);
  };

  useEffect(() => () => { if (intervalRef.current) clearTimeout(intervalRef.current); }, []);

  const selectedNode = config.nodes.find(n => n.id === activeNode);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h3 className="text-xl font-bold text-zinc-900">{config.title}</h3>
          <p className="text-sm text-zinc-500 mt-1">{config.description}</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={reset} className="p-2 rounded-lg bg-zinc-100 text-zinc-500 hover:bg-zinc-200 transition-colors">
            <RotateCcw size={16} />
          </button>
          <button
            onClick={runWorkflow}
            disabled={running}
            className={'px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 transition-all ' +
              (running ? 'bg-zinc-300 text-zinc-500 cursor-not-allowed' : 'bg-zinc-900 text-white hover:bg-zinc-800 shadow-lg shadow-zinc-900/20')}
          >
            {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {running ? 'Simulating...' : 'Simulate'}
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs">
        {Object.entries(nodeStyles).map(([type, style]) => (
          <div key={type} className="flex items-center gap-1.5">
            <div className={'w-3 h-3 border-2 ' + style.border + ' ' + style.bg + ' ' + style.shape} />
            <span className="text-zinc-500 capitalize">{type}</span>
          </div>
        ))}
      </div>

      {/* Workflow graph */}
      <div className="overflow-x-auto bg-zinc-50 border border-zinc-200 rounded-2xl p-4">
        <svg width={svgW} height={svgH} className="mx-auto">
          {/* Edges */}
          {config.edges.map((edge, idx) => {
            const fromNode = config.nodes.find(n => n.id === edge.from);
            const toNode = config.nodes.find(n => n.id === edge.to);
            if (!fromNode || !toNode) return null;
            const f = nodePos(fromNode);
            const t = nodePos(toNode);
            const isActive = visitedNodes.has(edge.from) && visitedNodes.has(edge.to);
            const edgeColor = edge.type === 'failure' ? '#ef4444' : edge.type === 'success' ? '#22c55e' : '#94a3b8';
            const activeColor = isActive ? edgeColor : '#d4d4d8';

            // Simple path from bottom of source to top of target
            const x1 = f.cx;
            const y1 = f.cy + NODE_H / 2;
            const x2 = t.cx;
            const y2 = t.cy - NODE_H / 2;
            const midY = (y1 + y2) / 2;

            return (
              <g key={idx}>
                <path
                  d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
                  fill="none"
                  stroke={activeColor}
                  strokeWidth={isActive ? 2.5 : 1.5}
                  strokeDasharray={isActive ? '8 4' : '4 4'}
                  className={isActive ? 'animate-dash-flow' : ''}
                  markerEnd={`url(#arrow-${isActive ? 'active' : 'inactive'}-${edge.type || 'default'})`}
                />
                {edge.label && (
                  <text x={(x1 + x2) / 2 + 8} y={midY - 4} fontSize="9" fill="#a1a1aa" fontWeight="500" textAnchor="middle">
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Arrow markers */}
          <defs>
            {['default', 'success', 'failure'].flatMap(type =>
              ['active', 'inactive'].map(state => {
                const color = state === 'inactive' ? '#d4d4d8' : type === 'failure' ? '#ef4444' : type === 'success' ? '#22c55e' : '#94a3b8';
                return (
                  <marker key={`${state}-${type}`} id={`arrow-${state}-${type}`} viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill={color} />
                  </marker>
                );
              })
            )}
          </defs>

          {/* Nodes */}
          {config.nodes.map(node => {
            const pos = nodePos(node);
            const style = nodeStyles[node.type];
            const isCurrent = currentNode === node.id;
            const isVisited = visitedNodes.has(node.id);
            const isSelected = activeNode === node.id;

            return (
              <g key={node.id} onClick={() => setActiveNode(activeNode === node.id ? null : node.id)} className="cursor-pointer">
                {/* Glow effect for current node */}
                {isCurrent && (
                  <rect
                    x={pos.x - 4} y={pos.y - 4} width={NODE_W + 8} height={NODE_H + 8}
                    rx={node.type === 'start' || node.type === 'end' ? NODE_H / 2 + 4 : 16}
                    fill="none" stroke="#3b82f6" strokeWidth="2"
                    opacity="0.6"
                  >
                    <animate attributeName="opacity" values="0.3;0.8;0.3" dur="1.2s" repeatCount="indefinite" />
                  </rect>
                )}
                {/* Node background */}
                <rect
                  x={pos.x} y={pos.y} width={NODE_W} height={NODE_H}
                  rx={node.type === 'start' || node.type === 'end' ? NODE_H / 2 : 12}
                  fill={isCurrent ? '#eff6ff' : isVisited ? '#f0fdf4' : 'white'}
                  stroke={isCurrent ? '#3b82f6' : isVisited ? '#86efac' : isSelected ? '#a1a1aa' : '#e4e4e7'}
                  strokeWidth={isCurrent || isSelected ? 2.5 : 1.5}
                />
                {/* Icon */}
                <text x={pos.x + 14} y={pos.cy + 1} fontSize="14" textAnchor="middle" dominantBaseline="middle">
                  {nodeIcons[node.type]}
                </text>
                {/* Label */}
                <text x={pos.x + 28} y={pos.cy + 1} fontSize="11" fontWeight="600" fill="#18181b" dominantBaseline="middle">
                  {node.label}
                </text>
                {/* Visited checkmark */}
                {isVisited && !isCurrent && (
                  <circle cx={pos.x + NODE_W - 8} cy={pos.y + 8} r="7" fill="#22c55e">
                    <text x={pos.x + NODE_W - 8} y={pos.y + 8} fontSize="8" fill="white" textAnchor="middle" dominantBaseline="middle">✓</text>
                  </circle>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Node detail panel */}
      <AnimatePresence mode="wait">
        {selectedNode && selectedNode.description && (
          <motion.div
            key={selectedNode.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="p-5 bg-white border border-zinc-200 rounded-xl shadow-sm"
          >
            <div className="flex items-center gap-3">
              <span className="text-xl">{nodeIcons[selectedNode.type]}</span>
              <div>
                <h4 className="font-bold text-zinc-900">{selectedNode.label}</h4>
                <span className={'text-[10px] font-medium uppercase tracking-wider px-2 py-0.5 rounded-full ' + nodeStyles[selectedNode.type].bg + ' ' + nodeStyles[selectedNode.type].text}>
                  {selectedNode.type}
                </span>
              </div>
            </div>
            <p className="text-sm text-zinc-500 mt-3">{selectedNode.description}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
