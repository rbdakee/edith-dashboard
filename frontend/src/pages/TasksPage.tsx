import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ListTodo, ArrowUpDown } from 'lucide-react';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { TaskDetailPanel } from '@/components/tasks/TaskDetailPanel';
import { NewTaskDialog } from '@/components/tasks/NewTaskDialog';
import { PRIORITY_COLORS, PRIORITY_LABELS } from '@/lib/constants';
import { tasksApi } from '@/api/tasks';
import { cn } from '@/lib/utils';
import type { Task } from '@/types';

type SortField = 'title' | 'status' | 'priority' | 'updated_at';
type SortDir = 'asc' | 'desc';

const PRIORITY_ORDER = { p0: 0, p1: 1, p2: 2, p3: 3 };
const STATUS_ORDER = { idea: 0, planned: 1, in_progress: 2, done: 3, archive: 4 };

export function TasksPage() {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [sortField, setSortField] = useState<SortField>('updated_at');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list(),
    refetchInterval: 30_000,
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const sorted = [...tasks].sort((a, b) => {
    let cmp = 0;
    if (sortField === 'title') cmp = a.title.localeCompare(b.title);
    else if (sortField === 'status') cmp = STATUS_ORDER[a.status] - STATUS_ORDER[b.status];
    else if (sortField === 'priority') cmp = PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority];
    else if (sortField === 'updated_at') cmp = a.updated_at.localeCompare(b.updated_at);
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const SortIcon = ({ field }: { field: SortField }) => (
    <ArrowUpDown
      className={cn(
        'h-3 w-3 ml-1 inline',
        sortField === field ? 'text-blue-400' : 'text-gray-600'
      )}
    />
  );

  return (
    <div className="flex gap-4 h-full">
      {/* Table */}
      <div className="flex-1 min-w-0 space-y-4">
        <div className="flex items-center gap-2">
          <ListTodo className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-gray-100">Tasks</h2>
          <span className="text-sm text-gray-500">({tasks.length})</span>
          <div className="ml-auto">
            <NewTaskDialog />
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 rounded-lg bg-gray-800 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-gray-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 bg-gray-800/50">
                  <th
                    className="text-left px-4 py-2.5 text-xs font-medium text-gray-400 cursor-pointer hover:text-gray-200"
                    onClick={() => handleSort('title')}
                  >
                    Title <SortIcon field="title" />
                  </th>
                  <th
                    className="text-left px-3 py-2.5 text-xs font-medium text-gray-400 cursor-pointer hover:text-gray-200 w-32"
                    onClick={() => handleSort('status')}
                  >
                    Status <SortIcon field="status" />
                  </th>
                  <th
                    className="text-left px-3 py-2.5 text-xs font-medium text-gray-400 cursor-pointer hover:text-gray-200 w-24"
                    onClick={() => handleSort('priority')}
                  >
                    Priority <SortIcon field="priority" />
                  </th>
                  <th className="text-left px-3 py-2.5 text-xs font-medium text-gray-400 w-36">Agent</th>
                  <th
                    className="text-left px-3 py-2.5 text-xs font-medium text-gray-400 cursor-pointer hover:text-gray-200 w-28"
                    onClick={() => handleSort('updated_at')}
                  >
                    Updated <SortIcon field="updated_at" />
                  </th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((task) => (
                  <tr
                    key={task.id}
                    className={cn(
                      'border-b border-gray-700/50 cursor-pointer hover:bg-gray-800/50 transition-colors',
                      selectedTask?.id === task.id && 'bg-blue-500/5 border-blue-500/20'
                    )}
                    onClick={() => setSelectedTask(task)}
                  >
                    <td className="px-4 py-2.5">
                      <div className="font-medium text-gray-200 truncate max-w-xs">{task.title}</div>
                    </td>
                    <td className="px-3 py-2.5">
                      <StatusBadge status={task.status} />
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={cn('text-xs rounded-full border px-1.5 py-0.5', PRIORITY_COLORS[task.priority])}>
                        {PRIORITY_LABELS[task.priority]}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      {task.executor_agent ? (
                        <AgentBadge agentId={task.executor_agent} />
                      ) : (
                        <span className="text-xs text-gray-600">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      <TimestampLabel dateStr={task.updated_at} />
                    </td>
                  </tr>
                ))}
                {sorted.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-gray-500 text-sm">
                      No tasks yet. Create your first task!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selectedTask && (
        <div className="w-[420px] flex-shrink-0 h-full overflow-hidden rounded-lg border border-gray-700">
          <TaskDetailPanel
            task={selectedTask}
            onClose={() => setSelectedTask(null)}
          />
        </div>
      )}
    </div>
  );
}
