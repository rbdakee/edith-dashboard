import { useLocation } from 'react-router-dom';
import { Sun, Moon, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSettingsStore } from '@/stores/settingsStore';

const PAGE_TITLES: Record<string, string> = {
  '/overview': 'Overview',
  '/kanban': 'Kanban Board',
  '/tasks': 'Tasks',
  '/events': 'Events',
  '/sessions': 'Sessions',
  '/agents': 'Agents',
  '/files': 'Files',
  '/comments': 'Comments',
  '/timeline': 'Timeline',
  '/settings': 'Settings',
};

interface HeaderProps {
  wsConnected: boolean;
}

export function Header({ wsConnected }: HeaderProps) {
  const { pathname } = useLocation();
  const { theme, toggleTheme } = useSettingsStore();
  const title = PAGE_TITLES[pathname] ?? 'E.D.I.T.H. Ops';

  return (
    <header className="h-12 flex items-center justify-between px-4 border-b border-gray-700/50 bg-gray-900/80 backdrop-blur-sm">
      <h1 className="text-sm font-semibold text-gray-200">{title}</h1>
      <div className="flex items-center gap-3">
        {/* WebSocket connection indicator */}
        <div className="flex items-center gap-1.5">
          {wsConnected ? (
            <>
              <Wifi className="h-3.5 w-3.5 text-green-400" />
              <span className="text-xs text-green-400">Live</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 text-gray-500" />
              <span className="text-xs text-gray-500">Offline</span>
            </>
          )}
        </div>

        {/* Theme toggle */}
        <Button variant="ghost" size="icon" onClick={toggleTheme} className="h-7 w-7">
          {theme === 'dark' ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
        </Button>
      </div>
    </header>
  );
}
