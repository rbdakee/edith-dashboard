import { useState, FormEvent } from 'react';
import { Plus, Loader2 } from 'lucide-react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { tasksApi } from '@/api/tasks';
import { useQueryClient } from '@tanstack/react-query';
import type { Priority } from '@/types';

interface SubTaskCreateButtonProps {
  parentTaskId: string;
}

export function SubTaskCreateButton({ parentTaskId }: SubTaskCreateButtonProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Priority>('p2');
  const [executorAgent, setExecutorAgent] = useState('');
  const queryClient = useQueryClient();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    try {
      await tasksApi.create({
        title,
        description,
        priority,
        status: 'planned',
        category: 'work',
        executor_agent: executorAgent || null,
        parent_task_id: parentTaskId,
      });
      await queryClient.invalidateQueries({ queryKey: ['tasks', { parent_task_id: parentTaskId }] });
      setOpen(false);
      setTitle('');
      setDescription('');
      setPriority('p2');
      setExecutorAgent('');
    } catch (err) {
      console.error('Create sub-task failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline" className="w-full h-8 text-xs border-dashed">
          <Plus className="h-3.5 w-3.5 mr-1" />
          Add Sub-Task
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Create Sub-Task</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="subtask-title">Title *</Label>
            <Input
              id="subtask-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Sub-task title"
              required
              autoFocus
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="subtask-desc">Description</Label>
            <textarea
              id="subtask-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              className="w-full min-h-[60px] resize-none rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Priority</Label>
              <Select value={priority} onValueChange={(v) => setPriority(v as Priority)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="p0">P0 — Critical</SelectItem>
                  <SelectItem value="p1">P1 — High</SelectItem>
                  <SelectItem value="p2">P2 — Medium</SelectItem>
                  <SelectItem value="p3">P3 — Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Agent</Label>
              <Select value={executorAgent || 'none'} onValueChange={(v) => setExecutorAgent(v === 'none' ? '' : v)}>
                <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="main">Main</SelectItem>
                  <SelectItem value="edith-dev">Dev</SelectItem>
                  <SelectItem value="edith-routine">Routine</SelectItem>
                  <SelectItem value="edith-analytics">Analytics</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" size="sm" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" size="sm" disabled={loading || !title.trim()}>
              {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : <Plus className="h-3.5 w-3.5 mr-1" />}
              Create
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
