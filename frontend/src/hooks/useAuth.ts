import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/api/client';

export function useAuth() {
  const { isAuthenticated, setAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    api.get<{ ok: boolean }>('/auth/me')
      .then(() => setAuthenticated(true))
      .catch(() => {
        setAuthenticated(false);
        navigate('/login');
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { isAuthenticated };
}
