import { useQuery } from '@tanstack/react-query';
import { GitBranch } from 'lucide-react';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { eventsApi } from '@/api/events';
import { EVENT_TYPE_COLORS } from '@/lib/constants';
import { formatDate } from '@/lib/format';
import { cn } from '@/lib/utils';
import { parseISO } from 'date-fns';

export function TimelinePage() {
  const { data: events = [], isLoading } = useQuery({
    queryKey: ['events', { limit: '200' }],
    queryFn: () => eventsApi.list({ limit: '200' }),
    refetchInterval: 15_000,
  });

  // Group events by date
  const grouped = events.reduce<Record<string, typeof events>>((acc, event) => {
    const date = formatDate(event.timestamp);
    if (!acc[date]) acc[date] = [];
    acc[date].push(event);
    return acc;
  }, {});

  const dates = Object.keys(grouped).sort((a, b) => {
    try {
      return parseISO(b).getTime() - parseISO(a).getTime();
    } catch {
      return 0;
    }
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <GitBranch className="h-5 w-5 text-blue-400" />
        <h2 className="text-lg font-semibold text-gray-100">Timeline</h2>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i}>
              <div className="h-4 w-24 bg-gray-800 rounded animate-pulse mb-3" />
              <div className="space-y-2">
                {[1, 2, 3].map((j) => <div key={j} className="h-12 bg-gray-800 rounded animate-pulse" />)}
              </div>
            </div>
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <GitBranch className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No events to display</p>
        </div>
      ) : (
        <div className="space-y-6">
          {dates.map((date) => (
            <div key={date}>
              <div className="flex items-center gap-3 mb-3">
                <div className="h-px flex-1 bg-gray-700" />
                <span className="text-xs font-medium text-gray-400 px-2">{date}</span>
                <div className="h-px flex-1 bg-gray-700" />
              </div>
              <div className="relative">
                <div className="absolute left-3 top-0 bottom-0 w-px bg-gray-700" />
                <div className="space-y-2">
                  {grouped[date].map((event) => (
                    <div key={event.id} className="flex items-start gap-4 pl-8 relative">
                      <div className="absolute left-2.5 top-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 border-2 border-gray-900" />
                      <div className="flex-1 min-w-0 pb-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={cn('text-xs font-mono font-medium', EVENT_TYPE_COLORS[event.type] ?? 'text-gray-300')}>
                            {event.type}
                          </span>
                          <span className="text-sm text-gray-300 flex-1 truncate">{event.title}</span>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          {event.agent_id && <AgentBadge agentId={event.agent_id} />}
                          <TimestampLabel dateStr={event.timestamp} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
