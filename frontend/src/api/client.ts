import type { Dashboard, Paper, PaperSummary } from '@/types/bank';

const API_BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers ?? {}
    },
    ...init
  });

  if (!response.ok) {
    let message = `请求失败：${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) {
        message = data.detail;
      }
    } catch {
      // 响应体不是 JSON 时保留状态码错误
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; service: string }>('/health/'),
  dashboard: () => request<Dashboard>('/dashboard/'),
  generatePaper: (difficulty: string, amount: number) =>
    request<{ paper: Paper }>('/papers/generate/', {
      method: 'POST',
      body: JSON.stringify({ difficulty, amount })
    }),
  getPaper: (paperNo: number) =>
    request<{ paper: Paper }>(`/papers/${paperNo}/`),
  paperHistory: () =>
    request<{ papers: PaperSummary[]; pool: Record<string, Record<string, number>> }>('/papers/history/'),
  submitExam: (answers: Record<number, string>, paperNo?: number) =>
    request<{
      score: number;
      paperCode: string;
      correctCount: number;
      totalCount: number;
      rank_hint: string;
      analysis: string[];
    }>('/exams/submit/', {
      method: 'POST',
      body: JSON.stringify({ answers, ...(paperNo === undefined ? {} : { paper_no: paperNo }) })
    }),
  demoLogin: () =>
    request<{ access: string; refresh: string }>('/auth/demo-login/', {
      method: 'POST'
    })
};
