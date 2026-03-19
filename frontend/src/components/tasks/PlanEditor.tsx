import { useState } from 'react';
import { Eye, Edit3, Save, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MarkdownRenderer } from '@/components/shared/MarkdownRenderer';
import { tasksApi } from '@/api/tasks';
import { useQueryClient } from '@tanstack/react-query';

interface PlanEditorProps {
  taskId: string;
  plan: string | null;
}

export function PlanEditor({ taskId, plan }: PlanEditorProps) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(plan ?? '');
  const [saving, setSaving] = useState(false);
  const queryClient = useQueryClient();

  const handleSave = async () => {
    setSaving(true);
    try {
      await tasksApi.update(taskId, { plan: value });
      await queryClient.invalidateQueries({ queryKey: ['tasks', taskId] });
      setEditing(false);
    } catch (err) {
      console.error('Save failed:', err);
    } finally {
      setSaving(false);
    }
  };

  if (editing) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Editing plan (Markdown)</span>
          <div className="flex gap-1">
            <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setValue(plan ?? ''); }}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : <Save className="h-3.5 w-3.5 mr-1" />}
              Save
            </Button>
          </div>
        </div>
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="w-full min-h-[200px] resize-y rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 font-mono"
          placeholder="Write the task plan in Markdown..."
        />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">Task Plan</span>
        <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>
          <Edit3 className="h-3.5 w-3.5 mr-1" />
          Edit
        </Button>
      </div>
      {value ? (
        <MarkdownRenderer content={value} />
      ) : (
        <div className="text-center py-6 text-gray-500">
          <Eye className="h-6 w-6 mx-auto mb-1 opacity-50" />
          <p className="text-sm">No plan yet</p>
          <Button size="sm" variant="ghost" className="mt-2" onClick={() => setEditing(true)}>
            Write a plan
          </Button>
        </div>
      )}
    </div>
  );
}
