export interface DashboardEvent {
  id: string;
  type: string;
  task_id: string | null;
  session_id: string | null;
  agent_id: string | null;
  source: 'hook' | 'watcher' | 'gateway' | 'user' | 'system';
  title: string;
  data: Record<string, unknown>;
  timestamp: string;
}
