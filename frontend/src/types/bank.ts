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
  /** 快照题：生成该卷时用户选择的目标难度 */
  requested_difficulty?: string;
  /** 快照题：是否由相邻难度补入 */
  replaced?: boolean;
  /** 与目标难度相差几个等级（0 为原题难度） */
  replace_distance?: number;
  /** 补入说明文案，如“相邻难度补入” */
  replace_label?: string;
}

export interface Replacement {
  question_id: number;
  type: string;
  target_difficulty: string;
  actual_difficulty: string;
  distance: number;
  label: string;
}

/** 带编号的试卷快照：同编号回查时内容与生成时完全一致 */
export interface Paper {
  paperNo: number;
  paperCode: string;
  difficulty: string;
  requestedAmount: number;
  actualAmount: number;
  questions: Question[];
  typeQuota: Record<string, number>;
  typeActual: Record<string, number>;
  typeGaps: Record<string, number>;
  replacements: Replacement[];
  replacementCount: number;
  replacementNote: string;
  shortage: boolean;
  shortageCount: number;
  createdAt?: string | null;
}

/** 历史列表中的试卷摘要 */
export interface PaperSummary {
  paperNo: number;
  paperCode: string;
  difficulty: string;
  requestedAmount: number;
  actualAmount: number;
  replacementCount: number;
  replacementNote: string;
  shortage: boolean;
  shortageCount: number;
  typeGaps: Record<string, number>;
  createdAt?: string | null;
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
  paper: Question[];
  wrongBook: WrongBookItem[];
  rankings: Ranking[];
  radar: { axis: string; value: number }[];
}
