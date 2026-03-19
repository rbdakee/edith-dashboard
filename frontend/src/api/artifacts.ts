import { api } from './client';
import type { Artifact } from '@/types';

export const artifactsApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return api.get<Artifact[]>(`/artifacts/${qs}`);
  },
  get: (id: string) => api.get<Artifact>(`/artifacts/${id}`),
};
