const API_URL = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";

export interface Me {
  username: string;
  display_name: string;
  role: string;
}

export interface Citation {
  chunk_id: string;
  doc_id: string;
  source: string;
}

export interface QueryResponse {
  request_id: string;
  question: string;
  strategy: string;
  answer: string;
  citations: Citation[];
  graph_seeds: string[];
  graph_edges: [string, string, string][];
  latency_ms: number;
  refused: boolean;
}

export interface GraphNode {
  id: string;
  type: string;
  degree: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  rel: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface EvalSummaryRow {
  kind: string;
  strategy: string;
  n: number;
  citation_precision: number;
  keyword_hit: number;
  refused: number;
}

export interface EvalDetailRow {
  question: string;
  kind: string;
  strategy: string;
  expected_doc_ids: string[];
  cited_doc_ids: string[];
  cited_chunk_ids: string[];
  answer_excerpt: string;
  citation_precision: number;
  keyword_hit_rate: number;
  refused: boolean;
}

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API_URL}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${await r.text()}`);
  return r.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${await r.text()}`);
  return r.json();
}

export const STRATEGIES = ["vector", "bm25", "graph", "hybrid"] as const;

export async function ask(question: string, strategy: string): Promise<QueryResponse> {
  return apiPost<QueryResponse>("/query", { question, strategy });
}

export async function getGraph(): Promise<GraphResponse> {
  return apiGet<GraphResponse>("/graph");
}

export async function getGraphStats(): Promise<{
  nodes: number;
  edges: number;
  node_types: Record<string, number>;
  rel_types: Record<string, number>;
}> {
  return apiGet("/graph/stats");
}

export async function getEvalSummary(): Promise<{ rows: EvalSummaryRow[] }> {
  return apiGet("/eval/summary");
}

export async function getEvalRows(
  kind?: string,
  strategy?: string
): Promise<EvalDetailRow[]> {
  const params = new URLSearchParams();
  if (kind) params.set("kind", kind);
  if (strategy) params.set("strategy", strategy);
  return apiGet<EvalDetailRow[]>(`/eval/rows?${params.toString()}`);
}

export async function ingestEval(): Promise<{ rows_inserted: number }> {
  return apiPost("/ingest/eval", {});
}
