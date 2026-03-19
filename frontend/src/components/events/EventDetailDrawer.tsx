import { useQuery } from '@tanstack/react-query';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { MarkdownRenderer } from '@/components/shared/MarkdownRenderer';
import { api } from '@/api/client';
import { EVENT_TYPE_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { DashboardEvent } from '@/types';

interface EventDetailDrawerProps {
  event: DashboardEvent | null;
  onClose: () => void;
}

function DiffViewer({ diff }: { diff: string }) {
  return (
    <div className="font-mono text-xs bg-gray-900 border border-gray-700 rounded p-2 overflow-x-auto max-h-80 overflow-y-auto">
      {diff.split('\n').map((line, i) => (
        <div
          key={i}
          className={cn(
            'leading-5 px-1',
            line.startsWith('+') && !line.startsWith('+++') && 'text-green-400 bg-green-950/30',
            line.startsWith('-') && !line.startsWith('---') && 'text-red-400 bg-red-950/30',
            line.startsWith('@@') && 'text-blue-400',
            !line.match(/^[+\-@]/) && 'text-gray-500',
          )}
        >
          {line || ' '}
        </div>
      ))}
    </div>
  );
}

function FileContentViewer({ path }: { path: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['file-content', path],
    queryFn: () => api.get<{ content: string; mime_type: string; filename: string }>(
      `/files/content?path=${encodeURIComponent(path)}`
    ),
    enabled: !!path,
    staleTime: 30_000,
  });

  if (isLoading) return <div className="text-xs text-gray-500 py-2">Loading file...</div>;
  if (error) return <div className="text-xs text-red-400 py-2">Could not load file</div>;
  if (!data) return null;

  const isMd = data.mime_type === 'text/markdown' || data.filename.endsWith('.md');

  return (
    <div>
      <div className="text-xs text-gray-500 mb-1 font-mono">{data.filename}</div>
      {isMd ? (
        <div className="max-h-72 overflow-y-auto border border-gray-700 rounded p-3">
          <MarkdownRenderer content={data.content} />
        </div>
      ) : (
        <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap bg-gray-900 border border-gray-700 rounded p-2 max-h-72 overflow-y-auto">
          {data.content}
        </pre>
      )}
    </div>
  );
}

function isFileEvent(event: DashboardEvent): boolean {
  return event.type.startsWith('file.') || event.type.startsWith('memory.');
}

export function EventDetailDrawer({ event, onClose }: EventDetailDrawerProps) {
  if (!event) return null;

  const filePath = event.data?.path as string | undefined;
  const diff = event.data?.diff as string | undefined;
  const contentSnapshot = event.data?.content_snapshot as string | undefined;

  return (
    <Sheet open={!!event} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent side="right" className="w-[500px] overflow-y-auto bg-gray-900 border-gray-700">
        <SheetHeader className="mb-4">
          <SheetTitle className="flex items-center gap-2">
            <span className={cn('font-mono text-sm', EVENT_TYPE_COLORS[event.type] ?? 'text-gray-300')}>
              {event.type}
            </span>
          </SheetTitle>
        </SheetHeader>

        <div className="space-y-4">
          {/* Title */}
          <p className="text-sm text-gray-200">{event.title}</p>

          {/* Meta */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {event.agent_id && <AgentBadge agentId={event.agent_id} />}
            <span className="text-gray-600 bg-gray-800 px-1.5 py-0.5 rounded">{event.source}</span>
            {event.task_id && (
              <span className="text-gray-500 font-mono">task:{event.task_id.slice(0, 8)}</span>
            )}
            {event.session_id && (
              <span className="text-gray-500 font-mono">session:{event.session_id.slice(0, 8)}</span>
            )}
            <TimestampLabel dateStr={event.timestamp} className="text-gray-500" />
          </div>

          {/* File diff or snapshot */}
          {isFileEvent(event) && filePath && (
            <div className="space-y-2">
              <div className="text-xs text-gray-500 font-mono truncate">{filePath}</div>
              {diff ? (
                <div>
                  <div className="text-xs text-gray-400 mb-1">Changes</div>
                  <DiffViewer diff={diff} />
                </div>
              ) : contentSnapshot ? (
                <div>
                  <div className="text-xs text-gray-400 mb-1">Content snapshot</div>
                  <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap bg-gray-900 border border-gray-700 rounded p-2 max-h-60 overflow-y-auto">
                    {contentSnapshot}
                  </pre>
                </div>
              ) : null}

              {/* Live file viewer */}
              <div>
                <div className="text-xs text-gray-400 mb-1">Current file</div>
                <FileContentViewer path={filePath} />
              </div>
            </div>
          )}

          {/* Raw data (collapsible) */}
          <details className="group">
            <summary className="text-xs text-gray-500 cursor-pointer select-none hover:text-gray-300">
              Raw data
            </summary>
            <pre className="mt-1 text-xs text-gray-400 bg-gray-950 border border-gray-700 rounded p-2 overflow-x-auto max-h-64 overflow-y-auto">
              {JSON.stringify(event.data, null, 2)}
            </pre>
          </details>
        </div>
      </SheetContent>
    </Sheet>
  );
}
