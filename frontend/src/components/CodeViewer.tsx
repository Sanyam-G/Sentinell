import { CodeFile } from '../types';
import { highlightPython } from '../utils/syntaxHighlight';

interface CodeViewerProps {
  files: CodeFile[];
}

export default function CodeViewer({ files }: CodeViewerProps) {
  return (
    <div className="h-full flex flex-col bg-slate-900/30">
      <div className="flex-1 overflow-auto scrollbar-thin">
        {files.map((file, idx) => (
          <div key={idx}>
            <div className="px-6 py-3 bg-slate-900/50 border-b border-slate-800">
              <code className="text-xs text-slate-400">{file.path}</code>
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
                      className={`${isHighlighted ? 'bg-cyan-500/5' : ''}`}
                    >
                      <span className="inline-block w-10 text-slate-600 select-none text-right pr-4">
                        {lineNumber}
                      </span>
                      <code
                        className={isHighlighted ? 'text-slate-200' : 'text-slate-400'}
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
