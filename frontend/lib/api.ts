const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

function authHeaders(): HeadersInit {
  return {
    Authorization: `Bearer ${API_KEY}`,
    "Content-Type": "application/json",
  };
}

function authHeadersNoJson(): HeadersInit {
  return { Authorization: `Bearer ${API_KEY}` };
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface UploadResponse {
  month_key: string;
  chunks_indexed: number;
  namespace: string;
}

export interface MonthsResponse {
  months: string[];
}

export interface DeleteMonthResponse {
  deleted: boolean;
  month_key: string;
}

export interface KeyTransaction {
  description: string;
  amount: number;
}

export interface SingleMonthAnalysis {
  summary: string;
  total_income: number;
  total_expenses: number;
  net_pnl: number;
  key_transactions: KeyTransaction[];
  insights: string[];
}

export interface ChangeMetric {
  amount: number;
  percent: number;
  direction: "up" | "down" | "unchanged";
}

export interface MonthComparisonResult {
  current_month: string;
  previous_month: string;
  income_change: ChangeMetric;
  expense_change: ChangeMetric;
  net_pnl_change: ChangeMetric;
  highlights: string[];
  warnings: string[];
  recommendations: string[];
}

export interface SourceChunk {
  month_key: string;
  chunk_preview: string;
}

export interface AskResponse {
  answer: string;
  sources: SourceChunk[];
}

export interface HealthResponse {
  status: string;
  pinecone_namespaces: string[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ── Ingest ────────────────────────────────────────────────────────────────────

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<UploadResponse>("/ingest/upload", {
    method: "POST",
    headers: authHeadersNoJson(),
    body: form,
  });
}

export async function listMonths(): Promise<string[]> {
  const data = await apiFetch<MonthsResponse>("/ingest/months", {
    headers: authHeaders(),
  });
  return data.months;
}

export async function deleteMonth(monthKey: string): Promise<DeleteMonthResponse> {
  return apiFetch<DeleteMonthResponse>(`/ingest/month/${monthKey}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

// ── Query ─────────────────────────────────────────────────────────────────────

export async function analyzeMonth(
  monthKey: string,
  question: string
): Promise<SingleMonthAnalysis> {
  return apiFetch<SingleMonthAnalysis>("/query/analyze", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ month_key: monthKey, question }),
  });
}

export async function compareMonths(
  currentMonth: string,
  previousMonth: string
): Promise<MonthComparisonResult> {
  return apiFetch<MonthComparisonResult>("/query/compare", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      current_month: currentMonth,
      previous_month: previousMonth,
    }),
  });
}

export async function askQuestion(
  question: string,
  months: string[]
): Promise<AskResponse> {
  return apiFetch<AskResponse>("/query/ask", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ question, months }),
  });
}

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}
