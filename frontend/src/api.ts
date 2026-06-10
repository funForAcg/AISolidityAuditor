export type AuditStatus =
  | "pending"
  | "running_slither"
  | "running_ai"
  | "completed"
  | "failed";

export type Severity =
  | "High"
  | "Medium"
  | "Low"
  | "Informational"
  | "Optimization";

export interface AuditSummary {
  total: number;
  high: number;
  medium: number;
  low: number;
  informational: number;
  optimization: number;
  ai_explained: number;
}

export interface AuditStatusResponse {
  task_id: string;
  status: AuditStatus;
  progress: string;
  error?: string;
  summary?: AuditSummary;
  filename?: string;
  finished_at?: string;
  duration_sec?: number;
}

export interface AIExplanation {
  title: string;
  problem: string;
  impact: string;
  recommendation: string;
  ai_success: boolean;
  provider?: string;
  error?: string;
}

export interface Finding {
  id: string;
  detector: string;
  severity: Severity;
  description: string;
  contract?: string;
  function?: string;
  file?: string;
  line?: number;
  ai: AIExplanation;
  ai_expanded: boolean;
}

export interface FindingsResponse {
  task_id: string;
  findings: Finding[];
}

const API_BASE = "/api";

export async function createAudit(
  file: File,
  apiKey?: string,
  aiProvider?: "openai" | "claude"
): Promise<{ task_id: string }> {
  const form = new FormData();
  form.append("file", file);
  if (apiKey) form.append("api_key", apiKey);
  if (aiProvider) form.append("ai_provider", aiProvider);

  const res = await fetch(`${API_BASE}/v1/audits`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }

  return res.json();
}

export async function getAuditStatus(
  taskId: string
): Promise<AuditStatusResponse> {
  const res = await fetch(`${API_BASE}/v1/audits/${taskId}`);
  if (!res.ok) throw new Error("Failed to fetch task status");
  return res.json();
}

export async function getFindings(taskId: string): Promise<FindingsResponse> {
  const res = await fetch(`${API_BASE}/v1/audits/${taskId}/findings`);
  if (!res.ok) throw new Error("Failed to fetch findings");
  return res.json();
}

export async function getReport(taskId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/v1/audits/${taskId}/report`);
  if (!res.ok) throw new Error("Failed to fetch report");
  return res.text();
}

export function getReportDownloadUrl(taskId: string): string {
  return `${API_BASE}/v1/audits/${taskId}/report?download=true`;
}
