import { useQuery } from '@tanstack/react-query';
import { Bot, Cpu, Clock, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { agentsApi } from '@/api/agents';
import { AGENT_STATUS_COLORS, AGENT_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';

export function AgentsPage() {
  const { data: agents = [], isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list(),
    refetchInterval: 5_000,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-40 rounded-lg bg-gray-800 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Bot className="h-5 w-5 text-blue-400" />
        <h2 className="text-lg font-semibold text-gray-100">Agent Monitor</h2>
        <span className="text-sm text-gray-500 ml-auto">Refreshes every 5s</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agents.map((agent) => {
          const agentColor = AGENT_COLORS[agent.id] ?? 'bg-gray-500/20 text-gray-300 border-gray-500/30';
          return (
            <Card key={agent.id} className="overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center border', agentColor)}>
                      <Bot className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{agent.name}</CardTitle>
                      <div className="flex items-center gap-1.5 mt-1">
                        <Cpu className="h-3 w-3 text-gray-500" />
                        <span className="text-xs text-gray-500">{agent.model}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className={cn('w-2 h-2 rounded-full', AGENT_STATUS_COLORS[agent.status])} />
                    <span className="text-xs capitalize text-gray-400">{agent.status}</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 space-y-3">
                {/* Skills */}
                <div>
                  <div className="text-xs text-gray-500 mb-1.5 flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    Skills
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {agent.skills.map((skill) => (
                      <span
                        key={skill}
                        className="text-xs bg-gray-700/50 border border-gray-600/50 text-gray-300 rounded px-1.5 py-0.5"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Current task */}
                {agent.current_task_id && (
                  <div className="text-xs text-gray-400">
                    <span className="text-gray-500">Task: </span>
                    <span className="font-mono text-blue-400">{agent.current_task_id}</span>
                  </div>
                )}

                {/* Last active */}
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Clock className="h-3 w-3" />
                  Last active: <TimestampLabel dateStr={agent.last_active_at} />
                </div>
              </CardContent>
            </Card>
          );
        })}

        {agents.length === 0 && (
          <div className="col-span-2 text-center py-12 text-gray-500">
            <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No agents data available yet</p>
            <p className="text-xs mt-1">Agents will appear when the backend is running</p>
          </div>
        )}
      </div>
    </div>
  );
}
