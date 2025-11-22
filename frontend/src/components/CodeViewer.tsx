import { CodeFile } from '../types';

interface CodeViewerProps {
  files: CodeFile[];
}

export default function CodeViewer({ files }: CodeViewerProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b border-cyan-500/20">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-cyan-400"></span>
          Code Context
        </h3>
      </div>
      <div className="flex-1 overflow-auto scrollbar-thin">
        {files.map((file, idx) => (
          <div key={idx} className="border-b border-slate-800 last:border-b-0">
            <div className="px-4 py-2 bg-slate-800/50">
              <div className="flex items-center gap-2">
                <span className="text-xs text-cyan-400">📄</span>
                <code className="text-xs text-gray-300">{file.path}</code>
              </div>
            </div>
            <div className="p-4 bg-slate-950/50">
              <pre className="text-xs leading-relaxed overflow-auto">
                {file.content.split('\n').map((line, lineIdx) => {
                  const lineNumber = lineIdx + 1;
                  const isHighlighted = file.highlightedLines?.includes(lineNumber);
                  return (
                    <div
                      key={lineIdx}
                      className={`${
                        isHighlighted
                          ? 'bg-yellow-500/10 border-l-2 border-yellow-500 pl-2 -ml-2'
                          : ''
                      }`}
                    >
                      <span className="inline-block w-8 text-gray-600 select-none">
                        {lineNumber}
                      </span>
                      <code
                        className={
                          isHighlighted ? 'text-yellow-200' : 'text-gray-300'
                        }
                      >
                        {line}
                      </code>
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
