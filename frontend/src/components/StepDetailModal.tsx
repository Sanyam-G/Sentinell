import { AgentStep } from '../types';
import { highlightPython } from '../utils/syntaxHighlight';

interface StepDetailModalProps {
  step: AgentStep;
  onClose: () => void;
}

export default function StepDetailModal({ step, onClose }: StepDetailModalProps) {
  // Mock detailed content based on step type
  const getDetailedContent = () => {
    switch (step.type) {
      case 'search_slack':
        return {
          title: 'Slack Search Results',
          content: (
            <div className="space-y-4">
              <div className="text-sm text-slate-400">
                Searched channels: #prod-alerts, #infra-debug
              </div>
              <div className="space-y-3">
                <div className="bg-slate-900/50 border border-slate-700 rounded p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-5 h-5 rounded bg-slate-700 flex items-center justify-center text-white text-xs">A</div>
                    <span className="text-xs text-slate-400">alert-bot</span>
                    <span className="text-xs text-slate-600">3:42 PM</span>
                  </div>
                  <p className="text-sm text-slate-300">🚨 Worker-17 CPU utilization at 95% for 5 minutes</p>
                  <div className="mt-2 text-xs text-cyan-400">Relevance: 95%</div>
                </div>
                <div className="bg-slate-900/50 border border-slate-700 rounded p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-5 h-5 rounded bg-slate-700 flex items-center justify-center text-white text-xs">M</div>
                    <span className="text-xs text-slate-400">mike.rodriguez</span>
                    <span className="text-xs text-slate-600">3:48 PM</span>
                  </div>
                  <p className="text-sm text-slate-300">Worker-17 seems to be stuck in a loop processing the same tasks</p>
                  <div className="mt-2 text-xs text-cyan-400">Relevance: 88%</div>
                </div>
                <div className="bg-slate-900/50 border border-slate-700 rounded p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-5 h-5 rounded bg-slate-700 flex items-center justify-center text-white text-xs">S</div>
                    <span className="text-xs text-slate-400">sarah.chen</span>
                    <span className="text-xs text-slate-600">3:45 PM</span>
                  </div>
                  <p className="text-sm text-slate-300">Seeing increased latency on the worker pool. Investigating...</p>
                  <div className="mt-2 text-xs text-cyan-400">Relevance: 82%</div>
                </div>
              </div>
            </div>
          ),
        };

      case 'read_file':
        const codeSnippet = `def process_queue(self):
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
            continue`;

        return {
          title: 'Code Analysis',
          content: (
            <div className="space-y-4">
              <div className="text-sm text-slate-400">
                Analyzed: services/worker.py (lines 45-89)
              </div>
              <div className="bg-slate-900/50 border border-slate-700 rounded p-4">
                <div className="text-xs text-slate-500 mb-3">Identified Issue:</div>
                <pre className="text-xs leading-6">
                  {codeSnippet.split('\n').map((line, idx) => (
                    <div key={idx}>
                      <code dangerouslySetInnerHTML={{ __html: highlightPython(line) }} />
                    </div>
                  ))}
                </pre>
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded">
                  <div className="text-xs text-red-400">
                    ⚠ Missing exponential backoff in error handling loop
                  </div>
                </div>
              </div>
            </div>
          ),
        };

      case 'analyze':
        return {
          title: 'Root Cause Analysis',
          content: (
            <div className="space-y-4">
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-slate-500 mb-2">Problem:</div>
                  <p className="text-sm text-slate-300">
                    Queue processing loop lacks backoff strategy, causing continuous retries on failures.
                    This leads to CPU saturation when tasks repeatedly fail.
                  </p>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-2">Evidence:</div>
                  <ul className="text-sm text-slate-400 space-y-1">
                    <li>• CPU utilization: 95% sustained</li>
                    <li>• Error logs: 247 "Queue processing timeout" errors in 1 hour</li>
                    <li>• Service latency: +400ms increase</li>
                  </ul>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-2">Impact:</div>
                  <p className="text-sm text-slate-300">
                    Worker-17 is unable to process new tasks effectively, causing cascading delays
                    across the entire worker pool.
                  </p>
                </div>
              </div>
            </div>
          ),
        };

      default:
        return {
          title: step.title,
          content: (
            <div className="text-sm text-slate-400">
              {step.details}
            </div>
          ),
        };
    }
  };

  const detailContent = getDetailedContent();

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-slate-900 border border-slate-700 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
          <h3 className="text-lg font-medium text-white">{detailContent.title}</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>
        <div className="p-6">
          {detailContent.content}
        </div>
      </div>
    </div>
  );
}
