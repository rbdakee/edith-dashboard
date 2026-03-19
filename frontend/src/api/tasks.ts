import { api } from './client';
import type { Task } from '@/types';

type TaskListParams = Record<string, string | boolean | null | undefined>;

export const tasksApi = {
  list: (params?: TaskListParams) => {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params ?? {})) {
      if (value === undefined || value === null || value === '') continue;
      search.set(key, String(value));
    }
    const qs = search.size > 0 ? `?${search.toString()}` : '';
    return api.get<Task[]>(`/tasks/${qs}`);
  },
  get: (id: string) => api.get<Task>(`/tasks/${id}`),
  create: (data: Partial<Task>) => api.post<Task>('/tasks/', data),
  update: (id: string, data: Partial<Task>) => api.patch<Task>(`/tasks/${id}`, data),
  delete: (id: string) => api.delete<void>(`/tasks/${id}`),
  approve: (id: string) => api.post<Task>(`/tasks/${id}/approve`),
};
