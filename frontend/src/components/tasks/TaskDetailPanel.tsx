import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { X, ExternalLink } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { MarkdownRenderer } from '@/components/shared/MarkdownRenderer';
import { ApproveButton } from '@/components/shared/ApproveButton';
import { PlanEditor } from './PlanEditor';
import { SubTaskCreateButton } from './SubTaskCreateButton';
import { SubTaskList } from './SubTaskList';
import { CommentThread } from '@/components/comments/CommentThread';
import { eventsApi } from '@/api/events';
import { sessionsApi } from '@/api/sessions';
import { artifactsApi } from '@/api/artifacts';
import { tasksApi } from '@/api/tasks';
import { PRIORITY_COLORS, PRIORITY_LABELS, SUB_STATUS_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { Task } from '@/types';

interface TaskDetailPanelProps {
  task: Task;
  onClose: () => void;
}

export function TaskDetailPanel({ task, onClose }: TaskDetailPanelProps) {
  const [selectedSubTask, setSelectedSubTask] = useState<Task | null>(null);

  const { data: subtasks = [] } = useQuery({
    queryKey: ['tasks', { parent_task_id: task.id }],
    queryFn: () => tasksApi.list({ parent_task_id: task.id }),
  });

  const { data: events = [] } = useQuery({
    queryKey: ['events', { task_id: task.id }],
    queryFn: () => eventsApi.list({ task_id: task.id }),
  });

  const { data: sessions = [] } = useQuery({
    queryKey: ['sessions', { task_id: task.id }],
    queryFn: () => sessionsApi.list({ task_id: task.id }),
  });

  const { data: artifacts = [] } = useQuery({
    queryKey: ['artifacts', { task_id: task.id }],
    queryFn: () => artifactsApi.list({ task_id: task.id }),
  });

  return (
    <div className="flex flex-col h-full bg-gray-900 border-l border-gray-700">
      {/* Header */}
      <div className="flex items-start gap-3 p-4 border-b border-gray-700">
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-semibold text-gray-100 mb-2">{task.title}</h2>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={task.status} />
            {task.sub_status && (
              <span className={cn('text-xs rounded-full px-2 py-0.5', SUB_STATUS_COLORS[task.sub_status])}>
                {task.sub_status}
              </span>
            )}
            <span className={cn('text-xs rounded-full border px-2 py-0.5', PRIORITY_COLORS[task.priority])}>
              {PRIORITY_LABELS[task.priority]}
            </span>
            {task.executor_agent && <AgentBadge agentId={task.executor_agent} />}
          </div>
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            <span>Updated <TimestampLabel dateStr={task.updated_at} /></span>
            {task.notion_id && (
              <a
                href={`https://notion.so/${task.notion_id.replace(/-/g, '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
              >
                <ExternalLink className="h-3 w-3" />
                Notion
              </a>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {task.status === 'planned' && !task.approved && (
            <ApproveButton task={task} />
          )}
          <Button variant="ghost" size="icon" onClick={onClose} className="h-7 w-7">
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-1 overflow-hidden flex flex-col px-4 pt-3">
        <Tabs defaultValue="plan" className="flex flex-col h-full">
          <TabsList className="flex-shrink-0 overflow-x-auto">
            <TabsTrigger value="plan">Plan</TabsTrigger>
            <TabsTrigger value="context">Context</TabsTrigger>
            <TabsTrigger value="subtasks">Sub-Tasks ({subtasks.length})</TabsTrigger>
            <TabsTrigger value="events">Events ({events.length})</TabsTrigger>
            <TabsTrigger value="sessions">Sessions ({sessions.length})</TabsTrigger>
            <TabsTrigger value="files">Files ({artifacts.length})</TabsTrigger>
            <TabsTrigger value="comments">Comments</TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto mt-4 pb-4">
            <TabsContent value="plan">
              <PlanEditor taskId={task.id} plan={task.plan} />
            </TabsContent>

            <TabsContent value="context">
              <div className="space-y-4">
                {task.description && (
                  <div>
                    <div className="text-xs text-gray-500 mb-2">Description</div>
                    <MarkdownRenderer content={task.description} />
                  </div>
                )}
                {task.context_file && (
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Context File</div>
                    <code className="text-xs text-blue-300 bg-gray-800 px-2 py-1 rounded block">
                      {task.context_file}
                    </code>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-gray-800 rounded p-2">
                    <div className="text-gray-500 mb-1">Category</div>
                    <div className="text-gray-200 capitalize">{task.category}</div>
                  </div>
                  <div className="bg-gray-800 rounded p-2">
                    <div className="text-gray-500 mb-1">Created</div>
                    <TimestampLabel dateStr={task.created_at} />
                  </div>
                  {task.approved_at && (
                    <div className="bg-gray-800 rounded p-2">
                      <div className="text-gray-500 mb-1">Approved</div>
                      <TimestampLabel dateStr={task.approved_at} />
                    </div>
                  )}
                  {task.parent_task_id && (
                    <div className="bg-gray-800 rounded p-2">
                      <div className="text-gray-500 mb-1">Parent Task</div>
                      <code className="text-blue-400 font-mono text-xs">{task.parent_task_id.slice(0, 8)}</code>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="subtasks">
              <div className="space-y-3">
                <SubTaskCreateButton parentTaskId={task.id} />
                {subtasks.length === 0 ? (
                  <div className="text-center py-6 text-gray-500 text-sm">No sub-tasks yet</div>
                ) : (
                  <SubTaskList
                    tasks={subtasks}
                    onTaskClick={setSelectedSubTask}
                    queryKey={['tasks', { parent_task_id: task.id }]}
                  />
                )}
              </div>
              {selectedSubTask && (
                <div className="fixed inset-0 z-50 flex items-stretch justify-end">
                  <div className="w-[480px] shadow-xl">
                    <TaskDetailPanel task={selectedSubTask} onClose={() => setSelectedSubTask(null)} />
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="events">
              {events.length === 0 ? (
                <div className="text-center py-6 text-gray-500 text-sm">No events for this task</div>
              ) : (
                <div className="space-y-2">
                  {events.map((event) => (
                    <div key={event.id} className="flex gap-2 p-2 bg-gray-800/50 rounded text-xs">
                      <div className="w-1 rounded-full bg-blue-500 flex-shrink-0" />
                      <div>
                        <div className="text-blue-300 font-mono">{event.type}</div>
                        <div className="text-gray-300">{event.title}</div>
                        <TimestampLabel dateStr={event.timestamp} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="sessions">
              {sessions.length === 0 ? (
                <div className="text-center py-6 text-gray-500 text-sm">No sessions for this task</div>
              ) : (
                <div className="space-y-2">
                  {sessions.map((session) => (
                    <div key={session.id} className="p-2 bg-gray-800/50 rounded text-xs">
                      <div className="flex items-center gap-2 mb-1">
                        <AgentBadge agentId={session.agent_id} />
                        <span className="text-gray-400 capitalize">{session.status}</span>
                      </div>
                      <TimestampLabel dateStr={session.started_at} />
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="files">
              {artifacts.length === 0 ? (
                <div className="text-center py-6 text-gray-500 text-sm">No files for this task</div>
              ) : (
                <div className="space-y-2">
                  {artifacts.map((artifact) => (
                    <div key={artifact.id} className="p-2 bg-gray-800/50 rounded text-xs">
                      <div className="text-gray-200 font-medium">{artifact.filename}</div>
                      <div className="text-gray-500 truncate">{artifact.filepath}</div>
                      {artifact.content_preview && (
                        <div className="text-gray-400 mt-1 truncate">{artifact.content_preview}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="comments">
              <CommentThread taskId={task.id} />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
