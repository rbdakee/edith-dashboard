import { useEffect, useState, useCallback } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { api } from '@/api/client';
import { useAuthStore } from '@/stores/authStore';
import { useAgentStore } from '@/stores/agentStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { agentsApi } from '@/api/agents';
import type { Agent, DashboardEvent, Task } from '@/types';

export function AppLayout() {
  const navigate = useNavigate();
  const { isAuthenticated, setAuthenticated, token, setToken } = useAuthStore();
  const { setAgents, updateAgent } = useAgentStore();
  const queryClient = useQueryClient();
  const [wsConnected, setWsConnected] = useState(false);

  // Auth check on mount: check setup status first, then auth
  useEffect(() => {
    api.get<{ configured: boolean }>('/auth/status')
      .then((res) => {
        if (!res.configured) {
          navigate('/setup');
          return;
        }
        // Setup done — check if logged in
        api.get<{ ok: boolean }>('/auth/me')
          .then(() => {
            setAuthenticated(true);
            api.get<{ token: string }>('/auth/ws-token')
              .then((r) => setToken(r.token))
              .catch(() => { /* WS stays offline, non-fatal */ });
          })
          .catch(() => navigate('/login'));
      })
      .catch(() => navigate('/login'));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load agents on mount
  useEffect(() => {
    if (isAuthenticated) {
      agentsApi.list()
        .then(setAgents)
        .catch(() => {/* agents endpoint may not be ready */});
    }
  }, [isAuthenticated, setAgents]);

  // Handle WebSocket messages — stable reference required to avoid reconnect loop
  const handleWsMessage = useCallback((msg: { type: string; payload: unknown }) => {
    if (msg.type === 'agent_state') {
      const agent = msg.payload as Agent;
      updateAgent(agent.id, agent);
    } else if (msg.type === 'task_update') {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    } else if (msg.type === 'event') {
      const event = msg.payload as DashboardEvent;
      queryClient.invalidateQueries({ queryKey: ['events'] });
      if (event.task_id) {
        queryClient.invalidateQueries({ queryKey: ['tasks', event.task_id] });
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { connected } = useWebSocket(token, handleWsMessage);

  useEffect(() => {
    setWsConnected(connected);
  }, [connected]);

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <div className="text-gray-400 text-sm">Checking authentication...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Header wsConnected={wsConnected} />
        <main className="flex-1 overflow-y-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
