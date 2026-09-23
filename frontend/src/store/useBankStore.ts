import { create } from 'zustand';
import { api } from '@/api/client';
import type { Dashboard } from '@/types/bank';

interface BankState {
  loading: boolean;
  error: string;
  dashboard: Dashboard | null;
  token: string;
  loadDashboard: () => Promise<void>;
  demoLogin: () => Promise<void>;
}

export const useBankStore = create<BankState>((set) => ({
  loading: false,
  error: '',
  dashboard: null,
  token: '',
  loadDashboard: async () => {
    set({ loading: true, error: '' });
    try {
      set({ dashboard: await api.dashboard() });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '数据加载失败' });
    } finally {
      set({ loading: false });
    }
  },
  demoLogin: async () => {
    const result = await api.demoLogin();
    set({ token: result.access });
  }
}));
