import { create } from 'zustand';
import { api } from '@/api/client';
import type { Dashboard, PaperSnapshot } from '@/types/bank';

interface BankState {
  loading: boolean;
  error: string;
  dashboard: Dashboard | null;
  token: string;
  paper: PaperSnapshot | null;
  paperLoading: boolean;
  paperError: string;
  loadDashboard: () => Promise<void>;
  demoLogin: () => Promise<void>;
  generatePaper: (difficulty: string, amount: number) => Promise<void>;
  loadPaper: (number: number) => Promise<void>;
}

export const useBankStore = create<BankState>((set) => ({
  loading: false,
  error: '',
  dashboard: null,
  token: '',
  paper: null,
  paperLoading: false,
  paperError: '',
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
  },
  generatePaper: async (difficulty, amount) => {
    set({ paperLoading: true, paperError: '' });
    try {
      set({ paper: await api.generatePaper(difficulty, amount) });
    } catch (error) {
      set({ paperError: error instanceof Error ? error.message : '试卷生成失败' });
    } finally {
      set({ paperLoading: false });
    }
  },
  loadPaper: async (number) => {
    set({ paperLoading: true, paperError: '' });
    try {
      set({ paper: await api.getPaper(number) });
    } catch {
      set({ paperError: `未找到编号为 ${number} 的试卷` });
    } finally {
      set({ paperLoading: false });
    }
  }
}));
