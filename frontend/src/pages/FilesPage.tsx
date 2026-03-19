import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FolderOpen, File, FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { TimestampLabel } from '@/components/shared/TimestampLabel';
import { FileViewerPanel } from '@/components/artifacts/FileViewerPanel';
import { artifactsApi } from '@/api/artifacts';
import type { Artifact } from '@/types';

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
}

function getDir(filepath: string): string {
  const parts = filepath.replace(/\\/g, '/').split('/');
  parts.pop();
  return parts.join('/') || '/';
}

function FileIcon({ artifact }: { artifact: Artifact }) {
  const isText = artifact.mime_type.includes('text') || artifact.mime_type.includes('markdown');
  return isText
    ? <FileText className="h-4 w-4 text-blue-400 flex-shrink-0" />
    : <File className="h-4 w-4 text-gray-400 flex-shrink-0" />;
}

interface DirectoryGroupProps {
  dir: string;
  files: Artifact[];
  selectedId: string | null;
  onSelect: (a: Artifact) => void;
}

function DirectoryGroup({ dir, files, selectedId, onSelect }: DirectoryGroupProps) {
  const [open, setOpen] = useState(true);

  return (
    <div className="mb-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200 py-1 w-full text-left"
      >
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <FolderOpen className="h-3.5 w-3.5" />
        <span className="font-mono truncate">{dir}</span>
        <span className="ml-auto text-gray-600">{files.length}</span>
      </button>

      {open && (
        <div className="ml-5 space-y-1">
          {files.map((artifact) => (
            <Card
              key={artifact.id}
              className={`hover:border-gray-600 transition-colors cursor-pointer ${selectedId === artifact.id ? 'border-blue-500/60 bg-blue-500/5' : ''}`}
              onClick={() => onSelect(artifact)}
            >
              <CardContent className="py-2 px-3">
                <div className="flex items-center gap-2">
                  <FileIcon artifact={artifact} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-200 truncate">{artifact.filename}</span>
                      <span className="text-xs text-gray-500">{formatSize(artifact.size)}</span>
                    </div>
                    {artifact.content_preview && (
                      <div className="text-xs text-gray-500 mt-0.5 truncate">{artifact.content_preview}</div>
                    )}
                  </div>
                  <TimestampLabel dateStr={artifact.updated_at} className="flex-shrink-0 text-xs text-gray-600" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export function FilesPage() {
  const [selected, setSelected] = useState<Artifact | null>(null);

  const { data: artifacts = [], isLoading } = useQuery({
    queryKey: ['artifacts'],
    queryFn: () => artifactsApi.list(),
  });

  // Group by directory
  const grouped: Record<string, Artifact[]> = {};
  for (const a of artifacts) {
    const dir = getDir(a.filepath);
    if (!grouped[dir]) grouped[dir] = [];
    grouped[dir].push(a);
  }

  return (
    <div className="flex h-full gap-0">
      {/* Left: file tree */}
      <div className={`flex flex-col ${selected ? 'w-1/2' : 'w-full'} overflow-y-auto`}>
        <div className="flex items-center gap-2 mb-4">
          <FolderOpen className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-gray-100">Artifacts & Files</h2>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <div key={i} className="h-14 rounded-lg bg-gray-800 animate-pulse" />)}
          </div>
        ) : artifacts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FolderOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No artifacts yet</p>
            <p className="text-xs mt-1">Files created by agents will appear here</p>
          </div>
        ) : (
          Object.entries(grouped).map(([dir, files]) => (
            <DirectoryGroup
              key={dir}
              dir={dir}
              files={files}
              selectedId={selected?.id ?? null}
              onSelect={(a) => setSelected(selected?.id === a.id ? null : a)}
            />
          ))
        )}
      </div>

      {/* Right: file viewer */}
      {selected && (
        <div className="w-1/2 h-full border-l border-gray-700">
          <FileViewerPanel artifact={selected} onClose={() => setSelected(null)} />
        </div>
      )}
    </div>
  );
}
