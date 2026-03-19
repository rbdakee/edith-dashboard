import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Terminal, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { sessionsApi } from '@/api/sessions';
import { formatDuration } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Session } from '@/types';

const STATUS_ICONS: Record<Session['status'], React.ReactNode> = {
  active: <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />,
  completed: <CheckCircle2 className="h-4 w-4 text-green-400" />,
  failed: <XCircle className="h-4 w-4 text-red-400" />,
  cancelled: <AlertCircle className="h-4 w-4 text-gray-500" />,
};

const STATUS_COLORS: Record<Session['status'], string> = {
  active: 'text-green-400',
  completed: 'text-green-300',
  failed: 'text-red-400',
  cancelled: 'text-gray-500',
};

export function SessionsPage() {
  const [selected, setSelected] = useState<Session | null>(null);

  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => sessionsApi.list(),
    refetchInterval: 10_000,
  });

  return (
    <div className="flex gap-4 h-full">
      {/* Sessions list */}
      <div className="flex-1 space-y-4">
        <div className="flex items-center gap-2">
          <Terminal className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-gray-100">Sessions</h2>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-lg bg-gray-800 animate-pulse" />)}
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Terminal className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No sessions recorded yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => (
              <Card
                key={session.id}
                className={cn('cursor-pointer hover:border-gray-600 transition-colors', selected?.id === session.id && 'border-blue-500/50')}
                onClick={() => setSelected(session)}
              >
                <CardContent className="py-3 px-4">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      {STATUS_ICONS[session.status]}
                      <AgentBadge agentId={session.agent_id} />
                      <span className={cn('text-xs capitalize', STATUS_COLORS[session.status])}>
                        {session.status}
                      </span>
                    </div>
                    <TimestampLabel dateStr={session.started_at} />
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="font-mono text-gray-600">{session.id.slice(0, 8)}...</span>
                    {session.task_id && (
                      <span>task: <span className="text-blue-400 font-mono">{session.task_id.slice(0, 8)}</span></span>
                    )}
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDuration(session.started_at, session.ended_at)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Session detail panel */}
      {selected && (
        <div className="w-80 flex-shrink-0">
          <Card className="sticky top-0">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Terminal className="h-4 w-4 text-blue-400" />
                Session Detail
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <div className="text-xs text-gray-500 mb-1">Agent</div>
                <AgentBadge agentId={selected.agent_id} />
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Status</div>
                <span className={cn('text-sm capitalize', STATUS_COLORS[selected.status])}>
                  {selected.status}
                </span>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Model</div>
                <span className="text-gray-300 font-mono text-xs">{selected.model}</span>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Duration</div>
                <span className="text-gray-300">{formatDuration(selected.started_at, selected.ended_at)}</span>
              </div>
              {selected.task_id && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Task</div>
                  <span className="text-blue-400 font-mono text-xs">{selected.task_id}</span>
                </div>
              )}
              <div>
                <div className="text-xs text-gray-500 mb-1">Context</div>
                <pre className="text-xs text-gray-400 bg-gray-800 rounded p-2 overflow-auto max-h-32">
                  {JSON.stringify(selected.context_snapshot, null, 2)}
                </pre>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Prompts: {selected.prompts.length}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Actions: {selected.actions.length}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Outputs: {selected.outputs.length}</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
