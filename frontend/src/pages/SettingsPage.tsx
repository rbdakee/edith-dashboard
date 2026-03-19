import { useState } from 'react';
import { Settings, Sun, Moon, RefreshCw, Server, Key } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useSettingsStore } from '@/stores/settingsStore';
import { api } from '@/api/client';

export function SettingsPage() {
  const { theme, toggleTheme } = useSettingsStore();
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'done' | 'error'>('idle');

  const triggerSync = async () => {
    setSyncStatus('syncing');
    try {
      await api.post('/settings/sync');
      setSyncStatus('done');
      setTimeout(() => setSyncStatus('idle'), 3000);
    } catch {
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-2">
        <Settings className="h-5 w-5 text-blue-400" />
        <h2 className="text-lg font-semibold text-gray-100">Settings</h2>
      </div>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Appearance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-200">Theme</div>
              <div className="text-xs text-gray-500">Current: {theme}</div>
            </div>
            <Button variant="outline" size="sm" onClick={toggleTheme}>
              {theme === 'dark' ? (
                <><Sun className="h-4 w-4 mr-2" />Switch to Light</>
              ) : (
                <><Moon className="h-4 w-4 mr-2" />Switch to Dark</>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Notion Sync */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <RefreshCw className="h-4 w-4 text-blue-400" />
            Notion Sync
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-200">Manual Sync</div>
              <div className="text-xs text-gray-500">Pull tasks from Notion into Dashboard</div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={triggerSync}
              disabled={syncStatus === 'syncing'}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${syncStatus === 'syncing' ? 'animate-spin' : ''}`} />
              {syncStatus === 'idle' && 'Sync Now'}
              {syncStatus === 'syncing' && 'Syncing...'}
              {syncStatus === 'done' && 'Done!'}
              {syncStatus === 'error' && 'Failed'}
            </Button>
          </div>
          <Separator />
          <div className="text-xs text-gray-500 space-y-1">
            <div>Auto-sync interval: 60 seconds</div>
            <div>Status mapping: Backlog↔Idea, Todo↔Planned, In Progress↔In Progress, Done↔Done, Cancelled↔Archive</div>
          </div>
        </CardContent>
      </Card>

      {/* OpenClaw Gateway */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Server className="h-4 w-4 text-blue-400" />
            OpenClaw Gateway
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-200">Gateway URL</div>
            <code className="text-xs text-blue-300 bg-gray-800 px-2 py-1 rounded">http://localhost:18789</code>
          </div>
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-200">Dashboard API</div>
            <code className="text-xs text-blue-300 bg-gray-800 px-2 py-1 rounded">http://localhost:18790</code>
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Key className="h-4 w-4 text-blue-400" />
            Security
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-gray-500">
            Authentication uses bcrypt-hashed passwords with JWT tokens (24h access, 30d refresh) stored in httpOnly cookies.
            The ingest API key for OpenClaw webhooks is generated during setup.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
