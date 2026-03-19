import { useState, useEffect, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Loader2, Copy, CheckCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/api/client';

export function SetupPage() {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [copied, setCopied] = useState(false);
  const navigate = useNavigate();

  // Redirect to login if already configured
  useEffect(() => {
    api.get<{ configured: boolean }>('/auth/status').then((res) => {
      if (res.configured) navigate('/login');
    }).catch(() => {});
  }, [navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post<{ ok: boolean; ingest_api_key: string }>('/auth/setup', { password });
      setApiKey(res.ingest_api_key);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Setup failed');
    } finally {
      setLoading(false);
    }
  };

  const copyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (apiKey) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="w-full max-w-md">
          <div className="bg-gray-900 rounded-xl border border-gray-700 p-6 space-y-4">
            <div className="flex items-center gap-2 text-green-400">
              <CheckCheck className="h-5 w-5" />
              <h2 className="text-lg font-semibold">Setup Complete</h2>
            </div>
            <p className="text-gray-400 text-sm">
              Save your OpenClaw hook API key below. You'll need it to configure the webhook in OpenClaw.
            </p>
            <div className="space-y-2">
              <Label>Ingest API Key</Label>
              <div className="flex gap-2">
                <code className="flex-1 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-blue-300 font-mono break-all">
                  {apiKey}
                </code>
                <Button variant="outline" size="icon" onClick={copyKey}>
                  {copied ? <CheckCheck className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>
            <Button className="w-full" onClick={() => navigate('/login')}>
              Continue to Login
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center mb-4">
            <Zap className="h-6 w-6 text-blue-400" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100">First Time Setup</h1>
          <p className="text-gray-400 text-sm mt-1">Configure your E.D.I.T.H. Ops Dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-gray-900 rounded-xl border border-gray-700 p-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="password">Dashboard Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Choose a strong password"
              autoFocus
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm">Confirm Password</Label>
            <Input
              id="confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Confirm password"
              required
            />
          </div>

          {error && (
            <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Setting up...
              </>
            ) : (
              'Complete Setup'
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
