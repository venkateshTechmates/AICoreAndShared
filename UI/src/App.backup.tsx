import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Database, 
  Users, 
  ShieldCheck, 
  Terminal, 
  LayoutDashboard, 
  Settings, 
  HelpCircle, 
  ChevronRight, 
  Activity, 
  DollarSign, 
  Cpu, 
  Search,
  Code,
  Layers,
  Zap,
  Box,
  Globe,
  Lock,
  BarChart3,
  FileText,
  Trash2,
  Plus,
  Play,
  CheckCircle2,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { ModuleType, AgentRole, Deployment, LineageEntry, AgentTeam } from './types';
import { GoogleGenAI } from "@google/genai";

// Initialize Gemini
const genAI = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || '' });

const RAGDesigner = ({ onDeploy, onLog }: { onDeploy: (d: Deployment) => void, onLog: (l: LineageEntry) => void }) => {
  const [selectedStep, setSelectedStep] = useState<number | null>(0);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployStatus, setDeployStatus] = useState<'idle' | 'processing' | 'success'>('idle');

  const steps = [
    { step: '01', title: 'Ingestion', icon: <FileText size={20} />, desc: 'PDF, CSV, JSON, Web, SQL', details: 'Configuring connectors for S3, Google Drive, and local file systems. Auto-sync enabled.' },
    { step: '02', title: 'Chunking', icon: <Layers size={20} />, desc: 'Semantic, Recursive, Fixed', details: 'Using semantic boundary detection with a 512 token window and 10% overlap.' },
    { step: '03', title: 'Embedding', icon: <Cpu size={20} />, desc: 'OpenAI, Cohere, HuggingFace', details: 'Deploying text-embedding-3-large with 3072 dimensions for maximum precision.' },
    { step: '04', title: 'Vector Store', icon: <Database size={20} />, desc: 'Qdrant, Pinecone, Weaviate', details: 'Initializing Qdrant cluster in us-east-1 with HNSW indexing enabled.' },
    { step: '05', title: 'Search', icon: <Search size={20} />, desc: 'Hybrid, MMR, Reranking', details: 'Hybrid search enabled (Alpha: 0.5) with BGE-Reranker-v2 integration.' },
    { step: '06', title: 'Generation', icon: <Terminal size={20} />, desc: 'GPT-4o, Claude 3, Llama 3', details: 'Configured with GPT-4o-mini for speed and Claude-3-Opus for complex reasoning fallbacks.' },
  ];

  const handleDeploy = () => {
    setIsDeploying(true);
    setDeployStatus('processing');
    
    // Log the deployment start
    onLog({
      source: 'RAG Pipeline Designer',
      op: 'Deployment Started',
      status: 'Processing',
      tokens: 'N/A',
      time: 'Just now'
    });

    setTimeout(() => {
      const newDeployment: Deployment = {
        id: Math.random().toString(36).substr(2, 9),
        name: `RAG Pipeline ${new Date().toLocaleTimeString()}`,
        type: 'RAG Pipeline',
        region: 'us-east-1',
        status: 'Healthy',
        traffic: '0%',
        updated: 'Just now',
        config: { steps }
      };

      onDeploy(newDeployment);
      onLog({
        source: newDeployment.name,
        op: 'Ingestion & Embedding',
        status: 'Success',
        tokens: '120k',
        time: 'Just now'
      });

      setDeployStatus('success');
      setTimeout(() => {
        setIsDeploying(false);
        setDeployStatus('idle');
      }, 3000);
    }, 2500);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-zinc-900 font-sans tracking-tight">RAG Pipeline Designer</h2>
          <p className="text-zinc-500 text-sm mt-1">Configure your end-to-end retrieval augmented generation workflow.</p>
        </div>
        <button 
          onClick={handleDeploy}
          disabled={isDeploying}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
            deployStatus === 'success' 
              ? 'bg-green-600 text-white' 
              : 'bg-zinc-900 text-white hover:bg-zinc-800 disabled:opacity-50'
          }`}
        >
          {deployStatus === 'processing' ? <Loader2 size={16} className="animate-spin" /> : deployStatus === 'success' ? <CheckCircle2 size={16} /> : <Zap size={16} />}
          {deployStatus === 'processing' ? 'Deploying...' : deployStatus === 'success' ? 'Deployed' : 'Deploy Pipeline'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {steps.map((item, i) => (
          <div 
            key={i} 
            onClick={() => setSelectedStep(i)}
            className={`p-6 bg-white border rounded-xl transition-all cursor-pointer group relative overflow-hidden ${
              selectedStep === i ? 'border-zinc-900 ring-1 ring-zinc-900' : 'border-zinc-200 hover:border-zinc-400'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono text-zinc-400 font-medium uppercase tracking-widest">{item.step}</span>
              <div className={`p-2 rounded-lg transition-colors ${
                selectedStep === i ? 'bg-zinc-900 text-white' : 'bg-zinc-50 text-zinc-600 group-hover:bg-zinc-900 group-hover:text-white'
              }`}>
                {item.icon}
              </div>
            </div>
            <h3 className="font-semibold text-zinc-900 mb-1">{item.title}</h3>
            <p className="text-sm text-zinc-500">{item.desc}</p>
            {selectedStep === i && (
              <motion.div 
                layoutId="active-indicator"
                className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-900"
              />
            )}
          </div>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {selectedStep !== null && (
          <motion.div 
            key={selectedStep}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-8 bg-zinc-50 border border-zinc-200 rounded-2xl"
          >
            <div className="flex items-start gap-6">
              <div className="p-4 bg-white border border-zinc-200 rounded-xl text-zinc-900">
                {steps[selectedStep].icon}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-zinc-900 mb-2">{steps[selectedStep].title} Configuration</h3>
                <p className="text-zinc-600 text-sm leading-relaxed mb-6">
                  {steps[selectedStep].details}
                </p>
                <div className="flex gap-3">
                  <button className="px-4 py-2 bg-white border border-zinc-200 rounded-lg text-xs font-medium hover:bg-zinc-100 transition-colors">
                    Advanced Settings
                  </button>
                  <button className="px-4 py-2 bg-white border border-zinc-200 rounded-lg text-xs font-medium hover:bg-zinc-100 transition-colors">
                    View Documentation
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="p-8 bg-zinc-900 border border-zinc-800 rounded-2xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Code size={20} className="text-zinc-500" />
            <h3 className="font-semibold text-white">Generated Python SDK Code</h3>
          </div>
          <button className="text-xs text-zinc-400 hover:text-white transition-colors font-mono uppercase tracking-widest">Copy Code</button>
        </div>
        <pre className="text-zinc-400 font-mono text-sm overflow-x-auto leading-relaxed">
{`from ai_core import AICore

# Initialize with enterprise config
ai = AICore.from_yaml("config.yml")

# Step 1: Ingest with ${steps[0].desc.split(',')[0]}
await ai.ingest(
    documents=["docs/report.pdf"],
    chunking="${steps[1].title.toLowerCase()}",
    namespace="finance"
)

# Step 2: Query using ${steps[4].title} strategy
response = await ai.query(
    query="What were the Q4 revenue drivers?",
    search_strategy="${steps[4].desc.split(',')[0].toLowerCase()}",
    prompt_technique="chain_of_thought"
)`}
        </pre>
      </div>
    </motion.div>
  );
};

const AgentOrchestrator = ({ onDeploy, onLog }: { onDeploy: (d: Deployment) => void, onLog: (l: LineageEntry) => void }) => {
  const [agents, setAgents] = useState<AgentRole[]>([
    { id: '1', name: 'Researcher', tools: ['Google Search', 'ArXiv'], llm: 'GPT-4o', memory: 'vector' },
    { id: '2', name: 'Analyst', tools: ['Python Code', 'SQL'], llm: 'Claude 3.5', memory: 'summary' },
    { id: '3', name: 'Writer', tools: ['Markdown', 'PDF Gen'], llm: 'GPT-4o', memory: 'buffer' },
  ]);
  const [coordination, setCoordination] = useState<'hierarchical' | 'swarm'>('hierarchical');

  const addAgent = () => {
    const newAgent: AgentRole = {
      id: Math.random().toString(36).substr(2, 9),
      name: 'New Agent',
      tools: ['Custom Tool'],
      llm: 'GPT-4o',
      memory: 'buffer'
    };
    setAgents([...agents, newAgent]);
  };

  const removeAgent = (id: string) => {
    setAgents(agents.filter(a => a.id !== id));
  };

  const handleInitialize = () => {
    const newDeployment: Deployment = {
      id: Math.random().toString(36).substr(2, 9),
      name: `Agent Team ${new Date().toLocaleTimeString()}`,
      type: 'Agent Team',
      region: 'eu-west-1',
      status: 'Healthy',
      traffic: '100%',
      updated: 'Just now',
      config: { agents, coordination }
    };

    onDeploy(newDeployment);
    onLog({
      source: newDeployment.name,
      op: 'Team Initialization',
      status: 'Success',
      tokens: '0.8k',
      time: 'Just now'
    });
    alert('Team initialized and deployed!');
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-zinc-900 font-sans tracking-tight">Agent Orchestrator</h2>
          <p className="text-zinc-500 text-sm mt-1">Design multi-agent systems with specialized roles and tools.</p>
        </div>
        <button 
          onClick={handleInitialize}
          className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2"
        >
          <Users size={16} />
          Initialize Team
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-mono text-zinc-400 uppercase tracking-widest font-medium">Team Configuration</h3>
            <span className="text-xs text-zinc-400">{agents.length} Agents Active</span>
          </div>
          <div className="space-y-3">
            <AnimatePresence mode="popLayout">
              {agents.map((agent) => (
                <motion.div 
                  key={agent.id}
                  layout
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="p-4 bg-white border border-zinc-200 rounded-xl flex items-center justify-between hover:shadow-sm transition-shadow group"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-zinc-100 rounded-full flex items-center justify-center text-zinc-600 font-semibold">
                      {agent.name[0]}
                    </div>
                    <div>
                      <h4 className="font-medium text-zinc-900">{agent.name}</h4>
                      <p className="text-xs text-zinc-500">{agent.llm} • {agent.memory} memory</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1">
                      {agent.tools.map((t, j) => (
                        <span key={j} className="px-2 py-1 bg-zinc-50 border border-zinc-100 rounded text-[10px] font-mono text-zinc-500 uppercase">{t}</span>
                      ))}
                    </div>
                    <button 
                      onClick={() => removeAgent(agent.id)}
                      className="p-1.5 text-zinc-400 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            <button 
              onClick={addAgent}
              className="w-full py-3 border-2 border-dashed border-zinc-200 rounded-xl text-zinc-400 text-sm font-medium hover:border-zinc-400 hover:text-zinc-600 transition-all flex items-center justify-center gap-2"
            >
              <Plus size={16} />
              Add Agent Role
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-mono text-zinc-400 uppercase tracking-widest font-medium">Coordination Strategy</h3>
          <div className="p-6 bg-zinc-50 border border-zinc-200 rounded-2xl space-y-4">
            <button 
              onClick={() => setCoordination('hierarchical')}
              className={`w-full flex items-center justify-between p-4 border rounded-xl transition-all ${
                coordination === 'hierarchical' ? 'bg-white border-zinc-900 ring-1 ring-zinc-900' : 'bg-white border-zinc-200 opacity-60 hover:opacity-100'
              }`}
            >
              <div className="flex items-center gap-3">
                <Layers size={20} className={coordination === 'hierarchical' ? 'text-zinc-900' : 'text-zinc-400'} />
                <div className="text-left">
                  <h4 className="font-medium text-zinc-900">Hierarchical</h4>
                  <p className="text-xs text-zinc-500">Manager-worker pattern with oversight</p>
                </div>
              </div>
              {coordination === 'hierarchical' && (
                <div className="w-4 h-4 rounded-full bg-zinc-900 flex items-center justify-center">
                  <div className="w-1.5 h-1.5 rounded-full bg-white" />
                </div>
              )}
            </button>
            <button 
              onClick={() => setCoordination('swarm')}
              className={`w-full flex items-center justify-between p-4 border rounded-xl transition-all ${
                coordination === 'swarm' ? 'bg-white border-zinc-900 ring-1 ring-zinc-900' : 'bg-white border-zinc-200 opacity-60 hover:opacity-100'
              }`}
            >
              <div className="flex items-center gap-3">
                <Zap size={20} className={coordination === 'swarm' ? 'text-zinc-900' : 'text-zinc-400'} />
                <div className="text-left">
                  <h4 className="font-medium text-zinc-900">Swarm</h4>
                  <p className="text-xs text-zinc-500">Decentralized peer-to-peer execution</p>
                </div>
              </div>
              {coordination === 'swarm' && (
                <div className="w-4 h-4 rounded-full bg-zinc-900 flex items-center justify-center">
                  <div className="w-1.5 h-1.5 rounded-full bg-white" />
                </div>
              )}
            </button>
          </div>
          
          <div className="p-6 bg-white border border-zinc-200 rounded-2xl">
            <h4 className="text-sm font-semibold text-zinc-900 mb-3">Orchestration Preview</h4>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span>Researcher: Searching for "AI Market Trends 2026"...</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                <div className="w-2 h-2 rounded-full bg-zinc-300" />
                <span>Analyst: Waiting for data input...</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                <div className="w-2 h-2 rounded-full bg-zinc-300" />
                <span>Writer: Waiting for analysis...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const GovernanceHub = ({ lineage }: { lineage: LineageEntry[] }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="space-y-8"
  >
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-semibold text-zinc-900 font-sans tracking-tight">Governance & Cost</h2>
        <p className="text-zinc-500 text-sm mt-1">Monitor data lineage, compliance, and token expenditure.</p>
      </div>
      <div className="flex gap-2">
        <button className="px-4 py-2 border border-zinc-200 rounded-lg text-sm font-medium hover:bg-zinc-50 transition-colors">
          Export Audit
        </button>
        <button className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors">
          Set Quotas
        </button>
      </div>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[
        { label: 'Total Cost (MTD)', value: `$${(lineage.length * 0.15 + 1240.50).toFixed(2)}`, trend: 'up', change: '+12%', icon: <DollarSign size={20} /> },
        { label: 'Token Usage', value: `${(lineage.length * 0.1 + 4.2).toFixed(1)}M`, trend: 'down', change: '-5%', icon: <Activity size={20} /> },
        { label: 'PII Redactions', value: '842', trend: 'up', change: '+24%', icon: <Lock size={20} /> },
        { label: 'Compliance Score', value: '98%', trend: 'neutral', change: '0%', icon: <ShieldCheck size={20} /> },
      ].map((metric, i) => (
        <div key={i} className="p-6 bg-white border border-zinc-200 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-zinc-50 rounded-lg text-zinc-500">{metric.icon}</div>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              metric.trend === 'up' ? 'bg-red-50 text-red-600' : 
              metric.trend === 'down' ? 'bg-green-50 text-green-600' : 
              'bg-zinc-50 text-zinc-600'
            }`}>
              {metric.change}
            </span>
          </div>
          <p className="text-sm text-zinc-500 mb-1">{metric.label}</p>
          <h3 className="text-2xl font-bold text-zinc-900">{metric.value}</h3>
        </div>
      ))}
    </div>

    <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden">
      <div className="p-6 border-b border-zinc-100 flex items-center justify-between">
        <h3 className="font-semibold text-zinc-900">Recent Data Lineage</h3>
        <BarChart3 size={18} className="text-zinc-400" />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-50 text-zinc-500 font-mono text-[10px] uppercase tracking-widest">
            <tr>
              <th className="px-6 py-3 font-medium">Source</th>
              <th className="px-6 py-3 font-medium">Operation</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Tokens</th>
              <th className="px-6 py-3 font-medium">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {lineage.map((row, i) => (
              <tr key={i} className="hover:bg-zinc-50 transition-colors">
                <td className="px-6 py-4 font-medium text-zinc-900">{row.source}</td>
                <td className="px-6 py-4 text-zinc-500">{row.op}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-[10px] font-semibold ${
                    row.status === 'Success' ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'
                  }`}>
                    {row.status}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-zinc-500">{row.tokens}</td>
                <td className="px-6 py-4 text-zinc-400">{row.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </motion.div>
);

const Dashboard = ({ deployments }: { deployments: Deployment[] }) => {
  const ragCount = deployments.filter(d => d.type === 'RAG Pipeline').length;
  const agentCount = deployments.filter(d => d.type === 'Agent Team').length;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-zinc-900 font-sans tracking-tight">Enterprise Overview</h2>
          <p className="text-zinc-500 text-sm mt-1">High-level metrics across all AI core modules.</p>
        </div>
        <button className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors">
          Generate Report
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-white border border-zinc-200 rounded-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg"><Database size={20} /></div>
            <h3 className="font-semibold text-zinc-900">RAG Pipelines</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Active Pipelines</span>
              <span className="font-medium">{ragCount}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Total Documents</span>
              <span className="font-medium">{(ragCount * 100000).toLocaleString()}</span>
            </div>
            <div className="w-full bg-zinc-100 h-1.5 rounded-full mt-4">
              <div className="bg-blue-600 h-full rounded-full" style={{ width: `${Math.min(ragCount * 10, 100)}%` }} />
            </div>
          </div>
        </div>

        <div className="p-6 bg-white border border-zinc-200 rounded-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-50 text-purple-600 rounded-lg"><Users size={20} /></div>
            <h3 className="font-semibold text-zinc-900">Agent Teams</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Active Teams</span>
              <span className="font-medium">{agentCount}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Total Agents</span>
              <span className="font-medium">{agentCount * 4}</span>
            </div>
            <div className="w-full bg-zinc-100 h-1.5 rounded-full mt-4">
              <div className="bg-purple-600 h-full rounded-full" style={{ width: `${Math.min(agentCount * 20, 100)}%` }} />
            </div>
          </div>
        </div>

        <div className="p-6 bg-white border border-zinc-200 rounded-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-amber-50 text-amber-600 rounded-lg"><Zap size={20} /></div>
            <h3 className="font-semibold text-zinc-900">System Health</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Uptime</span>
              <span className="font-medium">99.98%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Avg Latency</span>
              <span className="font-medium">420ms</span>
            </div>
            <div className="w-full bg-zinc-100 h-1.5 rounded-full mt-4">
              <div className="bg-amber-600 h-full rounded-full w-[98%]" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="p-6 bg-white border border-zinc-200 rounded-2xl">
          <h3 className="font-semibold text-zinc-900 mb-6">Cost Distribution</h3>
          <div className="space-y-4">
            {[
              { label: 'RAG Inference', value: 45, color: 'bg-blue-500' },
              { label: 'Agent Execution', value: 30, color: 'bg-purple-500' },
              { label: 'Vector Storage', value: 15, color: 'bg-zinc-500' },
              { label: 'Other', value: 10, color: 'bg-zinc-200' },
            ].map((item, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-500">{item.label}</span>
                  <span className="font-medium">{item.value}%</span>
                </div>
                <div className="w-full bg-zinc-100 h-2 rounded-full">
                  <div className={`${item.color} h-full rounded-full`} style={{ width: `${item.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 bg-white border border-zinc-200 rounded-2xl">
          <h3 className="font-semibold text-zinc-900 mb-6">Recent Activity</h3>
          <div className="space-y-4">
            {deployments.slice(0, 4).map((item, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold ${item.type === 'RAG Pipeline' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'}`}>
                  {item.name.substring(0, 2).toUpperCase()}
                </div>
                <div className="flex-1">
                  <p className="text-sm text-zinc-900">
                    <span className="font-medium">{item.name}</span> deployed successfully
                  </p>
                  <p className="text-[10px] text-zinc-400">{item.updated}</p>
                </div>
              </div>
            ))}
            {deployments.length === 0 && (
              <p className="text-sm text-zinc-500 text-center py-4">No recent activity</p>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const Deployments = ({ deployments }: { deployments: Deployment[] }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="space-y-8"
  >
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-semibold text-zinc-900 font-sans tracking-tight">Active Deployments</h2>
        <p className="text-zinc-500 text-sm mt-1">Manage and monitor your production AI services.</p>
      </div>
      <button className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2">
        <Plus size={16} />
        New Deployment
      </button>
    </div>

    <div className="space-y-4">
      {deployments.map((dep, i) => (
        <div key={i} className="p-6 bg-white border border-zinc-200 rounded-xl flex items-center justify-between hover:border-zinc-400 transition-all group">
          <div className="flex items-center gap-6">
            <div className={`p-3 rounded-xl ${dep.type === 'RAG Pipeline' ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'}`}>
              {dep.type === 'RAG Pipeline' ? <Database size={24} /> : <Users size={24} />}
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900">{dep.name}</h3>
              <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                <span className="flex items-center gap-1"><Globe size={12} /> {dep.region}</span>
                <span>•</span>
                <span>{dep.type}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-12">
            <div className="text-right">
              <p className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest mb-1">Traffic</p>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-zinc-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-zinc-900 h-full" style={{ width: dep.traffic }} />
                </div>
                <span className="text-xs font-medium text-zinc-900">{dep.traffic}</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest mb-1">Status</p>
              <span className={`px-2 py-1 rounded-full text-[10px] font-semibold ${
                dep.status === 'Healthy' ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'
              }`}>
                {dep.status}
              </span>
            </div>
            <button className="p-2 text-zinc-400 hover:text-zinc-900 transition-colors">
              <Settings size={18} />
            </button>
          </div>
        </div>
      ))}
      {deployments.length === 0 && (
        <div className="text-center py-12 bg-zinc-50 border border-dashed border-zinc-200 rounded-xl">
          <p className="text-zinc-500">No active deployments found. Create one in RAG Designer or Agent Orchestrator.</p>
        </div>
      )}
    </div>
  </motion.div>
);

const PromptLab = () => {
  const [technique, setTechnique] = useState('Chain of Thought');
  const [systemPrompt, setSystemPrompt] = useState('You are a senior financial analyst. Use the provided context to answer questions with extreme precision. Think step-by-step.');
  const [userPrompt, setUserPrompt] = useState('What are the key risks mentioned in the Q4 report?');
  const [result, setResult] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runTest = async () => {
    setIsLoading(true);
    setError(null);
    setResult('');
    try {
      const response = await genAI.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `System: ${systemPrompt}\nTechnique: ${technique}\nUser: ${userPrompt}`,
      });
      setResult(response.text || 'No response generated.');
    } catch (err) {
      console.error(err);
      setError('Failed to generate response. Please check your API key.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-zinc-900 font-sans tracking-tight">Prompt Lab</h2>
          <p className="text-zinc-500 text-sm mt-1">Experiment with 15+ advanced prompt engineering techniques.</p>
        </div>
        <button className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2">
          <Box size={16} />
          Save Template
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 space-y-4">
          <h3 className="text-sm font-mono text-zinc-400 uppercase tracking-widest font-medium">Techniques</h3>
          <div className="space-y-1">
            {[
              'Zero-Shot', 'Few-Shot', 'Chain of Thought', 'Self-Consistency', 
              'Tree of Thoughts', 'ReAct', 'Reflexion', 'Plan-and-Solve'
            ].map((t, i) => (
              <button 
                key={i} 
                onClick={() => setTechnique(t)}
                className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-all ${
                  technique === t ? 'bg-zinc-900 text-white font-medium' : 'text-zinc-600 hover:bg-zinc-100'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3 space-y-6">
          <div className="space-y-4">
            <label className="text-sm font-medium text-zinc-900">System Instruction</label>
            <textarea 
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="w-full h-24 p-4 bg-white border border-zinc-200 rounded-xl text-sm focus:ring-2 focus:ring-zinc-900 outline-none transition-all resize-none"
            />
          </div>
          <div className="space-y-4">
            <label className="text-sm font-medium text-zinc-900">User Query</label>
            <textarea 
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className="w-full h-24 p-4 bg-white border border-zinc-200 rounded-xl text-sm focus:ring-2 focus:ring-zinc-900 outline-none transition-all resize-none"
            />
          </div>
          
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <Activity size={14} />
              <span>Technique: {technique}</span>
            </div>
            <div className="flex gap-3">
              <button className="px-6 py-2 border border-zinc-200 rounded-lg text-sm font-medium hover:bg-zinc-50 transition-colors">
                Optimize
              </button>
              <button 
                onClick={runTest}
                disabled={isLoading}
                className="px-6 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                {isLoading ? 'Running...' : 'Run Test'}
              </button>
            </div>
          </div>

          <AnimatePresence>
            {(result || error) && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className={`p-6 rounded-2xl border ${error ? 'bg-red-50 border-red-100 text-red-900' : 'bg-zinc-50 border-zinc-200 text-zinc-900'}`}
              >
                <div className="flex items-center gap-2 mb-3">
                  {error ? <AlertCircle size={18} /> : <Terminal size={18} className="text-zinc-400" />}
                  <h4 className="font-semibold text-sm">{error ? 'Error' : 'Model Output'}</h4>
                </div>
                <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
                  {error || result}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

export default function App() {
  const [activeModule, setActiveModule] = useState<ModuleType>('dashboard');
  const [deployments, setDeployments] = useState<Deployment[]>([
    { id: '1', name: 'Finance RAG v2.1', type: 'RAG Pipeline', region: 'us-east-1', status: 'Healthy', traffic: '45%', updated: '2h ago' },
    { id: '2', name: 'Customer Support Swarm', type: 'Agent Team', region: 'eu-west-1', status: 'Healthy', traffic: '100%', updated: '1d ago' },
    { id: '3', name: 'Legal Doc Analyzer', type: 'RAG Pipeline', region: 'us-west-2', status: 'Warning', traffic: '10%', updated: '15m ago' },
  ]);
  const [lineage, setLineage] = useState<LineageEntry[]>([
    { source: 'finance_report_q4.pdf', op: 'Ingestion', status: 'Success', tokens: '42k', time: '2m ago' },
    { source: 'customer_query_882', op: 'RAG Query', status: 'Success', tokens: '1.2k', time: '15m ago' },
    { source: 'internal_wiki_v2', op: 'Embedding', status: 'Processing', tokens: '120k', time: 'Just now' },
  ]);

  const addDeployment = (dep: Deployment) => setDeployments(prev => [dep, ...prev]);
  const addLineage = (entry: LineageEntry) => setLineage(prev => [entry, ...prev]);

  const navItems = [
    { id: 'rag', label: 'RAG Designer', icon: <Database size={18} /> },
    { id: 'agents', label: 'Agent Orchestrator', icon: <Users size={18} /> },
    { id: 'prompts', label: 'Prompt Lab', icon: <Terminal size={18} /> },
    { id: 'governance', label: 'Governance Hub', icon: <ShieldCheck size={18} /> },
  ];

  const platformItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'deployments', label: 'Deployments', icon: <Globe size={18} /> },
    { id: 'settings', label: 'Settings', icon: <Settings size={18} /> },
  ];

  return (
    <div className="flex h-screen bg-zinc-50 text-zinc-900 font-sans selection:bg-zinc-900 selection:text-white">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-zinc-200 flex flex-col">
        <div className="p-6 border-b border-zinc-100">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center text-white">
              <Cpu size={18} />
            </div>
            <h1 className="font-bold text-lg tracking-tight">AI Core</h1>
          </div>
          <p className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">Enterprise Shared Library</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <div className="mb-4">
            <p className="px-4 text-[10px] font-mono text-zinc-400 uppercase tracking-widest mb-2">Modules</p>
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveModule(item.id as ModuleType)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm transition-all ${
                  activeModule === item.id 
                    ? 'bg-zinc-900 text-white font-medium shadow-lg shadow-zinc-200' 
                    : 'text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900'
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </div>

          <div>
            <p className="px-4 text-[10px] font-mono text-zinc-400 uppercase tracking-widest mb-2">Platform</p>
            {platformItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  if (item.id !== 'settings') {
                    setActiveModule(item.id as ModuleType);
                  }
                }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm transition-all ${
                  activeModule === item.id 
                    ? 'bg-zinc-900 text-white font-medium shadow-lg shadow-zinc-200' 
                    : 'text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900'
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </div>
        </nav>

        <div className="p-4 border-t border-zinc-100">
          <div className="p-4 bg-zinc-50 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">System Status</span>
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            </div>
            <p className="text-xs font-medium text-zinc-900">All systems operational</p>
            <p className="text-[10px] text-zinc-500 mt-1">v2.0.0 Stable</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-zinc-200 px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <span>Library</span>
            <ChevronRight size={14} />
            <span className="text-zinc-900 font-medium">
              {[...navItems, ...platformItems].find(n => n.id === activeModule)?.label}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input 
                type="text" 
                placeholder="Search modules..." 
                className="pl-10 pr-4 py-1.5 bg-zinc-50 border border-zinc-200 rounded-lg text-sm focus:ring-2 focus:ring-zinc-900 outline-none transition-all w-64"
              />
            </div>
            <div className="w-8 h-8 bg-zinc-100 rounded-full flex items-center justify-center border border-zinc-200">
              <HelpCircle size={16} className="text-zinc-500" />
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-6xl mx-auto">
            <AnimatePresence mode="wait">
              {activeModule === 'dashboard' && <Dashboard deployments={deployments} />}
              {activeModule === 'rag' && <RAGDesigner onDeploy={addDeployment} onLog={addLineage} />}
              {activeModule === 'agents' && <AgentOrchestrator onDeploy={addDeployment} onLog={addLineage} />}
              {activeModule === 'governance' && <GovernanceHub lineage={lineage} />}
              {activeModule === 'prompts' && <PromptLab />}
              {activeModule === 'deployments' && <Deployments deployments={deployments} />}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}

