import { useState } from 'react';
import { SectionHeader, CodeBlock } from '../components/ui';

const PlaygroundPage = () => {
  const [view, setView] = useState<'rag' | 'prompt'>('rag');
  return (
    <div className="space-y-8">
      <SectionHeader badge="Interactive" title="Playground — Try It Live" subtitle="Interactive RAG pipeline designer and prompt engineering lab." />
      <div className="flex gap-2">
        <button onClick={() => setView('rag')} className={'px-4 py-2 rounded-lg text-sm font-medium transition-colors ' + (view === 'rag' ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200')}>RAG Pipeline Designer</button>
        <button onClick={() => setView('prompt')} className={'px-4 py-2 rounded-lg text-sm font-medium transition-colors ' + (view === 'prompt' ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200')}>Prompt Lab</button>
      </div>
      {view === 'rag' ? <RAGDesigner /> : <PromptLab />}
    </div>
  );
};

// ── RAG Designer ──────────────────────────────────────────────
const RAGDesigner = () => {
  const [selectedStep, setSelectedStep] = useState(0);
  const steps = [
    { step: '01', title: 'Ingestion', desc: 'PDF, CSV, JSON, Web, SQL', details: 'Configure connectors for document sources with auto-sync.' },
    { step: '02', title: 'Chunking', desc: 'Semantic, Recursive, Fixed', details: 'Semantic boundary detection with 512 token window.' },
    { step: '03', title: 'Embedding', desc: 'OpenAI, Cohere, HuggingFace', details: 'text-embedding-3-large with 3072 dimensions.' },
    { step: '04', title: 'Vector Store', desc: 'Qdrant, Pinecone, Weaviate', details: 'Qdrant cluster with HNSW indexing enabled.' },
    { step: '05', title: 'Search', desc: 'Hybrid, MMR, Reranking', details: 'Hybrid search (Alpha: 0.5) with Cohere reranker.' },
    { step: '06', title: 'Generation', desc: 'GPT-4o, Claude 3, Llama 3', details: 'GPT-4o with Chain-of-Thought prompting.' },
  ];
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {steps.map((item, i) => (
          <div key={i} onClick={() => setSelectedStep(i)} className={'p-5 bg-white border rounded-xl cursor-pointer transition-all ' + (selectedStep === i ? 'border-zinc-900 ring-1 ring-zinc-900' : 'border-zinc-200 hover:border-zinc-400')}>
            <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">{item.step}</span>
            <h4 className="font-semibold text-zinc-900 mt-1">{item.title}</h4>
            <p className="text-xs text-zinc-500 mt-1">{item.desc}</p>
          </div>
        ))}
      </div>
      <div className="p-6 bg-zinc-50 border border-zinc-200 rounded-xl">
        <h4 className="font-semibold text-zinc-900 mb-2">{steps[selectedStep].title} Configuration</h4>
        <p className="text-sm text-zinc-600">{steps[selectedStep].details}</p>
      </div>
      <CodeBlock code={'from ai_core import AICore\n\nai = AICore.from_yaml(\"config.yml\")\n\nawait ai.ingest(documents=[\"docs/report.pdf\"], chunking=\"semantic\", namespace=\"finance\")\n\nresponse = await ai.query(\n    query=\"What were the Q4 revenue drivers?\",\n    search_strategy=\"hybrid\",\n    prompt_technique=\"chain_of_thought\",\n)\nprint(response.answer)\nprint(response.citations)'} />
    </div>
  );
};

// ── Prompt Lab ────────────────────────────────────────────────
const PromptLab = () => {
  const [technique, setTechnique] = useState('chain_of_thought');
  const techniques = [
    { key: 'chain_of_thought', label: 'Chain of Thought', desc: 'Step-by-step reasoning for complex problems' },
    { key: 'few_shot', label: 'Few-Shot', desc: 'Provide examples for consistent formatting' },
    { key: 'react', label: 'ReAct', desc: 'Reason + Act: multi-step agent prompts' },
    { key: 'tree_of_thought', label: 'Tree of Thought', desc: 'Explore multiple reasoning branches' },
    { key: 'self_consistency', label: 'Self-Consistency', desc: 'Sample multiple paths and aggregate' },
    { key: 'role_based', label: 'Role Prompting', desc: 'Set expert persona for the model' },
    { key: 'meta', label: 'Meta Prompting', desc: 'Prompt that generates optimized prompts' },
    { key: 'rag_fusion', label: 'RAG Fusion', desc: 'Multi-query retrieval with reciprocal rank fusion' },
  ];
  const selectedTech = techniques.find(t => t.key === technique)!;
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {techniques.map(t => (
          <button key={t.key} onClick={() => setTechnique(t.key)} className={'px-3 py-1.5 rounded-full text-xs font-medium transition-all ' + (technique === t.key ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200')}>{t.label}</button>
        ))}
      </div>
      <div className="p-6 bg-zinc-50 border border-zinc-200 rounded-xl space-y-4">
        <h4 className="font-semibold text-zinc-900">{selectedTech.label}</h4>
        <p className="text-sm text-zinc-600">{selectedTech.desc}</p>
        <div className="space-y-3">
          <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider">System Prompt</label>
          <textarea readOnly className="w-full h-24 text-sm p-3 bg-white border border-zinc-200 rounded-lg font-mono resize-none" value={'You are a senior data analyst. Use ' + selectedTech.label + ' to analyze the context and provide structured answers.'} />
          <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider">User Query</label>
          <textarea readOnly className="w-full h-16 text-sm p-3 bg-white border border-zinc-200 rounded-lg font-mono resize-none" value="What were the key revenue drivers in Q4? Provide a breakdown by business unit." />
        </div>
      </div>
      <CodeBlock code={'from ai_core.prompt_engine import PromptEngine\n\nengine = PromptEngine()\n\nprompt = engine.build(\n    technique=\"' + technique + '\",\n    system=\"Senior data analyst persona\",\n    query=\"Q4 revenue drivers analysis\",\n    context=retrieved_chunks,\n)\n\nresult = await engine.execute(prompt, model=\"gpt-4o\")\nprint(result.answer)\nprint(f\"Tokens: {result.usage.total_tokens}\")'} />
    </div>
  );
};

export default PlaygroundPage;
