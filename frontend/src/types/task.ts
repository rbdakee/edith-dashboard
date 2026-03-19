export type TaskStatus = 'idea' | 'planned' | 'in_progress' | 'done' | 'archive';
export type SubStatus = 'working' | 'thinking' | 'blocked' | 'waiting' | 'delegated' | 'reviewing' | 'updating';
export type Priority = 'p0' | 'p1' | 'p2' | 'p3';

export interface Task {
  id: string;
  notion_id: string | null;
  title: string;
  description: string;
  status: TaskStatus;
  sub_status: SubStatus | null;
  priority: Priority;
  category: string;
  project_id: string | null;
  executor_agent: string | null;
  plan: string | null;
  context_file: string | null;
  parent_task_id: string | null;
  approved: boolean;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  last_status_change_at: string;
}
