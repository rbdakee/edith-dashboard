import { useState, useCallback } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { tasksApi } from '@/api/tasks';
import { STATUS_LABELS, PRIORITY_COLORS, PRIORITY_LABELS, SUB_STATUS_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { Task, TaskStatus } from '@/types';

const STATUSES: TaskStatus[] = ['in_progress', 'planned', 'idea', 'done', 'archive'];

const STATUS_DOT_COLORS: Record<TaskStatus, string> = {
  idea: 'bg-slate-400',
  planned: 'bg-blue-400',
  in_progress: 'bg-amber-400',
  done: 'bg-green-400',
  archive: 'bg-gray-500',
};

const NEXT_STATUS: Record<TaskStatus, TaskStatus> = {
  idea: 'planned',
  planned: 'in_progress',
  in_progress: 'done',
  done: 'archive',
  archive: 'idea',
};

interface SubTaskListProps {
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  queryKey?: unknown[];
}

export function SubTaskList({ tasks, onTaskClick, queryKey = ['tasks'] }: SubTaskListProps) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const queryClient = useQueryClient();

  const toggleSection = useCallback((status: string) => {
    setCollapsed((prev) => ({ ...prev, [status]: !prev[status] }));
  }, []);

  const cycleStatus = useCallback(
    async (e: React.MouseEvent, task: Task) => {
      e.stopPropagation();
      const newStatus = NEXT_STATUS[task.status];

      // Optimistic update
      queryClient.setQueryData<Task[]>(queryKey, (old = []) =>
        old.map((t) => (t.id === task.id ? { ...t, status: newStatus } : t))
      );

      try {
        await tasksApi.update(task.id, { status: newStatus });
        await queryClient.invalidateQueries({ queryKey });
        await queryClient.invalidateQueries({ queryKey: ['tasks'] });
      } catch {
        queryClient.invalidateQueries({ queryKey });
        queryClient.invalidateQueries({ queryKey: ['tasks'] });
      }
    },
    [queryClient, queryKey]
  );

  const grouped = STATUSES.map((status) => ({
    status,
    label: STATUS_LABELS[status],
    items: tasks.filter((t) => t.status === status),
  })).filter((g) => g.items.length > 0);

  if (tasks.length === 0) {
    return <div className="text-center py-6 text-gray-500 text-sm">No sub-tasks yet</div>;
  }

  return (
    <div className="space-y-3">
      {grouped.map(({ status, label, items }) => {
        const isCollapsed = collapsed[status] ?? false;

        return (
          <div key={status} className="rounded-lg border border-gray-700/60 overflow-hidden">
            {/* Section header */}
            <button
              onClick={() => toggleSection(status)}
              className="flex items-center gap-2 w-full px-3 py-2 bg-gray-800/40 hover:bg-gray-800/70 transition-colors text-left"
            >
              {isCollapsed ? (
                <ChevronRight className="h-3.5 w-3.5 text-gray-500 flex-shrink-0" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-gray-500 flex-shrink-0" />
              )}
              <span className={cn('h-2 w-2 rounded-full flex-shrink-0', STATUS_DOT_COLORS[status])} />
              <span className="text-xs font-medium text-gray-300">{label}</span>
              <span className="text-xs text-gray-500 ml-auto">{items.length}</span>
            </button>

            {/* Sub-task items */}
            {!isCollapsed && (
              <div className="divide-y divide-gray-700/40">
                {items.map((task) => (
                  <button
                    key={task.id}
                    onClick={() => onTaskClick(task)}
                    className="w-full text-left px-3 py-2.5 hover:bg-gray-800/50 transition-colors flex items-start gap-3"
                  >
                    {/* Status cycle button */}
                    <div
                      onClick={(e) => cycleStatus(e, task)}
                      title={`Click to move to ${STATUS_LABELS[NEXT_STATUS[task.status]]}`}
                      className="mt-0.5 flex-shrink-0 cursor-pointer"
                    >
                      <StatusBadge status={task.status} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-gray-200 leading-snug mb-1 truncate">
                        {task.title}
                      </div>
                      <div className="flex flex-wrap items-center gap-1.5">
                        {task.sub_status && (
                          <span
                            className={cn(
                              'text-xs rounded-full px-1.5 py-0.5',
                              SUB_STATUS_COLORS[task.sub_status]
                            )}
                          >
                            {task.sub_status}
                          </span>
                        )}
                        <span
                          className={cn(
                            'text-xs rounded-full border px-1.5 py-0.5',
                            PRIORITY_COLORS[task.priority]
                          )}
                        >
                          {PRIORITY_LABELS[task.priority]}
                        </span>
                        {task.executor_agent && <AgentBadge agentId={task.executor_agent} />}
                        <TimestampLabel
                          dateStr={task.last_activity_at}
                          className="ml-auto text-xs text-gray-500"
                        />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
