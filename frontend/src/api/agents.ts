import { api } from './client';
import type { Agent } from '@/types';

export const agentsApi = {
  list: () => api.get<Agent[]>('/agents/'),
  get: (id: string) => api.get<Agent>(`/agents/${id}`),
};
