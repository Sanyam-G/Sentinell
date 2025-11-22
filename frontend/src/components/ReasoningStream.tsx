interface ReasoningStep {
  type: 'thought' | 'action' | 'observation';
  content: string;
}

interface ReasoningStreamProps {
  steps: ReasoningStep[];
}

export default function ReasoningStream({ steps }: ReasoningStreamProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case 'thought':
        return '💭';
      case 'action':
        return '⚡';
      case 'observation':
        return '👁️';
      default:
        return '•';
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'thought':
        return 'text-purple-400';
      case 'action':
        return 'text-cyan-400';
      case 'observation':
        return 'text-green-400';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="space-y-3">
      {steps.map((step, idx) => (
        <div key={idx} className="flex gap-3 items-start">
          <span className="text-lg mt-0.5">{getIcon(step.type)}</span>
          <div className="flex-1">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">
              {step.type}
            </div>
            <p className={`text-sm ${getColor(step.type)}`}>
              {step.content}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
