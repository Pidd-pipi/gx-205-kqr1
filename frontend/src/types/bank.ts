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
