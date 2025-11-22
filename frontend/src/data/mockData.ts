import { AgentStep, ToolCall, SlackMessage, CodeFile, AgentState, Incident } from '../types';

export const mockIncident: Incident = {
  id: '1',
  title: 'CPU spike on Worker-17',
  description: 'Worker-17 experiencing 95% CPU utilization. Service latency increased by 400ms.',
  status: 'active',
  timestamp: Date.now() - 300000,
};

export const mockAgentSteps: AgentStep[] = [
  {
    id: '1',
    timestamp: Date.now() - 180000,
    type: 'search_slack',
    title: 'Search Slack Channels',
    description: 'Searching #prod-alerts and #infra-debug for related incidents',
    status: 'completed',
    details: 'Found 3 relevant messages mentioning Worker-17 CPU issues',
  },
  {
    id: '2',
    timestamp: Date.now() - 120000,
    type: 'read_file',
    title: 'Analyze Worker Code',
    description: 'Reading worker.py and related configuration files',
    status: 'completed',
    details: 'Identified potential infinite loop in process_queue() function',
  },
  {
    id: '3',
    timestamp: Date.now() - 60000,
    type: 'analyze',
    title: 'Root Cause Analysis',
    description: 'Analyzing metrics, logs, and code patterns',
    status: 'completed',
    details: 'RCA: Queue processing not implementing backoff strategy',
  },
  {
    id: '4',
    timestamp: Date.now() - 30000,
    type: 'generate_plan',
    title: 'Generate Remediation Plan',
    description: 'Creating step-by-step remediation strategy',
    status: 'in_progress',
  },
];

export const mockToolCalls: ToolCall[] = [
  {
    id: '1',
    timestamp: Date.now() - 180000,
    toolName: 'search_slack',
    arguments: {
      channels: ['#prod-alerts', '#infra-debug'],
      query: 'Worker-17 CPU',
      timeRange: '24h',
    },
    response: {
      messagesFound: 3,
      relevantChannels: ['#prod-alerts'],
    },
    duration: 1200,
  },
  {
    id: '2',
    timestamp: Date.now() - 150000,
    toolName: 'get_metrics',
    arguments: {
      service: 'Worker-17',
      metrics: ['cpu', 'memory', 'latency'],
      duration: '1h',
    },
    response: {
      cpu: { average: 94.5, peak: 98.2 },
      memory: { average: 62.1, peak: 68.9 },
      latency: { p50: 450, p95: 890, p99: 1200 },
    },
    duration: 850,
  },
  {
    id: '3',
    timestamp: Date.now() - 120000,
    toolName: 'read_file',
    arguments: {
      path: 'services/worker.py',
      lines: '45-89',
    },
    response: {
      content: 'def process_queue():\\n    while True:\\n        task = queue.get()\\n        ...',
      linesRead: 44,
    },
    duration: 320,
  },
  {
    id: '4',
    timestamp: Date.now() - 90000,
    toolName: 'search_logs',
    arguments: {
      service: 'Worker-17',
      level: 'ERROR',
      timeRange: '1h',
    },
    response: {
      errorCount: 247,
      topErrors: [
        'Queue processing timeout',
        'Task execution failed',
      ],
    },
    duration: 2100,
  },
];

export const mockSlackMessages: SlackMessage[] = [
  {
    id: '1',
    channel: '#prod-alerts',
    user: 'alert-bot',
    timestamp: Date.now() - 240000,
    text: '🚨 Worker-17 CPU utilization at 95% for 5 minutes',
    isRetrieved: true,
    relevanceScore: 0.95,
  },
  {
    id: '2',
    channel: '#prod-alerts',
    user: 'sarah.chen',
    timestamp: Date.now() - 200000,
    text: 'Seeing increased latency on the worker pool. Investigating...',
    isRetrieved: true,
    relevanceScore: 0.82,
  },
  {
    id: '3',
    channel: '#infra-debug',
    user: 'mike.rodriguez',
    timestamp: Date.now() - 180000,
    text: 'Worker-17 seems to be stuck in a loop processing the same tasks',
    isRetrieved: true,
    relevanceScore: 0.88,
  },
  {
    id: '4',
    channel: '#prod-alerts',
    user: 'john.doe',
    timestamp: Date.now() - 120000,
    text: 'Anyone else seeing issues with the queue system?',
    isRetrieved: false,
  },
];

export const mockCodeFiles: CodeFile[] = [
  {
    path: 'services/worker.py',
    language: 'python',
    content: `import queue
import time
from logger import log

class Worker:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.queue = queue.Queue()

    def process_queue(self):
        """Process tasks from the queue"""
        while True:
            try:
                task = self.queue.get(timeout=1)
                self.execute_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                log.error(f"Task failed: {e}")
                # BUG: No backoff strategy here
                continue

    def execute_task(self, task):
        """Execute a single task"""
        log.info(f"Processing task: {task['id']}")
        # Task processing logic
        time.sleep(0.1)`,
    highlightedLines: [15, 16, 17, 18, 19, 20],
  },
];

export const mockAgentState: AgentState = {
  currentNode: 'generate_plan',
  pastNodes: ['initialize', 'search_slack', 'read_code', 'analyze'],
  loopIteration: 1,
  memory: {
    retrievedContext: [
      'Slack: 3 messages about Worker-17 CPU spike',
      'Code: worker.py lines 45-89 (process_queue function)',
      'Metrics: CPU at 94.5% avg, latency increased 400ms',
    ],
    pastActions: [
      'Searched Slack channels',
      'Retrieved metrics from monitoring',
      'Analyzed worker.py code',
      'Identified missing backoff strategy',
    ],
  },
};

export const mockReasoningStream = [
  { type: 'thought', content: 'Analyzing the incident: Worker-17 CPU spike...' },
  { type: 'action', content: 'Searching Slack for related incidents...' },
  { type: 'observation', content: 'Found 3 relevant messages in #prod-alerts' },
  { type: 'thought', content: 'Team already noticed the issue. Need to check code...' },
  { type: 'action', content: 'Reading worker.py to identify the root cause...' },
  { type: 'observation', content: 'Found process_queue() function without backoff strategy' },
  { type: 'thought', content: 'This explains the CPU spike. Generating remediation plan...' },
];

// Metrics data for sparklines (last 20 data points)
export const mockMetrics = {
  cpu: [45, 48, 52, 55, 58, 62, 68, 72, 78, 82, 85, 88, 90, 92, 94, 95, 96, 95, 95, 94],
  memory: [55, 56, 57, 58, 59, 60, 61, 62, 62, 63, 63, 64, 65, 66, 67, 68, 68, 69, 68, 67],
  latency: [120, 125, 130, 140, 150, 180, 220, 280, 320, 380, 420, 450, 480, 500, 520, 510, 505, 500, 495, 490],
};
