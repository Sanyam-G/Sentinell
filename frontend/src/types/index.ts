export interface AgentStep {
  id: string;
  timestamp: number;
  type: 'search_slack' | 'read_file' | 'analyze' | 'generate_plan' | 'execute_tool';
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  details?: string;
}

export interface ToolCall {
  id: string;
  timestamp: number;
  toolName: string;
  arguments: Record<string, any>;
  response: any;
  duration?: number;
}

export interface SlackMessage {
  id: string;
  channel: string;
  user: string;
  timestamp: number;
  text: string;
  isRetrieved: boolean;
  relevanceScore?: number;
}

export interface CodeFile {
  path: string;
  content: string;
  language: string;
  highlightedLines?: number[];
}

export interface AgentState {
  currentNode: string;
  pastNodes: string[];
  loopIteration: number;
  memory: {
    retrievedContext: string[];
    pastActions: string[];
  };
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  status: 'active' | 'investigating' | 'resolved';
  timestamp: number;
}
