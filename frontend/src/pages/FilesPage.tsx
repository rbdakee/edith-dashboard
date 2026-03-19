import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FolderOpen,
  File,
  FileText,
  ArrowUp,
  HardDrive,
  Folder,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { FileViewerPanel } from '@/components/artifacts/FileViewerPanel';
import { filesApi, type FileEntry } from '@/api/files';

function formatSize(bytes: number | null): string {
  if (bytes == null) return '-';
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
}

function EntryIcon({ entry }: { entry: FileEntry }) {
  if (entry.is_dir) return <Folder className="h-4 w-4 text-yellow-400 flex-shrink-0" />;
  const isText = String(entry.mime_type ?? '').includes('text') || entry.name.endsWith('.md');
  return isText
    ? <FileText className="h-4 w-4 text-blue-400 flex-shrink-0" />
    : <File className="h-4 w-4 text-gray-400 flex-shrink-0" />;
}

export function FilesPage() {
  const [currentPath, setCurrentPath] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileEntry | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['files-list', currentPath],
    queryFn: () => filesApi.list(currentPath ?? undefined),
  });

  const roots = data?.roots ?? [];
  const entries = data?.entries ?? [];
  const parent = data?.parent ?? null;
  const resolvedPath = data?.path ?? null;

  const pathSegments = useMemo(() => {
    if (!resolvedPath) return [];
    return resolvedPath.replace(/\\/g, '/').split('/').filter(Boolean);
  }, [resolvedPath]);

  return (
    <div className="flex h-full gap-0">
      {/* Left: file manager */}
      <div className={`flex flex-col ${selectedFile ? 'w-1/2' : 'w-full'} overflow-y-auto`}>
        <div className="flex items-center gap-2 mb-4">
          <FolderOpen className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-gray-100">Files</h2>
        </div>

        {/* Roots */}
        {roots.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {roots.map((root) => (
              <button
                key={root}
                onClick={() => {
                  setCurrentPath(root);
                  setSelectedFile(null);
                }}
                className={`px-2.5 py-1 rounded text-xs border transition-colors ${resolvedPath?.toLowerCase().startsWith(root.toLowerCase())
                  ? 'border-blue-500/50 bg-blue-500/10 text-blue-300'
                  : 'border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600'
                  }`}
              >
                <span className="inline-flex items-center gap-1.5">
                  <HardDrive className="h-3.5 w-3.5" />
                  <span className="font-mono">{root}</span>
                </span>
              </button>
            ))}
          </div>
        )}

        {/* Breadcrumb */}
        {resolvedPath && (
          <div className="mb-3 text-xs text-gray-500 font-mono break-all">/{pathSegments.join('/')}</div>
        )}

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <div key={i} className="h-12 rounded-lg bg-gray-800 animate-pulse" />)}
          </div>
        ) : !resolvedPath ? (
          <div className="text-center py-12 text-gray-500">
            <FolderOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No allowed roots configured</p>
          </div>
        ) : (
          <div className="space-y-1">
            {parent && (
              <button
                onClick={() => {
                  setCurrentPath(parent);
                  setSelectedFile(null);
                }}
                className="w-full text-left px-3 py-2 rounded hover:bg-gray-800/60 border border-transparent hover:border-gray-700 transition-colors"
              >
                <span className="inline-flex items-center gap-2 text-gray-300 text-sm">
                  <ArrowUp className="h-4 w-4" />
                  ..
                </span>
              </button>
            )}

            {entries.map((entry) => (
              <Card
                key={entry.path}
                className={`hover:border-gray-600 transition-colors cursor-pointer ${selectedFile?.path === entry.path ? 'border-blue-500/60 bg-blue-500/5' : ''}`}
                onClick={() => {
                  if (entry.is_dir) {
                    setCurrentPath(entry.path);
                    setSelectedFile(null);
                  } else {
                    setSelectedFile(selectedFile?.path === entry.path ? null : entry);
                  }
                }}
              >
                <CardContent className="py-2 px-3">
                  <div className="flex items-center gap-2">
                    <EntryIcon entry={entry} />
                    <span className="text-sm text-gray-200 truncate flex-1">{entry.name}</span>
                    {!entry.is_dir && (
                      <span className="text-xs text-gray-500">{formatSize(entry.size)}</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}

            {entries.length === 0 && (
              <div className="text-xs text-gray-500 px-1 py-3">Directory is empty</div>
            )}
          </div>
        )}
      </div>

      {/* Right: file viewer */}
      {selectedFile && (
        <div className="w-1/2 h-full border-l border-gray-700">
          <FileViewerPanel file={selectedFile} onClose={() => setSelectedFile(null)} />
        </div>
      )}
    </div>
  );
}
