import { useState } from 'react';
import { CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { tasksApi, type ApproveTaskPayload } from '@/api/tasks';
import { agentsApi } from '@/api/agents';
import { useQueryClient } from '@tanstack/react-query';
import type { Task } from '@/types';

interface ApproveButtonProps {
  task: Task;
  onApproved?: () => void;
}

function normalizePayload(payload: ApproveTaskPayload): ApproveTaskPayload {
  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => typeof value === 'string' && value.trim().length > 0)
  ) as ApproveTaskPayload;
}

function readDashboardApproval(task: Task): ApproveTaskPayload {
  const metadata = task.runtime_metadata;
  if (!metadata || typeof metadata !== 'object') {
    return {};
  }

  const approval = (metadata as Record<string, unknown>).dashboard_approval;
  if (!approval || typeof approval !== 'object') {
    return {};
  }

  const source = approval as Record<string, unknown>;
  const pick = (key: keyof ApproveTaskPayload): string | undefined => {
    const value = source[key];
    return typeof value === 'string' && value.trim() ? value.trim() : undefined;
  };

  return normalizePayload({
    report_back_session: pick('report_back_session'),
    report_back_channel: pick('report_back_channel'),
    report_back_chat_id: pick('report_back_chat_id'),
    main_session_id: pick('main_session_id'),
  });
}

async function buildApprovePayload(task: Task): Promise<ApproveTaskPayload> {
  const fromTask = readDashboardApproval(task);

  try {
    const mainAgent = await agentsApi.get('main');
    const ctx = mainAgent.current_session_context;

    const reportBackSession =
      (typeof ctx?.session_key === 'string' && ctx.session_key.trim())
      || (typeof ctx?.session_id === 'string' && ctx.session_id.trim())
      || (typeof mainAgent.current_session_id === 'string' && mainAgent.current_session_id.trim())
      || fromTask.report_back_session;

    const reportBackChannel =
      (typeof ctx?.channel === 'string' && ctx.channel.trim())
      || fromTask.report_back_channel;

    const reportBackChatId = reportBackSession?.startsWith('agent:main:telegram:direct:')
      ? reportBackSession.split(':').pop()
      : fromTask.report_back_chat_id;

    const mainSessionId =
      (typeof ctx?.session_id === 'string' && ctx.session_id.trim())
      || (typeof mainAgent.current_session_id === 'string' && mainAgent.current_session_id.startsWith('ses_') ? mainAgent.current_session_id : undefined)
      || fromTask.main_session_id;

    const payload = normalizePayload({
      report_back_session: reportBackSession,
      report_back_channel: reportBackChannel,
      report_back_chat_id: reportBackChatId,
      main_session_id: mainSessionId,
    });

    if (Object.keys(payload).length > 0) {
      return payload;
    }

    const agents = await agentsApi.list();
    const mainFromList = agents.find((agent) => agent.id === 'main');
    const listCtx = mainFromList?.current_session_context;
    const listSession =
      (typeof listCtx?.session_key === 'string' && listCtx.session_key.trim())
      || (typeof listCtx?.session_id === 'string' && listCtx.session_id.trim())
      || (typeof mainFromList?.current_session_id === 'string' && mainFromList.current_session_id.trim())
      || fromTask.report_back_session;

    const fromList = normalizePayload({
      report_back_session: listSession,
      report_back_channel: (typeof listCtx?.channel === 'string' && listCtx.channel.trim()) || fromTask.report_back_channel,
      report_back_chat_id: listSession?.startsWith('agent:main:telegram:direct:')
        ? listSession.split(':').pop()
        : fromTask.report_back_chat_id,
      main_session_id:
        (typeof listCtx?.session_id === 'string' && listCtx.session_id.trim())
        || (typeof mainFromList?.current_session_id === 'string' && mainFromList.current_session_id.startsWith('ses_') ? mainFromList.current_session_id : undefined)
        || fromTask.main_session_id,
    });

    return Object.keys(fromList).length > 0 ? fromList : fromTask;
  } catch {
    return fromTask;
  }
}

export function ApproveButton({ task, onApproved }: ApproveButtonProps) {
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
      const payload = await buildApprovePayload(task);
      await tasksApi.approve(task.id, payload);
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
      title={`Approve: ${task.title}`}
      className="border-green-500/50 text-green-400 hover:bg-green-500/10"
    >
      <CheckCircle className="h-3 w-3" />
      Approve
    </Button>
  );
}
