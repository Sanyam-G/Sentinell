import { SlackMessage } from '../types';

interface SlackViewerProps {
  messages: SlackMessage[];
}

export default function SlackViewer({ messages }: SlackViewerProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-auto scrollbar-thin space-y-4">
        {messages.length === 0 && (
          <div className="text-xs text-slate-500">No Slack context has been ingested for this incident yet.</div>
        )}
        {messages.map((message) => {
          const username = message.user || 'unknown';
          const initials = username.slice(0, 2).toUpperCase();
          return (
            <div
              key={message.id}
              className={`space-y-2 ${message.isRetrieved ? 'opacity-100' : 'opacity-40'}`}
            >
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded bg-slate-800 flex items-center justify-center text-white text-xs font-semibold">
                  {initials}
                </div>
                <div className="flex flex-col text-[11px] text-slate-500">
                  <span className="text-slate-300 font-medium">{username}</span>
                  <span className="uppercase tracking-wide">{message.channel}</span>
                </div>
                <span className="text-xs text-slate-600 ml-auto">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
                {message.isRetrieved && message.relevanceScore && (
                  <span className="ml-auto text-xs text-cyan-400">
                    {(message.relevanceScore * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-300 leading-relaxed pl-9">{message.text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
