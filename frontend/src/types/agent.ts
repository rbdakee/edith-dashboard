export type AgentStatus = 'idle' | 'active' | 'busy';

export interface AgentSessionContext {
  source_kind?: string | null;
  channel?: string | null;
  session_key?: string | null;
  session_id?: string | null;
}

export interface Agent {
  id: string;
  name: string;
  model: string;
  status: AgentStatus;
  current_task_id: string | null;
  current_session_id: string | null;
  current_session_context?: AgentSessionContext | null;
  skills: string[];
  last_active_at: string | null;
}
