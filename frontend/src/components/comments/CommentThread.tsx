import { useQuery } from '@tanstack/react-query';
import { MessageSquare, CheckCircle2, Clock } from 'lucide-react';
import { AgentBadge } from '@/components/shared/AgentBadge';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { MarkdownRenderer } from '@/components/shared/MarkdownRenderer';
import { CommentInput } from './CommentInput';
import { commentsApi } from '@/api/comments';

interface CommentThreadProps {
  taskId: string;
}

export function CommentThread({ taskId }: CommentThreadProps) {
  const { data: comments = [], isLoading } = useQuery({
    queryKey: ['comments', taskId],
    queryFn: () => commentsApi.list({ task_id: taskId }),
    refetchInterval: 15_000,
  });

  return (
    <div className="space-y-4">
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2].map((i) => <div key={i} className="h-16 rounded bg-gray-800 animate-pulse" />)}
        </div>
      ) : comments.length === 0 ? (
        <div className="text-center py-6 text-gray-500">
          <MessageSquare className="h-6 w-6 mx-auto mb-1 opacity-50" />
          <p className="text-sm">No comments yet</p>
        </div>
      ) : (
        <div className="space-y-3">
          {comments.map((comment) => (
            <div key={comment.id} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <AgentBadge agentId={comment.author} />
                  {comment.routed_to && (
                    <>
                      <span className="text-xs text-gray-500">→</span>
                      <AgentBadge agentId={comment.routed_to} />
                    </>
                  )}
                </div>
                <div className="flex items-center gap-1.5">
                  {comment.delivered ? (
                    <CheckCircle2 className="h-3 w-3 text-green-400" title="Delivered" />
                  ) : (
                    <Clock className="h-3 w-3 text-gray-500" title="Pending delivery" />
                  )}
                  <TimestampLabel dateStr={comment.created_at} />
                </div>
              </div>
              <MarkdownRenderer content={comment.content} />
            </div>
          ))}
        </div>
      )}

      <div className="border-t border-gray-700 pt-4">
        <CommentInput taskId={taskId} />
      </div>
    </div>
  );
}
