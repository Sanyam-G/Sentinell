import { SlackMessage } from '../types';

interface SlackViewerProps {
  messages: SlackMessage[];
}

export default function SlackViewer({ messages }: SlackViewerProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-auto scrollbar-thin space-y-4">
        {messages.length === 0 && (
          <div className="text-xs text-gray-500 dark:text-slate-500">No Slack context has been ingested for this incident yet.</div>
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
                <div className="w-8 h-8 rounded-xl bg-gray-200 dark:bg-slate-800 flex items-center justify-center text-gray-600 dark:text-white text-xs font-semibold">
                  {initials}
                </div>
                <div className="flex flex-col text-[11px] text-gray-500 dark:text-slate-500">
                  <span className="text-gray-900 dark:text-slate-200 font-medium">{username}</span>
                  <span className="uppercase tracking-wide">{message.channel}</span>
                </div>
                <span className="text-xs text-gray-400 dark:text-slate-500 ml-auto">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
                {message.isRetrieved && message.relevanceScore && (
                  <span className="ml-auto text-xs text-blue-600 dark:text-cyan-300">
                    {(message.relevanceScore * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-700 dark:text-slate-200 leading-relaxed pl-10">{message.text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
