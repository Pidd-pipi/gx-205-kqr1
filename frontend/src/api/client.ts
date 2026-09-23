import type { Dashboard, ExamReport, PaperSnapshot } from '@/types/bank';

const API_BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    throw new Error(`请求失败：${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; service: string }>('/health/'),
  dashboard: () => request<Dashboard>('/dashboard/'),
  generatePaper: (difficulty: string, amount: number) =>
    request<PaperSnapshot>('/papers/generate/', {
      method: 'POST',
      body: JSON.stringify({ difficulty, amount })
    }),
  getPaper: (number: number) => request<PaperSnapshot>(`/papers/${number}/`),
  submitExam: (paperNumber: number, answers: Record<number, string>) =>
    request<ExamReport>('/exams/submit/', {
      method: 'POST',
      body: JSON.stringify({ paper_number: paperNumber, answers })
    }),
  demoLogin: () =>
    request<{ access: string; refresh: string }>('/auth/demo-login/', {
      method: 'POST'
    })
};
