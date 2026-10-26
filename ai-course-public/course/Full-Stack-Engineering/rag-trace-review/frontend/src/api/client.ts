import type { TracePage, TraceDetail, TraceFilters, Rating } from '../types';

const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = 15_000;

function buildQuery(filters: TraceFilters, cursor?: string | null, limit = 100): string {
  const p = new URLSearchParams();
  if (filters.day) p.set('day', filters.day);
  if (filters.prompt_version) p.set('prompt_version', filters.prompt_version);
  if (filters.min_latency !== undefined) p.set('min_latency', String(filters.min_latency));
  if (filters.max_latency !== undefined) p.set('max_latency', String(filters.max_latency));
  if (cursor) p.set('cursor', cursor);
  p.set('limit', String(limit));
  return p.toString();
}

export async function fetchTraces(
  filters: TraceFilters,
  cursor?: string | null,
  signal?: AbortSignal
): Promise<TracePage> {
  const r = await fetch(`${BASE}/traces?${buildQuery(filters, cursor)}`, { signal });
  if (!r.ok) throw new Error(`Failed to load traces: ${r.status}`);
  return r.json();
}

export async function fetchTrace(id: string, signal?: AbortSignal): Promise<TraceDetail> {
  const r = await fetch(`${BASE}/traces/${id}`, { signal });
  if (!r.ok) throw new Error(`Failed to load trace: ${r.status}`);
  return r.json();
}

export async function submitFeedback(
  id: string,
  rating: Rating,
  note?: string
): Promise<void> {
  const r = await fetch(`${BASE}/traces/${id}/feedback`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rating, note }),
  });
  if (!r.ok) throw new Error(`Failed to submit feedback: ${r.status}`);
}
