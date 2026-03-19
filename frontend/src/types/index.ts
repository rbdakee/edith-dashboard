export * from './task';
export * from './event';
export * from './agent';

export interface Project {
  id: string;
  notion_id: string | null;
  title: string;
  description: string;
  status: 'active' | 'on_hold' | 'completed' | 'archived';
  deadline: string | null;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  openclaw_session_id: string | null;
  agent_id: string;
  task_id: string | null;
  status: 'active' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  ended_at: string | null;
  context_snapshot: Record<string, unknown>;
  prompts: unknown[];
  actions: unknown[];
  outputs: unknown[];
  model: string;
}

export interface Comment {
  id: string;
  task_id: string | null;
  artifact_id: string | null;
  session_id: string | null;
  author: string;
  content: string;
  fragment_refs: Array<{
    file_path: string;
    start_line: number;
    end_line: number;
    text_selection: string;
  }> | null;
  routed_to: string | null;
  delivered: boolean;
  delivered_at: string | null;
  created_at: string;
}

export interface Artifact {
  id: string;
  task_id: string | null;
  session_id: string | null;
  filename: string;
  filepath: string;
  mime_type: string;
  size: number;
  content_preview: string | null;
  created_at: string;
  updated_at: string;
}
