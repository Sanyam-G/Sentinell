import { SlackMessage } from '../types';

interface SlackViewerProps {
  messages: SlackMessage[];
}

export default function SlackViewer({ messages }: SlackViewerProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-auto scrollbar-thin p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`space-y-2 ${message.isRetrieved ? 'opacity-100' : 'opacity-40'}`}
          >
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded bg-slate-700 flex items-center justify-center text-white text-xs">
                {message.user[0].toUpperCase()}
              </div>
              <span className="text-xs text-slate-400">{message.user}</span>
              <span className="text-xs text-slate-600">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
              {message.isRetrieved && message.relevanceScore && (
                <span className="ml-auto text-xs text-cyan-400">
                  {(message.relevanceScore * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <p className="text-sm text-slate-300 leading-relaxed pl-7">{message.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
