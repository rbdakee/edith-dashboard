import { useState } from 'react';
import { CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { tasksApi } from '@/api/tasks';
import { useQueryClient } from '@tanstack/react-query';

interface ApproveButtonProps {
  taskId: string;
  taskTitle: string;
  onApproved?: () => void;
}

export function ApproveButton({ taskId, taskTitle, onApproved }: ApproveButtonProps) {
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const queryClient = useQueryClient();

  const handleClick = async () => {
    if (!confirmed) {
      setConfirmed(true);
      return;
    }

    setLoading(true);
    try {
      await tasksApi.approve(taskId);
      await queryClient.invalidateQueries({ queryKey: ['tasks'] });
      onApproved?.();
    } catch (err) {
      console.error('Approve failed:', err);
    } finally {
      setLoading(false);
      setConfirmed(false);
    }
  };

  if (loading) {
    return (
      <Button size="sm" variant="success" disabled>
        <Loader2 className="h-3 w-3 animate-spin" />
        Approving...
      </Button>
    );
  }

  if (confirmed) {
    return (
      <div className="flex gap-1">
        <Button size="sm" variant="success" onClick={handleClick}>
          <CheckCircle className="h-3 w-3" />
          Confirm
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setConfirmed(false)}>
          Cancel
        </Button>
      </div>
    );
  }

  return (
    <Button
      size="sm"
      variant="outline"
      onClick={handleClick}
      title={`Approve: ${taskTitle}`}
      className="border-green-500/50 text-green-400 hover:bg-green-500/10"
    >
      <CheckCircle className="h-3 w-3" />
      Approve
    </Button>
  );
}
