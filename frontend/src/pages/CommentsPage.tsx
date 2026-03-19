import { useQuery } from '@tanstack/react-query';
import { MessageSquare, CheckCircle2, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { MarkdownRenderer } from '@/components/shared/MarkdownRenderer';
import { commentsApi } from '@/api/comments';
import { cn } from '@/lib/utils';

export function CommentsPage() {
  const { data: comments = [], isLoading } = useQuery({
    queryKey: ['comments'],
    queryFn: () => commentsApi.list(),
    refetchInterval: 15_000,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <MessageSquare className="h-5 w-5 text-blue-400" />
        <h2 className="text-lg font-semibold text-gray-100">Comments</h2>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-lg bg-gray-800 animate-pulse" />)}
        </div>
      ) : comments.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No comments yet</p>
        </div>
      ) : (
        <div className="space-y-3">
          {comments.map((comment) => (
            <Card key={comment.id}>
              <CardContent className="py-3 px-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <AgentBadge agentId={comment.author} />
                    {comment.routed_to && (
                      <>
                        <span className="text-xs text-gray-500">→</span>
                        <AgentBadge agentId={comment.routed_to} />
                      </>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {comment.delivered ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-green-400" title="Delivered" />
                    ) : (
                      <Clock className="h-3.5 w-3.5 text-gray-500" title="Pending" />
                    )}
                    <TimestampLabel dateStr={comment.created_at} />
                  </div>
                </div>
                <MarkdownRenderer content={comment.content} />
                {comment.task_id && (
                  <div className="mt-2 text-xs text-gray-500">
                    Task: <span className="font-mono text-blue-400">{comment.task_id.slice(0, 8)}</span>
                  </div>
                )}
                {comment.fragment_refs && comment.fragment_refs.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {comment.fragment_refs.map((ref, i) => (
                      <div key={i} className={cn('text-xs bg-gray-800 rounded px-2 py-1 border-l-2 border-blue-500/50')}>
                        <span className="text-gray-400">{ref.file_path}</span>
                        <span className="text-gray-500 ml-2">L{ref.start_line}–{ref.end_line}</span>
                        {ref.text_selection && (
                          <div className="text-gray-500 font-mono mt-0.5 truncate">{ref.text_selection}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
