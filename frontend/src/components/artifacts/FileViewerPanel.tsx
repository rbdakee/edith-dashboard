import { useQuery } from '@tanstack/react-query';
import { X, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MarkdownRenderer } from '@/components/shared/MarkdownRenderer';
import { api } from '@/api/client';
import type { FileEntry } from '@/api/files';

interface FileViewerPanelProps {
  file: FileEntry;
  onClose: () => void;
}

export function FileViewerPanel({ file, onClose }: FileViewerPanelProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['file-content', file.path],
    queryFn: () => api.get<{ content: string; mime_type: string; filename: string }>(
      `/files/content?path=${encodeURIComponent(file.path)}`
    ),
    staleTime: 30_000,
  });

  const isMd = file.mime_type === 'text/markdown' || file.name.endsWith('.md');

  return (
    <div className="flex flex-col h-full bg-gray-900 border-l border-gray-700">
      <div className="flex items-center gap-2 p-3 border-b border-gray-700 flex-shrink-0">
        <FileText className="h-4 w-4 text-blue-400 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-200 truncate">{file.name}</div>
          <div className="text-xs text-gray-500 truncate">{file.path}</div>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-7 w-7 flex-shrink-0">
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && <div className="text-xs text-gray-500 animate-pulse">Loading...</div>}
        {error && <div className="text-xs text-red-400">Could not load file content</div>}
        {data && (
          isMd ? (
            <MarkdownRenderer content={data.content} />
          ) : (
            <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap leading-5">
              {data.content}
            </pre>
          )
        )}
      </div>
    </div>
  );
}
