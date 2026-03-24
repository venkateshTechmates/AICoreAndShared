export type ModuleType = 'rag' | 'agents' | 'governance' | 'prompts' | 'dashboard' | 'deployments';

export interface Deployment {
  id: string;
  name: string;
  type: 'RAG Pipeline' | 'Agent Team';
  region: string;
  status: 'Healthy' | 'Warning' | 'Error' | 'Processing';
  traffic: string;
  updated: string;
  config?: any;
}

export interface RAGConfig {
  ingestion: string;
  chunking: string;
  embedding: string;
  vectorStore: string;
  search: string;
  llm: string;
}

export interface AgentRole {
  id: string;
  name: string;
  tools: string[];
  llm: string;
  memory: string;
}

export interface AgentTeam {
  id: string;
  name: string;
  agents: AgentRole[];
  coordination: 'hierarchical' | 'sequential' | 'swarm';
}

export interface Metric {
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  change?: string;
}

export interface LineageEntry {
  source: string;
  op: string;
  status: 'Success' | 'Processing' | 'Error';
  tokens: string;
  time: string;
}
