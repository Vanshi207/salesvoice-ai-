export type User = { id: string; email: string; name: string; role: "admin" | "rep"; created_at: string };

export type Lead = {
  id: string; name: string; phone: string; email: string | null; company: string | null;
  language: string; stage: string; score: number | null; consent: boolean; dnd: boolean;
  created_at: string;
};

export type Page<T> = { items: T[]; total: number; limit: number; offset: number };

export type Call = {
  id: string; lead_id: string; filename: string; source: string;
  status: string; duration_s: number | null; languages: string | null;
  created_at: string;
};

export type Segment = { speaker: number; start_s: number; end_s: number; text: string };

export type AnalysisResult = {
  score_reasons: string[];
  next_steps: string[];
  objections: { category: string; quote: string; handled: boolean }[];
};

export type AnalysisMetrics = {
  rep_talk_ratio: number | null;
  longest_rep_monologue_s: number | null;
  rep_questions: number | null;
  customer_questions: number | null;
};

export type Analysis = {
  lead_score: number;
  sentiment: string;
  intent: string;
  summary: string;
  result: AnalysisResult;
  metrics: AnalysisMetrics;
};

export type CallDetail = Call & {
  rep_speaker: number;
  segments: Segment[];
  analysis: Analysis | null;
  error: string | null;
};

export type FollowUp = {
  id: string; lead_id: string; scheduled_at: string; note: string | null; status: string;
};

export type Doc = {
  id: string; title: string; status: string; chunk_count: number; created_at: string;
};

export type SearchHit = {
  chunk_id: string; document_title: string; text: string; score: number;
};

export const STAGES = ["new", "contacted", "hot", "follow_up", "won", "lost"] as const;

export const isFinished = (status: string) => ["done", "failed", "ready"].includes(status);
