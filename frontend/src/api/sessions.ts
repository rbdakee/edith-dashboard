import { api } from './client';
import type { Session } from '@/types';

export const sessionsApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return api.get<Session[]>(`/sessions/${qs}`);
  },
  get: (id: string) => api.get<Session>(`/sessions/${id}`),
};
