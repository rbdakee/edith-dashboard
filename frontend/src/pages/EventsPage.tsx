import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, Filter, RefreshCw } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { EventDetailDrawer } from '@/components/events/EventDetailDrawer';
import { eventsApi } from '@/api/events';
import { EVENT_TYPE_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { DashboardEvent } from '@/types';

export function EventsPage() {
  const [limit, setLimit] = useState(50);
  const [filterAgent, setFilterAgent] = useState('');
  const [filterType, setFilterType] = useState('');
  const [selectedEvent, setSelectedEvent] = useState<DashboardEvent | null>(null);

  const params: Record<string, string> = { limit: String(limit) };
  if (filterAgent) params.agent_id = filterAgent;
  if (filterType) params.event_type = filterType;

  const { data: events = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['events', params],
    queryFn: () => eventsApi.list(params),
    refetchInterval: 15_000,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Activity className="h-5 w-5 text-blue-400" />
        <h2 className="text-lg font-semibold text-gray-100">Event Log</h2>
        <div className="ml-auto flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-green-400">Live</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 items-center flex-wrap">
        <Filter className="h-4 w-4 text-gray-500" />
        <Input
          className="w-40 h-8 text-xs"
          placeholder="Filter by type..."
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        />
        <Input
          className="w-40 h-8 text-xs"
          placeholder="Filter by agent..."
          value={filterAgent}
          onChange={(e) => setFilterAgent(e.target.value)}
        />
        <Button variant="ghost" size="sm" onClick={() => refetch()} className="h-8">
          <RefreshCw className={cn('h-3.5 w-3.5', isFetching && 'animate-spin')} />
        </Button>
      </div>

      {/* Events list */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 rounded-lg bg-gray-800 animate-pulse" />
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No events yet</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {events.map((event) => (
            <Card key={event.id} className="hover:border-gray-600 transition-colors cursor-pointer" onClick={() => setSelectedEvent(event)}>
              <CardContent className="py-3 px-4">
                <div className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={cn('text-xs font-medium font-mono', EVENT_TYPE_COLORS[event.type] ?? 'text-gray-300')}>
                        {event.type}
                      </span>
                      <span className="text-xs text-gray-300 flex-1 truncate">{event.title}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {event.agent_id && <AgentBadge agentId={event.agent_id} />}
                      <span className="text-xs text-gray-600 bg-gray-800 px-1.5 py-0.5 rounded">
                        {event.source}
                      </span>
                      {event.task_id && (
                        <span className="text-xs text-gray-500 font-mono">task:{event.task_id.slice(0, 8)}</span>
                      )}
                      <TimestampLabel dateStr={event.timestamp} className="ml-auto text-xs text-gray-500" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {events.length >= limit && (
            <div className="text-center pt-2">
              <Button variant="outline" size="sm" onClick={() => setLimit((l) => l + 50)}>
                Load more
              </Button>
            </div>
          )}
        </div>
      )}

      <EventDetailDrawer event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
}
