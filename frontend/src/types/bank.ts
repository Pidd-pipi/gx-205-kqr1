export interface Category {
  id: number;
  name: string;
  accuracy: number;
  total: number;
}

export interface Question {
  id: number;
  type: string;
  difficulty: string;
  stem: string;
  options: string[];
  answer: string;
  explanation: string;
  knowledge: string;
}

export interface PaperQuestion extends Question {
  /** true 表示该题由相邻难度补入 */
  substituted: boolean;
}

export interface ReplacementNote {
  type: string;
  count: number;
  /** 各相邻难度分别补入的题数，如 { "初级": 2, "高级": 1 } */
  from: Record<string, number>;
}

export interface TypeGap {
  type: string;
  missing: number;
}

export interface PaperSnapshot {
  number: number;
  difficulty: string;
  requestedAmount: number;
  actualAmount: number;
  typeCounts: Record<string, number>;
  replacements: ReplacementNote[];
  gaps: TypeGap[];
  questions: PaperQuestion[];
  createdAt: string | null;
}

export interface ExamReport {
  paper_number: number;
  score: number;
  correct: number;
  total: number;
  rank_hint: string;
  analysis: string[];
}

export interface Ranking {
  rank: number;
  name: string;
  tier: string;
  score: number;
  accuracy: number;
}

export interface WrongBookItem {
  id: number;
  title: string;
  type: string;
  mistakes: number;
  lastPracticed: string;
}

export interface Dashboard {
  profile: {
    nickname: string;
    tier: string;
    totalAnswered: number;
    correctRate: number;
    streakDays: number;
    practiceMinutes: number;
  };
  categories: Category[];
  wrongBook: WrongBookItem[];
  rankings: Ranking[];
  radar: { axis: string; value: number }[];
}
