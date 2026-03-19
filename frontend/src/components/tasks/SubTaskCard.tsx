import { StatusBadge } from '@/components/shared/StatusBadge';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { PRIORITY_COLORS, PRIORITY_LABELS, SUB_STATUS_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { Task } from '@/types';

interface SubTaskCardProps {
  task: Task;
  onClick: () => void;
}

export function SubTaskCard({ task, onClick }: SubTaskCardProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 bg-gray-800/60 hover:bg-gray-800 border border-gray-700 hover:border-gray-600 rounded-lg transition-colors"
    >
      <div className="flex items-start gap-2 mb-1.5">
        <span className="text-sm text-gray-200 flex-1 leading-snug">{task.title}</span>
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        <StatusBadge status={task.status} />
        {task.sub_status && (
          <span className={cn('text-xs rounded-full px-1.5 py-0.5', SUB_STATUS_COLORS[task.sub_status])}>
            {task.sub_status}
          </span>
        )}
        <span className={cn('text-xs rounded-full border px-1.5 py-0.5', PRIORITY_COLORS[task.priority])}>
          {PRIORITY_LABELS[task.priority]}
        </span>
        {task.executor_agent && <AgentBadge agentId={task.executor_agent} />}
        <TimestampLabel dateStr={task.last_activity_at} className="ml-auto text-xs text-gray-500" />
      </div>
    </button>
  );
}
