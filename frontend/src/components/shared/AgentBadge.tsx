import { cn } from '@/lib/utils';
import { AGENT_COLORS } from '@/lib/constants';

interface AgentBadgeProps {
  agentId: string;
  className?: string;
}

const AGENT_NAMES: Record<string, string> = {
  main: 'E.D.I.T.H.',
  'edith-dev': 'Dev',
  'edith-routine': 'Routine',
  'edith-analytics': 'Analytics',
  'edith-orchestrator': 'Orchestrator',
};

export function AgentBadge({ agentId, className }: AgentBadgeProps) {
  const colorClass = AGENT_COLORS[agentId] ?? 'bg-gray-500/20 text-gray-300 border-gray-500/30';
  const name = AGENT_NAMES[agentId] ?? agentId;

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
        colorClass,
        className
      )}
    >
      {name}
    </span>
  );
}
