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

export type CoordinationMode = 'sequential' | 'parallel' | 'debate' | 'hierarchical' | 'swarm' | 'supervisor';

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
  coordination: CoordinationMode;
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

export interface DomainExample {
  id: string;
  domain: string;
  title: string;
  description: string;
  mode: CoordinationMode;
  compliance: string[];
  agents: string[];
  file: string;
  color: string;
  icon: string;
}
