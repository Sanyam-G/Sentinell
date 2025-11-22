import { SlackMessage } from '../types';

interface SlackViewerProps {
  messages: SlackMessage[];
}

export default function SlackViewer({ messages }: SlackViewerProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b border-cyan-500/20">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-cyan-400"></span>
          Slack Context
        </h3>
        <div className="flex gap-2 mt-2">
          <span className="text-xs px-2 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            #prod-alerts
          </span>
          <span className="text-xs px-2 py-1 rounded bg-gray-500/10 text-gray-400 border border-gray-500/30">
            #infra-debug
          </span>
        </div>
      </div>
      <div className="flex-1 overflow-auto scrollbar-thin p-4 space-y-3">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`p-3 rounded-lg border transition-all ${
              message.isRetrieved
                ? 'bg-cyan-500/10 border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                : 'bg-slate-800/30 border-slate-700/30'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
                {message.user[0].toUpperCase()}
              </div>
              <span className="text-sm font-semibold text-white">{message.user}</span>
              <span className="text-xs text-gray-500">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
              {message.isRetrieved && message.relevanceScore && (
                <span className="ml-auto text-xs px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  {(message.relevanceScore * 100).toFixed(0)}% match
                </span>
              )}
            </div>
            <p className="text-sm text-gray-300 leading-relaxed">{message.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
