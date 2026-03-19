import { useQuery } from '@tanstack/react-query';
import { Activity, Bot, CheckCircle2, Clock, AlertCircle, Lightbulb } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { agentsApi } from '@/api/agents';
import { tasksApi } from '@/api/tasks';
import { eventsApi } from '@/api/events';
import { AGENT_STATUS_COLORS, EVENT_TYPE_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { TaskStatus } from '@/types';

const STATUS_COUNTS_CONFIG: { status: TaskStatus; label: string; color: string; icon: React.ReactNode }[] = [
  { status: 'idea', label: 'Ideas', color: 'text-slate-400', icon: <Lightbulb className="h-4 w-4" /> },
  { status: 'planned', label: 'Planned', color: 'text-blue-400', icon: <Clock className="h-4 w-4" /> },
  { status: 'in_progress', label: 'In Progress', color: 'text-amber-400', icon: <Activity className="h-4 w-4" /> },
  { status: 'done', label: 'Done', color: 'text-green-400', icon: <CheckCircle2 className="h-4 w-4" /> },
  { status: 'archive', label: 'Archived', color: 'text-gray-500', icon: <AlertCircle className="h-4 w-4" /> },
];

export function OverviewPage() {
  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list(),
    refetchInterval: 10_000,
  });

  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list(),
    refetchInterval: 30_000,
  });

  const { data: events = [] } = useQuery({
    queryKey: ['events', { limit: '10' }],
    queryFn: () => eventsApi.list({ limit: '10' }),
    refetchInterval: 15_000,
  });

  const taskCounts = STATUS_COUNTS_CONFIG.map((cfg) => ({
    ...cfg,
    count: tasks.filter((t) => t.status === cfg.status).length,
  }));

  const activeAgents = agents.filter((a) => a.status !== 'idle').length;
  const inProgressTasks = tasks.filter((t) => t.status === 'in_progress').length;
  const pendingApprovals = tasks.filter((t) => t.status === 'planned' && !t.approved).length;

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Bot className="h-4 w-4 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-100">{activeAgents}</div>
                <div className="text-xs text-gray-400">Active Agents</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                <Activity className="h-4 w-4 text-amber-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-100">{inProgressTasks}</div>
                <div className="text-xs text-gray-400">In Progress</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-4 w-4 text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-100">{tasks.filter((t) => t.status === 'done').length}</div>
                <div className="text-xs text-gray-400">Completed</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <AlertCircle className="h-4 w-4 text-yellow-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-100">{pendingApprovals}</div>
                <div className="text-xs text-gray-400">Pending Approval</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Bot className="h-4 w-4 text-blue-400" />
              Agent Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {agents.length === 0 ? (
              <div className="text-gray-500 text-sm">No agents data</div>
            ) : (
              agents.map((agent) => (
                <div key={agent.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={cn('w-2 h-2 rounded-full', AGENT_STATUS_COLORS[agent.status])} />
                    <AgentBadge agentId={agent.id} />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 capitalize">{agent.status}</span>
                    {agent.last_active_at && (
                      <TimestampLabel dateStr={agent.last_active_at} />
                    )}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Task counts bar */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-400" />
              Task Distribution
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {taskCounts.map(({ status, label, color, icon, count }) => (
              <div key={status} className="flex items-center gap-3">
                <div className={cn('flex-shrink-0', color)}>{icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">{label}</span>
                    <span className={color}>{count}</span>
                  </div>
                  <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all', {
                        'bg-slate-400': status === 'idea',
                        'bg-blue-400': status === 'planned',
                        'bg-amber-400': status === 'in_progress',
                        'bg-green-400': status === 'done',
                        'bg-gray-500': status === 'archive',
                      })}
                      style={{ width: tasks.length > 0 ? `${(count / tasks.length) * 100}%` : '0%' }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Events */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-400" />
              Recent Events
              <div className="ml-auto flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                <span className="text-xs text-green-400">Live</span>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {events.length === 0 ? (
              <div className="text-gray-500 text-sm">No events yet</div>
            ) : (
              <div className="space-y-2">
                {events.slice(0, 8).map((event) => (
                  <div key={event.id} className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className={cn('text-xs font-medium truncate', EVENT_TYPE_COLORS[event.type] ?? 'text-gray-300')}>
                        {event.title}
                      </div>
                      <div className="flex items-center gap-1 mt-0.5">
                        {event.agent_id && <AgentBadge agentId={event.agent_id} className="text-xs" />}
                        <TimestampLabel dateStr={event.timestamp} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
