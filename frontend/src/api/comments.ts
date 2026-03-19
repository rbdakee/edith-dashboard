import { api } from './client';
import type { Comment } from '@/types';

export const commentsApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return api.get<Comment[]>(`/comments/${qs}`);
  },
  get: (id: string) => api.get<Comment>(`/comments/${id}`),
  create: (data: { task_id?: string; content: string; routed_to?: string; fragment_refs?: unknown[] }) =>
    api.post<Comment>('/comments/', data),
};
