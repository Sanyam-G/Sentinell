import { useState } from 'react';
import IncidentConsole from './components/IncidentConsole';
import ToolCallMonitor from './components/ToolCallMonitor';
import SlackViewer from './components/SlackViewer';
import CodeViewer from './components/CodeViewer';
import AgentStatePanel from './components/AgentStatePanel';
import {
  mockIncident,
  mockAgentSteps,
  mockToolCalls,
  mockSlackMessages,
  mockCodeFiles,
  mockAgentState,
} from './data/mockData';

function App() {
  const [isRunning, setIsRunning] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-cyan-500/20 bg-slate-900/50 backdrop-blur-sm">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-xl">S</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Sentinel</h1>
                <p className="text-sm text-cyan-400/70">Real-time incident monitoring & resolution</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm">
                {isRunning ? '● Active' : '○ Idle'}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Sidebar - Agent State */}
        <div className="w-80 border-r border-cyan-500/20 bg-slate-900/30 backdrop-blur-sm">
          <AgentStatePanel state={mockAgentState} />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Section - Incident Console */}
          <div className="flex-1 overflow-auto">
            <IncidentConsole
              incident={mockIncident}
              steps={mockAgentSteps}
              onStart={() => setIsRunning(true)}
              isRunning={isRunning}
            />
          </div>

          {/* Bottom Section - Tool Calls */}
          <div className="h-64 border-t border-cyan-500/20">
            <ToolCallMonitor toolCalls={mockToolCalls} />
          </div>
        </div>

        {/* Right Sidebar - Context */}
        <div className="w-96 border-l border-cyan-500/20 bg-slate-900/30 backdrop-blur-sm flex flex-col">
          <div className="flex-1 border-b border-cyan-500/20 overflow-auto">
            <SlackViewer messages={mockSlackMessages} />
          </div>
          <div className="flex-1 overflow-auto">
            <CodeViewer files={mockCodeFiles} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
