"use client";

/**
 * apex-rag-omni — Trace reviewer (1k rows, virtualized).
 *
 * Staff-level patterns:
 *   - Virtualized list: only the visible rows are in the DOM. Scrolling
 *     through 1k+ rows is constant-time, not O(N).
 *   - Cursor pagination: loadMore() walks a `next_cursor` from the API.
 *     No "page 1 of N", no OFFSET, O(1) per page.
 *   - Optimistic feedback: the user's star rating lands instantly in
 *     local state, and we POST /feedback in the background. If the POST
 *     fails, we roll back.
 *
 * This component is the operational ground truth for retrieval quality.
 * Every trace here is a real answer that the system produced, with
 * latency, refusal, and the user's rating.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { FixedSizeList as VirtualList } from "react-window";

type Collection = "hr_policies" | "tech_docs" | "product_docs";

interface Trace {
  trace_id: string;
  day: string;
  ts: string;
  collection: Collection;
  query: string;
  latency_ms: number;
  refused: boolean;
  rating: number | null;
}

interface TracesResponse {
  traces: Trace[];
  next_cursor: string | null;
  has_more: boolean;
}

const PAGE_SIZE = 50;
const ROW_HEIGHT = 64;
const VIEWPORT_HEIGHT = 720;
const TODAY = new Date().toISOString().slice(0, 10);

// Default API key for local dev. The user can override this from the
// header input (saved to localStorage). In prod, the key should come
// from a real session — for this prototype, the dev-mode key matches
// the .env default.
const DEFAULT_API_KEY = "devkey-change-me";
const STORAGE_KEY = "apex_api_key";

// API base URL. The frontend runs on :3000 (Next.js) and the API on
// :8000 (FastAPI/uvicorn). The user can override at runtime via
// localStorage.setItem("apex_api_base", "https://api.example.com").
const DEFAULT_API_BASE = "http://localhost:8000";
const API_BASE_STORAGE_KEY = "apex_api_base";

function readKey(): string {
  if (typeof window === "undefined") return DEFAULT_API_KEY;
  return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_API_KEY;
}

function readApiBase(): string {
  if (typeof window === "undefined") return DEFAULT_API_BASE;
  return window.localStorage.getItem(API_BASE_STORAGE_KEY) ?? DEFAULT_API_BASE;
}

function authHeaders(): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-API-Key": DEFAULT_API_KEY,
  };
}

export default function ApexRagOmni() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Collection | "all">("all");
  const [apiKey, setApiKey] = useState<string>(DEFAULT_API_KEY);
  const [keyInput, setKeyInput] = useState<string>(DEFAULT_API_KEY);
  const [keySaved, setKeySaved] = useState<boolean>(false);
  const [apiBase, setApiBase] = useState<string>(DEFAULT_API_BASE);
  const [baseInput, setBaseInput] = useState<string>(DEFAULT_API_BASE);
  const [baseSaved, setBaseSaved] = useState<boolean>(false);

  // Hydrate the key + base URL from localStorage on mount.
  useEffect(() => {
    const k = readKey();
    const b = readApiBase();
    setApiKey(k);
    setKeyInput(k);
    setApiBase(b);
    setBaseInput(b);
  }, []);

  // Pending optimistic feedback — keyed by trace_id, value is the rating.
  // If the POST fails, we roll back from this map.
  const pending = useRef<Map<string, number>>(new Map());

  /**
   * Load the next page of traces from the API. Cursor pagination:
   * the response's `next_cursor` is the `trace_id` of the last row.
   * The query plan is a range scan on (day, trace_id), so this is
   * O(log N) regardless of how deep we are in the result set.
   */
  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        day: TODAY,
        limit: String(PAGE_SIZE),
      });
      if (cursor) params.set("cursor", cursor);
      const res = await fetch(`${apiBase}/traces?${params.toString()}`, {
        headers: { "X-API-Key": apiKey },
      });
      if (res.status === 403) {
        throw new Error(
          "API key rejected. Run localStorage.setItem('apex_api_key', '<your-key>') in DevTools and reload.",
        );
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: TracesResponse = await res.json();
      setTraces((prev) => [...prev, ...data.traces]);
      setCursor(data.next_cursor);
      setHasMore(data.has_more);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load traces");
    } finally {
      setLoading(false);
    }
  }, [cursor, hasMore, loading, apiKey, apiBase]);

  // Re-fetch from the top when the key or base URL changes
  // (reset cursor + traces so the next page is the first page of the
  // new query).
  useEffect(() => {
    setTraces([]);
    setCursor(null);
    setHasMore(true);
    setError(null);
  }, [apiKey, apiBase]);

  // Initial load (after key + base hydrate from localStorage).
  useEffect(() => {
    loadMore();
  }, [apiKey, apiBase]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Optimistic feedback: update local state immediately, POST in
   * background, roll back on failure. The user sees their star click
   * land in < 16ms; the network is allowed to take 200ms.
   */
  const handleFeedback = useCallback(
    async (traceId: string, rating: number) => {
      const previous = traces.find((t) => t.trace_id === traceId)?.rating ?? null;
      // 1. Optimistic update
      pending.current.set(traceId, rating);
      setTraces((prev) =>
        prev.map((t) => (t.trace_id === traceId ? { ...t, rating } : t)),
      );
      try {
        // 2. POST in background
        const res = await fetch(`${apiBase}/feedback`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
          body: JSON.stringify({ trace_id: traceId, rating }),
        });
        if (res.status === 403) {
        throw new Error(
          "API key rejected. Run localStorage.setItem('apex_api_key', '<your-key>') in DevTools and reload.",
        );
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      } catch {
        // 3. Roll back on failure
        pending.current.delete(traceId);
        setTraces((prev) =>
          prev.map((t) =>
            t.trace_id === traceId ? { ...t, rating: previous } : t,
          ),
        );
      }
    },
    [traces, apiKey],
  );

  // Save the key the user typed: persist to localStorage and update state.
  const handleSaveKey = useCallback(() => {
    const trimmed = keyInput.trim();
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, trimmed);
    }
    setApiKey(trimmed);
    setKeySaved(true);
    setTimeout(() => setKeySaved(false), 1500);
  }, [keyInput]);

  // Save the API base URL the user typed: persist to localStorage and update state.
  const handleSaveBase = useCallback(() => {
    const trimmed = baseInput.trim().replace(/\/+$/, "");
    if (typeof window !== "undefined") {
      window.localStorage.setItem(API_BASE_STORAGE_KEY, trimmed);
    }
    setApiBase(trimmed);
    setBaseSaved(true);
    setTimeout(() => setBaseSaved(false), 1500);
  }, [baseInput]);

  // Filtered list (cheap O(N) — runs on every render but the row count
  // is bounded by what's loaded so far; virtualized windowing is the
  // real perf win).
  const visible = useMemo(
    () =>
      filter === "all"
        ? traces
        : traces.filter((t) => t.collection === filter),
    [traces, filter],
  );

  // Row renderer for the virtualized list.
  const Row = ({
    index,
    style,
  }: {
    index: number;
    style: React.CSSProperties;
  }) => {
    const t = visible[index];
    if (!t) return null;
    return (
      <div
        style={style}
        className={`apex-row ${t.refused ? "apex-row--refused" : ""}`}
      >
        <span className="apex-cell apex-cell--ts">{t.ts.slice(11, 19)}</span>
        <span className={`apex-cell apex-cell--collection apex-${t.collection}`}>
          {t.collection.replace("_", " ")}
        </span>
        <span className="apex-cell apex-cell--query" title={t.query}>
          {t.query.length > 60 ? t.query.slice(0, 60) + "…" : t.query}
        </span>
        <span className="apex-cell apex-cell--latency">
          {t.latency_ms.toFixed(0)} ms
        </span>
        <span className="apex-cell apex-cell--refused">
          {t.refused ? "REFUSED" : "✓"}
        </span>
        <span className="apex-cell apex-cell--stars">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              className={`apex-star ${
                (t.rating ?? 0) >= n ? "apex-star--on" : ""
              }`}
              onClick={() => handleFeedback(t.trace_id, n)}
              aria-label={`Rate ${n} stars`}
            >
              ★
            </button>
          ))}
        </span>
      </div>
    );
  };

  return (
    <div className="apex-trace-reviewer">
      <header className="apex-header">
        <h1>apex-rag-omni — trace reviewer</h1>
        <div className="apex-summary">
          <span>{visible.length} traces loaded</span>
          <span>·</span>
          <span>day {TODAY}</span>
        </div>
        <div className="apex-filters">
          {(["all", "hr_policies", "tech_docs", "product_docs"] as const).map(
            (f) => (
              <button
                key={f}
                type="button"
                className={`apex-filter ${filter === f ? "apex-filter--on" : ""}`}
                onClick={() => setFilter(f)}
              >
                {f.replace("_", " ")}
              </button>
            ),
          )}
        </div>
        <div className="apex-key">
          <label className="apex-key-label" htmlFor="apex-key-input">
            X-API-Key
          </label>
          <input
            id="apex-key-input"
            type="password"
            className="apex-key-input"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSaveKey();
            }}
            placeholder="devkey-change-me"
            autoComplete="off"
            spellCheck={false}
          />
          <button
            type="button"
            className="apex-key-save"
            onClick={handleSaveKey}
          >
            {keySaved ? "saved" : "save"}
          </button>
          <label className="apex-key-label" htmlFor="apex-base-input">
            API base
          </label>
          <input
            id="apex-base-input"
            type="text"
            className="apex-base-input"
            value={baseInput}
            onChange={(e) => setBaseInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSaveBase();
            }}
            placeholder="http://localhost:8000"
            autoComplete="off"
            spellCheck={false}
          />
          <button
            type="button"
            className="apex-key-save"
            onClick={handleSaveBase}
          >
            {baseSaved ? "saved" : "save"}
          </button>
        </div>
      </header>

      {error && <div className="apex-error">error: {error}</div>}

      <div className="apex-virtualized">
        <VirtualList
          height={VIEWPORT_HEIGHT}
          itemCount={visible.length}
          itemSize={ROW_HEIGHT}
          width="100%"
          onItemsRendered={({ visibleStopIndex }) => {
            // Pre-fetch when we're within 10 rows of the end.
            if (
              hasMore &&
              !loading &&
              visibleStopIndex >= visible.length - 10
            ) {
              loadMore();
            }
          }}
        >
          {Row}
        </VirtualList>
      </div>

      <footer className="apex-footer">
        {loading ? (
          <span>loading…</span>
        ) : hasMore ? (
          <button type="button" onClick={loadMore} className="apex-loadmore">
            load more
          </button>
        ) : (
          <span>end of traces</span>
        )}
      </footer>
    </div>
  );
}
