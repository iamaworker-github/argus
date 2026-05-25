export type AgentStatus = 'Running' | 'Queued' | 'Complete' | 'Failed' | 'Paused';
export type OperationMode = 'PENTEST' | 'RECON' | 'OSINT' | 'EXPLOIT' | 'AUDIT';

export interface Agent {
  id: string;
  name: string;
  icon: string;
  status: AgentStatus;
  color: string;
}

export interface PipelineStage {
  name: string;
  completed: number;
  total: number;
  active: boolean;
}

export interface LogLine {
  id: number;
  text: string;
  type: 'cmd' | 'output' | 'info' | 'success' | 'warn';
  timestamp?: string;
}

export interface ActivityEntry {
  time: string;
  agent: string;
  message: string;
}

export interface Finding {
  text: string;
  title?: string;
  description?: string;
  severity?: string;
  category?: string;
  evidence?: string;
  confidence?: number;
  cvss_score?: number | null;
  cwe_id?: string | null;
  remediation?: string | null;
  agent_name?: string;
}

export interface Technology {
  name: string;
  icon: string;
  percent: number;
}

export interface Discovery {
  name: string;
  time: string;
}

export interface GraphNode {
  id: string;
  label: string;
  sublabel?: string;
  x: number;
  y: number;
  type: 'host' | 'service' | 'application' | 'datastore' | 'external';
  color: string;
}

export interface GraphEdge {
  from: string;
  to: string;
}

export interface SystemState {
  cpu: number;
  mem: number;
  net: number;
  tokens: number;
  maxTokens: number;
  credits: number;
  uptime: string;
  sessionId: string;
  time: string;
  target: string;
  mode: OperationMode;
  agentStatus: 'EXECUTING' | 'IDLE' | 'PLANNING';
  riskProfile: string;
  maxParallel: string;
  safeMode: boolean;
  agents: Agent[];
  pipeline: PipelineStage[];
  logs: LogLine[];
  thinkingLines: string[];
  activities: ActivityEntry[];
  findings: Finding[];
  technologies: Technology[];
  discoveries: Discovery[];
  nodes: GraphNode[];
  edges: GraphEdge[];
  riskScore: number;
  riskLabel: string;
  targetIP: string;
  openPorts: number;
  subdomains: number;
  technologies_count: number;
  attackSurface: string;
  commandsExecuted: number;
  dataCollected: string;
  findingsCount: number;
  vulnerabilities: number;
  memoryPercent: number;
  knowledgeBase: string;
  activeAgentName: string;
  activeAgentTime: string;
  tokensUsed: string;
}
