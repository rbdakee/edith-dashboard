import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { ApproveButton } from '@/components/shared/ApproveButton';
import { PRIORITY_COLORS, PRIORITY_LABELS, SUB_STATUS_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { Task } from '@/types';

interface TaskCardProps {
  task: Task;
  onClick: (task: Task) => void;
}

export function TaskCard({ task, onClick }: TaskCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'bg-gray-800/80 border border-gray-700/60 rounded-lg p-3 cursor-pointer hover:border-gray-600 hover:bg-gray-800 transition-colors group',
        isDragging && 'opacity-50 shadow-xl border-blue-500/50'
      )}
      onClick={() => onClick(task)}
    >
      <div className="flex items-start gap-1.5">
        {/* Drag handle */}
        <button
          {...attributes}
          {...listeners}
          className="mt-0.5 flex-shrink-0 text-gray-600 hover:text-gray-400 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => e.stopPropagation()}
        >
          <GripVertical className="h-3.5 w-3.5" />
        </button>

        <div className="flex-1 min-w-0 space-y-1.5">
          {/* Title */}
          <div className="text-sm font-medium text-gray-100 leading-snug">{task.title}</div>

          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-1">
            <span className={cn('text-xs rounded-full border px-1.5 py-0.5', PRIORITY_COLORS[task.priority])}>
              {PRIORITY_LABELS[task.priority]}
            </span>
            {task.sub_status && (
              <span className={cn('text-xs rounded-full px-1.5 py-0.5', SUB_STATUS_COLORS[task.sub_status])}>
                {task.sub_status}
              </span>
            )}
          </div>

          {/* Agent + timestamp */}
          <div className="flex items-center gap-2">
            {task.executor_agent && <AgentBadge agentId={task.executor_agent} />}
            <TimestampLabel dateStr={task.last_activity_at} className="ml-auto text-xs text-gray-600" />
          </div>

          {/* Approve button */}
          {task.status === 'planned' && !task.approved && (
            <div onClick={(e) => e.stopPropagation()}>
              <ApproveButton taskId={task.id} taskTitle={task.title} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
