import { api } from './client';
import type { DashboardEvent } from '@/types';

export const eventsApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return api.get<DashboardEvent[]>(`/events/${qs}`);
  },
  get: (id: string) => api.get<DashboardEvent>(`/events/${id}`),
};
