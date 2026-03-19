import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Kanban, ListTodo, Activity, Terminal,
  Bot, FolderOpen, MessageSquare, GitBranch, Settings, ChevronLeft, ChevronRight, Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSettingsStore } from '@/stores/settingsStore';
import { useAgentStore } from '@/stores/agentStore';
import { AGENT_STATUS_COLORS, AGENT_DOT_COLORS } from '@/lib/constants';

const NAV_ITEMS = [
  { path: '/overview', label: 'Overview', icon: LayoutDashboard },
  { path: '/kanban', label: 'Kanban', icon: Kanban },
  { path: '/tasks', label: 'Tasks', icon: ListTodo },
  { path: '/events', label: 'Events', icon: Activity },
  { path: '/sessions', label: 'Sessions', icon: Terminal },
  { path: '/agents', label: 'Agents', icon: Bot },
  { path: '/files', label: 'Files', icon: FolderOpen },
  { path: '/comments', label: 'Comments', icon: MessageSquare },
  { path: '/timeline', label: 'Timeline', icon: GitBranch },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const { sidebarCollapsed, setSidebarCollapsed } = useSettingsStore();
  const { agents } = useAgentStore();

  return (
    <aside
      className={cn(
        'flex flex-col h-full bg-gray-900 border-r border-gray-700/50 transition-all duration-200',
        sidebarCollapsed ? 'w-14' : 'w-56'
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-3 py-4 border-b border-gray-700/50">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
          <Zap className="h-4 w-4 text-blue-400" />
        </div>
        {!sidebarCollapsed && (
          <div>
            <div className="text-sm font-bold text-gray-100">E.D.I.T.H.</div>
            <div className="text-xs text-gray-500">Ops Dashboard</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-2 overflow-y-auto">
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 mx-1 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                  : 'text-gray-400 hover:bg-gray-700/50 hover:text-gray-200'
              )
            }
            title={sidebarCollapsed ? label : undefined}
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            {!sidebarCollapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Agent status indicators */}
      {!sidebarCollapsed && agents.length > 0 && (
        <div className="px-3 py-3 border-t border-gray-700/50">
          <div className="text-xs text-gray-500 mb-2 uppercase tracking-wider">Agents</div>
          {agents.map((agent) => (
            <div key={agent.id} className="flex items-center gap-2 py-1">
              <div
                className={cn(
                  'w-1.5 h-1.5 rounded-full flex-shrink-0',
                  AGENT_STATUS_COLORS[agent.status]
                )}
              />
              <span className="text-xs text-gray-400 truncate">{agent.name}</span>
              <span className={cn('ml-auto text-xs', AGENT_DOT_COLORS[agent.id]?.replace('bg-', 'text-')?.replace('-400', '-400') ?? 'text-gray-500')}>
                {agent.status}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        className="flex items-center justify-center p-3 text-gray-500 hover:text-gray-300 border-t border-gray-700/50 transition-colors"
      >
        {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </button>
    </aside>
  );
}
