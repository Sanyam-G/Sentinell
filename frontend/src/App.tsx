import { useState } from 'react';
import IncidentConsole from './components/IncidentConsole';
import ToolCallMonitor from './components/ToolCallMonitor';
import SlackViewer from './components/SlackViewer';
import CodeViewer from './components/CodeViewer';
import AgentStatePanel from './components/AgentStatePanel';
import ReasoningStream from './components/ReasoningStream';
import {
  mockIncident,
  mockAgentSteps,
  mockToolCalls,
  mockSlackMessages,
  mockCodeFiles,
  mockAgentState,
  mockReasoningStream,
} from './data/mockData';

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<'reasoning' | 'slack' | 'code' | 'tools'>('reasoning');

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Minimal Header */}
      <header className="border-b border-slate-800">
        <div className="px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded bg-cyan-500/20 flex items-center justify-center">
                <span className="text-cyan-400 font-bold">S</span>
              </div>
              <h1 className="text-lg font-medium text-white">Sentinel</h1>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500">Iteration {mockAgentState.loopIteration}</span>
              <div className={`h-2 w-2 rounded-full ${isRunning ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`}></div>
            </div>
          </div>
        </div>
      </header>

      {/* Simplified Layout */}
      <div className="flex h-[calc(100vh-65px)]">
        {/* Main Content - 2/3 width */}
        <div className="flex-1 overflow-auto">
          <IncidentConsole
            incident={mockIncident}
            steps={mockAgentSteps}
            onStart={() => setIsRunning(true)}
            isRunning={isRunning}
          />
        </div>

        {/* Right Sidebar - 1/3 width with tabs */}
        <div className="w-[500px] border-l border-slate-800 flex flex-col">
          {/* Tabs */}
          <div className="flex border-b border-slate-800 bg-slate-900/50">
            <button
              onClick={() => setActiveTab('reasoning')}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'reasoning'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              Reasoning
            </button>
            <button
              onClick={() => setActiveTab('slack')}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'slack'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              Context
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'code'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              Code
            </button>
            <button
              onClick={() => setActiveTab('tools')}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'tools'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              Tools
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'reasoning' && (
              <div className="h-full overflow-auto scrollbar-thin p-6">
                <ReasoningStream steps={mockReasoningStream} />
              </div>
            )}
            {activeTab === 'slack' && <SlackViewer messages={mockSlackMessages} />}
            {activeTab === 'code' && <CodeViewer files={mockCodeFiles} />}
            {activeTab === 'tools' && <ToolCallMonitor toolCalls={mockToolCalls} />}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
