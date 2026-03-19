import { create } from 'zustand';

interface AuthStore {
  isAuthenticated: boolean;
  token: string;
  setAuthenticated: (v: boolean) => void;
  setToken: (t: string) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  isAuthenticated: false,
  token: '',
  setAuthenticated: (v) => set({ isAuthenticated: v }),
  setToken: (t) => set({ token: t }),
}));
