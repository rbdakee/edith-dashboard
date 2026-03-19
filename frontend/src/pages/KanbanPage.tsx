import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Kanban, Filter } from 'lucide-react';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';
import { TaskDetailPanel } from '@/components/tasks/TaskDetailPanel';
import { NewTaskDialog } from '@/components/tasks/NewTaskDialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { tasksApi } from '@/api/tasks';
import type { Task } from '@/types';

export function KanbanPage() {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [filterAgent, setFilterAgent] = useState('');
  const [filterPriority, setFilterPriority] = useState('');

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list(),
    refetchInterval: 30_000,
  });

  return (
    <div className="flex gap-4 h-full">
      {/* Main board */}
      <div className="flex-1 min-w-0 space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Kanban className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-gray-100">Kanban</h2>
          <div className="ml-auto flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <Select value={filterAgent || 'all'} onValueChange={(v) => setFilterAgent(v === 'all' ? '' : v)}>
              <SelectTrigger className="h-8 w-40 text-xs">
                <SelectValue placeholder="All agents" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All agents</SelectItem>
                <SelectItem value="main">E.D.I.T.H. Main</SelectItem>
                <SelectItem value="edith-dev">E.D.I.T.H. Dev</SelectItem>
                <SelectItem value="edith-routine">E.D.I.T.H. Routine</SelectItem>
                <SelectItem value="edith-analytics">E.D.I.T.H. Analytics</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterPriority || 'all'} onValueChange={(v) => setFilterPriority(v === 'all' ? '' : v)}>
              <SelectTrigger className="h-8 w-32 text-xs">
                <SelectValue placeholder="All priorities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All priorities</SelectItem>
                <SelectItem value="p0">P0 Critical</SelectItem>
                <SelectItem value="p1">P1 High</SelectItem>
                <SelectItem value="p2">P2 Medium</SelectItem>
                <SelectItem value="p3">P3 Low</SelectItem>
              </SelectContent>
            </Select>
            <NewTaskDialog />
          </div>
        </div>

        {isLoading ? (
          <div className="flex gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="w-72 flex-shrink-0 h-64 rounded-lg bg-gray-800 animate-pulse" />
            ))}
          </div>
        ) : (
          <KanbanBoard
            tasks={tasks}
            onTaskClick={setSelectedTask}
            filterAgent={filterAgent}
            filterPriority={filterPriority}
          />
        )}
      </div>

      {/* Task detail panel */}
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
