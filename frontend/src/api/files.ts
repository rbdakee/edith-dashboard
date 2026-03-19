import { api } from './client';

export interface FileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number | null;
  mime_type: string | null;
}

export interface FileListResponse {
  path: string | null;
  parent: string | null;
  roots: string[];
  entries: FileEntry[];
}

export const filesApi = {
  roots: () => api.get<{ roots: string[] }>(`/files/roots`),
  list: (path?: string) => {
    const qs = path ? `?path=${encodeURIComponent(path)}` : '';
    return api.get<FileListResponse>(`/files/list${qs}`);
  },
  content: (path: string) =>
    api.get<{ content: string; mime_type: string; filename: string; path: string }>(
      `/files/content?path=${encodeURIComponent(path)}`
    ),
};
