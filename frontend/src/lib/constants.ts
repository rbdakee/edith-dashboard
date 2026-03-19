import type { TaskStatus, Priority, AgentStatus } from '@/types';

export const AGENT_COLORS: Record<string, string> = {
  main: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  'edith-dev': 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  'edith-routine': 'bg-green-500/20 text-green-300 border-green-500/30',
  'edith-analytics': 'bg-orange-500/20 text-orange-300 border-orange-500/30',
};

export const AGENT_DOT_COLORS: Record<string, string> = {
  main: 'bg-purple-400',
  'edith-dev': 'bg-blue-400',
  'edith-routine': 'bg-green-400',
  'edith-analytics': 'bg-orange-400',
};

export const STATUS_COLORS: Record<TaskStatus, string> = {
  idea: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  planned: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  in_progress: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  done: 'bg-green-500/20 text-green-300 border-green-500/30',
  archive: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

export const STATUS_LABELS: Record<TaskStatus, string> = {
  idea: 'Idea',
  planned: 'Planned',
  in_progress: 'In Progress',
  done: 'Done',
  archive: 'Archive',
};

export const PRIORITY_COLORS: Record<Priority, string> = {
  p0: 'bg-red-500/20 text-red-300 border-red-500/30',
  p1: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  p2: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  p3: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

export const PRIORITY_LABELS: Record<Priority, string> = {
  p0: 'P0',
  p1: 'P1',
  p2: 'P2',
  p3: 'P3',
};

export const AGENT_STATUS_COLORS: Record<AgentStatus, string> = {
  idle: 'bg-gray-400',
  active: 'bg-green-400',
  busy: 'bg-amber-400',
};

export const SUB_STATUS_COLORS: Record<string, string> = {
  working: 'bg-blue-500/20 text-blue-300',
  thinking: 'bg-violet-500/20 text-violet-300',
  blocked: 'bg-red-500/20 text-red-300',
  waiting: 'bg-gray-500/20 text-gray-400',
  delegated: 'bg-cyan-500/20 text-cyan-300',
  reviewing: 'bg-amber-500/20 text-amber-300',
  updating: 'bg-teal-500/20 text-teal-300',
};

// AGENTS constant removed — agent list is now dynamic from backend API via agentStore.
// Use useAgentStore().agents instead of this static list.

export const EVENT_TYPE_COLORS: Record<string, string> = {
  'task.created': 'text-blue-400',
  'task.status_changed': 'text-amber-400',
  'task.approved': 'text-green-400',
  'task.assigned': 'text-purple-400',
  'task.comment_added': 'text-cyan-400',
  'session.started': 'text-blue-300',
  'session.completed': 'text-green-300',
  'session.failed': 'text-red-400',
  'agent.status_changed': 'text-violet-400',
  'agent.delegation_sent': 'text-orange-400',
  'agent.error': 'text-red-400',
  'memory.updated': 'text-teal-400',
  'file.created': 'text-indigo-400',
  'system.cron_executed': 'text-gray-400',
  'system.hook_received': 'text-gray-400',
};
