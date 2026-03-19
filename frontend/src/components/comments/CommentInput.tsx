import { useState, FormEvent } from 'react';
import { Send, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { commentsApi } from '@/api/comments';
import { useQueryClient } from '@tanstack/react-query';

interface CommentInputProps {
  taskId: string;
  onSubmitted?: () => void;
}

// Agent options are now dynamic from agentStore
import { useAgentStore } from '@/stores/agentStore';

export function CommentInput({ taskId, onSubmitted }: CommentInputProps) {
  const [content, setContent] = useState('');
  const [routedTo, setRoutedTo] = useState('');
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();
  const { agents } = useAgentStore();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setLoading(true);
    try {
      await commentsApi.create({
        task_id: taskId,
        content,
        routed_to: routedTo || undefined,
      });
      setContent('');
      setRoutedTo('');
      await queryClient.invalidateQueries({ queryKey: ['comments', taskId] });
      onSubmitted?.();
    } catch (err) {
      console.error('Comment failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex items-start gap-1.5 text-xs text-gray-500 bg-gray-800/50 rounded px-2 py-1.5">
        <Info className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-blue-400/70" />
        <span>Comments routed to an agent are delivered as pickup files on their next session boot.</span>
      </div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Add a comment or instruction for an agent..."
        className="w-full min-h-[80px] resize-none rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
      />
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <Label className="text-xs text-gray-500 mb-1 block">Route to agent (optional)</Label>
          <Select value={routedTo} onValueChange={setRoutedTo}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="Select agent..." />
            </SelectTrigger>
            <SelectContent>
              {agents.map((agent) => (
                <SelectItem key={agent.id} value={agent.id}>{agent.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button type="submit" size="sm" disabled={loading || !content.trim()} className="mt-5">
          <Send className="h-3.5 w-3.5 mr-1" />
          Send
        </Button>
      </div>
    </form>
  );
}
