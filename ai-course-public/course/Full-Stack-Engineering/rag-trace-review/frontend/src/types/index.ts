export type Rating = 'up' | 'down';

export interface TraceSummary {
  trace_id: string;
  created_at: string;
  prompt_version: string;
  user_query: string;
  token_usage: number;
  latency_ms: number;
  status: 'ok' | 'error';
  feedback: Rating | null;
}

export interface RetrievedChunk {
  chunk_id: string;
  text: string;
  score: number;
}

export interface Citation {
  chunk_id: string;
  source: string;
  score: number;
}

export interface TraceDetail extends TraceSummary {
  prompt: string;
  retrieved_chunks: RetrievedChunk[];
  model_response: string;
  citations: Citation[];
}

export interface PageMeta {
  next_cursor: string | null;
  has_more: boolean;
}

export interface TracePage {
  items: TraceSummary[];
  meta: PageMeta;
}

export interface TraceFilters {
  day?: string;
  prompt_version?: string;
  min_latency?: number;
  max_latency?: number;
}
