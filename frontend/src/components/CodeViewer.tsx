import { CodeFile } from '../types';
import { highlightPython } from '../utils/syntaxHighlight';

interface CodeViewerProps {
  files: CodeFile[];
}

export default function CodeViewer({ files }: CodeViewerProps) {
  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-950/40">
      <div className="flex-1 overflow-auto scrollbar-thin">
        {files.length === 0 && (
          <div className="p-6 text-xs text-gray-500 dark:text-slate-400">
            No file snippets available yet. Once commits or diffs are ingested for an incident, they will render here.
          </div>
        )}
        {files.map((file, idx) => (
          <div key={idx}>
            <div className="px-6 py-3 bg-gray-50 dark:bg-slate-900/60 border-b border-gray-200 dark:border-slate-800">
              <code className="text-xs text-gray-600 dark:text-slate-400">{file.path}</code>
            </div>
            <div className="p-6">
              <pre className="text-xs leading-6 overflow-auto">
                {file.content.split('\n').map((line, lineIdx) => {
                  const lineNumber = lineIdx + 1;
                  const isHighlighted = file.highlightedLines?.includes(lineNumber);
                  const highlightedLine = file.language === 'python' ? highlightPython(line) : line;

                  return (
                    <div
                      key={lineIdx}
                      className={`${isHighlighted ? 'bg-blue-50 dark:bg-blue-500/10' : ''}`}
                    >
                      <span className="inline-block w-10 text-gray-400 dark:text-slate-600 select-none text-right pr-4">
                        {lineNumber}
                      </span>
                      <code
                        className={isHighlighted ? 'text-blue-600 dark:text-blue-200' : 'text-gray-700 dark:text-slate-200'}
                        dangerouslySetInnerHTML={{ __html: highlightedLine }}
                      />
                    </div>
                  );
                })}
              </pre>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
