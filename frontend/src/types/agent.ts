export type AgentStatus = 'idle' | 'active' | 'busy';

export interface Agent {
  id: string;
  name: string;
  model: string;
  status: AgentStatus;
  current_task_id: string | null;
  current_session_id: string | null;
  skills: string[];
  last_active_at: string | null;
}
