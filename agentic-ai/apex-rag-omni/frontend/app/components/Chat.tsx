"use client";

/**
 * apex-rag-omni — ChatGPT-style chat UI.
 *
 *   - Streaming answers over SSE (POST /query/stream): citations (sources)
 *     arrive first so [n] chips are live while the text types out.
 *   - Stop generating (button or Esc) keeps the partial answer.
 *   - Regenerate, copy, thumbs up/down (optimistic, rolled back on failure).
 *   - Sessions: new / rename (double-click) / delete, persisted locally.
 *   - Smart auto-scroll (only follows the stream if you're at the bottom),
 *     auto-growing textarea, Enter to send / Shift+Enter newline, IME-safe.
 *   - Lightweight markdown (code fences, **bold**, `code`, lists) with no
 *     extra dependencies; [doc_N] becomes a clickable citation chip.
 *
 * Auth: API key + base URL live in localStorage (⚙ in the top bar).
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

type Collection = "hr_policies" | "tech_docs" | "product_docs";

interface Span {
  doc_id: string;
  title?: string;
  offset: number;
  text: string;
  score: number;
}

interface Evidence {
  query: string;
  collection: Collection;
  answer: string;
  spans: Span[];
  refused: boolean;
  refusal_reason: string | null;
  groundedness?: number | null;
  flags?: string[];
}

interface Timing {
  hybrid_ms: number;
  rerank_ms: number;
  answer_ms: number;
  total_ms: number;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  collection: Collection;
  traceId?: string;
  spans?: Span[];
  refused?: boolean;
  refusalReason?: string | null;
  groundedness?: number | null;
  flags?: string[];
  timing?: Timing;
  pending?: boolean; // request sent, nothing received yet
  streaming?: boolean; // tokens arriving
  stopped?: boolean; // user hit Stop
  error?: string;
  feedback?: "up" | "down";
}

interface ChatSession {
  id: string;
  title: string;
  collection: Collection;
  createdAt: number;
  messages: ChatMessage[];
}

const STORAGE_KEY = "apex_api_key";
const API_BASE_STORAGE_KEY = "apex_api_base";
const SESSIONS_STORAGE_KEY = "apex_chat_sessions";
const DEFAULT_API_BASE = "http://localhost:8000";
const DEFAULT_API_KEY = "devkey-change-me";

const COLLECTIONS: { id: Collection; label: string; hint: string }[] = [
  { id: "hr_policies", label: "HR Policies", hint: "PTO, benefits, conduct" },
  { id: "tech_docs", label: "Tech Docs", hint: "services, APIs, runbooks" },
  { id: "product_docs", label: "Product Docs", hint: "features, releases" },
];

const STARTERS: Record<Collection, string[]> = {
  hr_policies: [
    "How much PTO do I get per year?",
    "What is the parental leave policy?",
    "How do I submit an expense report?",
  ],
  tech_docs: [
    "How do I authenticate to the API gateway?",
    "Where do I find the deployment runbook?",
    "What's the SLA for the search service?",
  ],
  product_docs: [
    "How do I export data to CSV?",
    "What's new in this release?",
    "How do I invite a teammate?",
  ],
};

const colLabel = (c: Collection) =>
  COLLECTIONS.find((x) => x.id === c)?.label ?? c;

/* ---------- storage helpers ---------- */

function readKey(): string {
  if (typeof window === "undefined") return DEFAULT_API_KEY;
  return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_API_KEY;
}
function readApiBase(): string {
  if (typeof window === "undefined") return DEFAULT_API_BASE;
  return window.localStorage.getItem(API_BASE_STORAGE_KEY) ?? DEFAULT_API_BASE;
}

/** A reload mid-stream would leave a message "pending" forever. */
function sanitize(sessions: ChatSession[]): ChatSession[] {
  return sessions.map((s) => ({
    ...s,
    messages: s.messages.map((m) =>
      m.pending || m.streaming
        ? {
            ...m,
            pending: false,
            streaming: false,
            stopped: !m.error && m.text.length > 0,
            error: m.text ? undefined : "Interrupted (page was reloaded)",
          }
        : m,
    ),
  }));
}
function loadSessions(): ChatSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(SESSIONS_STORAGE_KEY);
    return raw ? sanitize(JSON.parse(raw) as ChatSession[]) : [];
  } catch {
    return [];
  }
}
function saveSessions(sessions: ChatSession[]) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions));
  } catch {
    /* quota exceeded: chat still works, just not persisted */
  }
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10);
}
function titleFor(text: string): string {
  const t = text.trim();
  if (!t) return "New chat";
  return t.length > 40 ? t.slice(0, 40) + "…" : t;
}

/* ---------- SSE client ---------- */

interface StreamHandlers {
  onMeta: (traceId: string) => void;
  onSources: (d: {
    spans: Span[];
    refused: boolean;
    refusal_reason: string | null;
    flags?: string[];
  }) => void;
  onToken: (delta: string) => void;
  onDone: (d: { trace_id: string; evidence: Evidence; timing_ms: Timing }) => void;
}

async function streamQuery(
  apiBase: string,
  apiKey: string,
  body: { collection: Collection; query: string },
  signal: AbortSignal,
  h: StreamHandlers,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${apiBase}/query/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    throw new Error(
      `Can't reach the API at ${apiBase}. Is the backend running (make api)? ` +
        `If it is, check ⚙ settings and that CORS allows ${window.location.origin}.`,
    );
  }
  if (res.status === 403) {
    throw new Error("API key rejected. Open ⚙ settings and set the matching X-API-Key.");
  }
  if (!res.ok || !res.body) {
    throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let finished = false;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const block = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      let event = "message";
      let data = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data += line.slice(6);
      }
      if (!data) continue;
      const payload = JSON.parse(data);
      if (event === "meta") h.onMeta(payload.trace_id);
      else if (event === "sources") h.onSources(payload);
      else if (event === "token") h.onToken(payload.delta);
      else if (event === "done") {
        finished = true;
        h.onDone(payload);
      } else if (event === "error") throw new Error(payload.message);
    }
  }
  if (!finished) throw new Error("Connection closed before the answer finished.");
}

/* ---------- lightweight markdown ---------- */

type CiteFn = (n: number) => void;

function renderInline(
  text: string,
  spanCount: number,
  onCite: CiteFn,
  keyBase: string,
): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  const re = /(\[doc_(\d+)\])|(\*\*[^*\n]+\*\*)|(`[^`\n]+`)/g;
  let last = 0;
  let i = 0;
  for (const m of text.matchAll(re)) {
    const start = m.index ?? 0;
    if (start > last) out.push(text.slice(last, start));
    const k = `${keyBase}-${i++}`;
    if (m[1]) {
      const n = parseInt(m[2], 10);
      const valid = n >= 1 && n <= spanCount;
      out.push(
        <button
          key={k}
          type="button"
          className={`apex-cite ${valid ? "" : "apex-cite--invalid"}`}
          onClick={() => valid && onCite(n)}
          title={valid ? `Jump to source ${n}` : "Citation out of range"}
          disabled={!valid}
        >
          {n}
        </button>,
      );
    } else if (m[3]) {
      out.push(<strong key={k}>{m[3].slice(2, -2)}</strong>);
    } else if (m[4]) {
      out.push(<code key={k} className="apex-code-inline">{m[4].slice(1, -1)}</code>);
    }
    last = start + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

function renderRich(text: string, spanCount: number, onCite: CiteFn): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  const parts = text.split(/(```[\s\S]*?(?:```|$))/g); // unterminated fence is fine while streaming
  parts.forEach((part, pi) => {
    if (part.startsWith("```")) {
      const body = part.replace(/^```[^\n]*\n?/, "").replace(/```$/, "");
      out.push(
        <pre key={`pre-${pi}`} className="apex-code-block">
          <code>{body}</code>
        </pre>,
      );
      return;
    }
    const lines = part.split("\n");
    let list: { ordered: boolean; items: string[] } | null = null;
    let para: string[] = [];
    const flushPara = () => {
      if (para.length) {
        out.push(
          <p key={`p-${pi}-${out.length}`}>
            {renderInline(para.join(" "), spanCount, onCite, `p${pi}-${out.length}`)}
          </p>,
        );
        para = [];
      }
    };
    const flushList = () => {
      if (!list) return;
      const Tag = list.ordered ? "ol" : "ul";
      out.push(
        <Tag key={`l-${pi}-${out.length}`}>
          {list.items.map((it, ii) => (
            <li key={ii}>{renderInline(it, spanCount, onCite, `li${pi}-${out.length}-${ii}`)}</li>
          ))}
        </Tag>,
      );
      list = null;
    };
    for (const line of lines) {
      const ul = line.match(/^\s*[-*]\s+(.*)$/);
      const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
      if (ul || ol) {
        flushPara();
        const ordered = !!ol;
        if (list && list.ordered !== ordered) flushList();
        if (!list) list = { ordered, items: [] };
        list.items.push((ul ?? ol)![1]);
      } else if (!line.trim()) {
        flushPara();
        flushList();
      } else {
        flushList();
        para.push(line.trim());
      }
    }
    flushPara();
    flushList();
  });
  return out;
}

/* ---------- main component ---------- */

export default function Chat() {
  const [apiKey, setApiKey] = useState<string>(DEFAULT_API_KEY);
  const [apiBase, setApiBase] = useState<string>(DEFAULT_API_BASE);
  const [collection, setCollection] = useState<Collection>("hr_policies");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [draft, setDraft] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [busy, setBusy] = useState<boolean>(false);
  const [atBottom, setAtBottom] = useState<boolean>(true);
  const [hydrated, setHydrated] = useState<boolean>(false);

  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const ctrlRef = useRef<AbortController | null>(null);
  const stickRef = useRef<boolean>(true);

  const newSession = useCallback((col: Collection): ChatSession => {
    return { id: uid(), title: "New chat", collection: col, createdAt: Date.now(), messages: [] };
  }, []);

  // Hydrate from localStorage once.
  useEffect(() => {
    setApiKey(readKey());
    setApiBase(readApiBase());
    const loaded = loadSessions();
    if (loaded.length > 0) {
      setSessions(loaded);
      setActiveId(loaded[0].id);
      setCollection(loaded[0].collection);
    } else {
      const s = newSession("hr_policies");
      setSessions([s]);
      setActiveId(s.id);
    }
    setHydrated(true);
  }, [newSession]);

  // Persist (never before hydration — would clobber stored chats).
  useEffect(() => {
    if (hydrated) saveSessions(sessions);
  }, [sessions, hydrated]);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeId) ?? null,
    [sessions, activeId],
  );

  // Follow the stream only while the user is parked at the bottom.
  useEffect(() => {
    const el = scrollerRef.current;
    if (el && stickRef.current) el.scrollTop = el.scrollHeight;
  }, [sessions, activeId]);

  const onScroll = useCallback(() => {
    const el = scrollerRef.current;
    if (!el) return;
    const near = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    stickRef.current = near;
    setAtBottom(near);
  }, []);
  const scrollToBottom = useCallback(() => {
    const el = scrollerRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, []);

  // Auto-grow textarea up to ~6 lines.
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [draft]);

  const patchSession = useCallback(
    (id: string, fn: (s: ChatSession) => ChatSession) =>
      setSessions((prev) => prev.map((s) => (s.id === id ? fn(s) : s))),
    [],
  );
  const patchMessage = useCallback(
    (sid: string, mid: string, fn: (m: ChatMessage) => ChatMessage) =>
      patchSession(sid, (s) => ({
        ...s,
        messages: s.messages.map((m) => (m.id === mid ? fn(m) : m)),
      })),
    [patchSession],
  );

  const stop = useCallback(() => ctrlRef.current?.abort(), []);

  /** Run one assistant turn for `query` into `session`. */
  const runTurn = useCallback(
    async (session: ChatSession, query: string, assistantId: string) => {
      const sid = session.id;
      const ctrl = new AbortController();
      ctrlRef.current = ctrl;
      setBusy(true);
      stickRef.current = true;
      try {
        await streamQuery(
          apiBase,
          apiKey,
          { collection: session.collection, query },
          ctrl.signal,
          {
            onMeta: (traceId) =>
              patchMessage(sid, assistantId, (m) => ({ ...m, traceId })),
            onSources: (d) =>
              patchMessage(sid, assistantId, (m) => ({
                ...m,
                pending: false,
                streaming: true,
                spans: d.spans,
                refused: d.refused,
                refusalReason: d.refusal_reason,
                flags: d.flags,
              })),
            onToken: (delta) =>
              patchMessage(sid, assistantId, (m) => ({
                ...m,
                pending: false,
                streaming: true,
                text: m.text + delta,
              })),
            onDone: (d) =>
              patchMessage(sid, assistantId, (m) => ({
                ...m,
                pending: false,
                streaming: false,
                text: d.evidence.answer, // authoritative final text
                traceId: d.trace_id,
                spans: d.evidence.spans,
                refused: d.evidence.refused,
                refusalReason: d.evidence.refusal_reason,
                groundedness: d.evidence.groundedness,
                flags: d.evidence.flags,
                timing: d.timing_ms,
              })),
          },
        );
      } catch (e: unknown) {
        const aborted = e instanceof DOMException && e.name === "AbortError";
        patchMessage(sid, assistantId, (m) => ({
          ...m,
          pending: false,
          streaming: false,
          ...(aborted
            ? { stopped: true }
            : { error: e instanceof Error ? e.message : "Request failed" }),
        }));
      } finally {
        if (ctrlRef.current === ctrl) ctrlRef.current = null;
        setBusy(false);
      }
    },
    [apiBase, apiKey, patchMessage],
  );

  const sendQuery = useCallback(
    (text: string) => {
      const q = text.trim();
      if (!q || !activeSession || busy) return;
      const userMsg: ChatMessage = { id: uid(), role: "user", text: q, collection: activeSession.collection };
      const asst: ChatMessage = {
        id: uid(), role: "assistant", text: "", collection: activeSession.collection, pending: true,
      };
      patchSession(activeSession.id, (s) => ({
        ...s,
        title: s.messages.length === 0 ? titleFor(q) : s.title,
        messages: [...s.messages, userMsg, asst],
      }));
      setDraft("");
      inputRef.current?.focus();
      void runTurn(activeSession, q, asst.id);
    },
    [activeSession, busy, patchSession, runTurn],
  );

  const regenerate = useCallback(
    (assistantId: string) => {
      if (!activeSession || busy) return;
      const idx = activeSession.messages.findIndex((m) => m.id === assistantId);
      const user = activeSession.messages[idx - 1];
      if (idx < 1 || user?.role !== "user") return;
      patchMessage(activeSession.id, assistantId, (m) => ({
        id: m.id, role: "assistant", text: "", collection: m.collection, pending: true,
      }));
      void runTurn(activeSession, user.text, assistantId);
    },
    [activeSession, busy, patchMessage, runTurn],
  );

  /** Optimistic thumbs: UI flips instantly, POST in background, rollback on failure. */
  const sendFeedback = useCallback(
    async (messageId: string, value: "up" | "down") => {
      if (!activeSession) return;
      const sid = activeSession.id;
      const msg = activeSession.messages.find((m) => m.id === messageId);
      if (!msg?.traceId || msg.feedback === value) return;
      const prev = msg.feedback;
      patchMessage(sid, messageId, (m) => ({ ...m, feedback: value }));
      try {
        const res = await fetch(`${apiBase}/feedback`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
          body: JSON.stringify({ trace_id: msg.traceId, rating: value === "up" ? 5 : 1 }),
        });
        if (!res.ok) throw new Error(String(res.status));
      } catch {
        patchMessage(sid, messageId, (m) => ({ ...m, feedback: prev }));
      }
    },
    [activeSession, apiBase, apiKey, patchMessage],
  );

  const addSession = useCallback(
    (col: Collection) => {
      stop();
      const s = newSession(col);
      setSessions((prev) => [s, ...prev]);
      setActiveId(s.id);
      setCollection(col);
      setDraft("");
      inputRef.current?.focus();
    },
    [newSession, stop],
  );

  const switchCollection = useCallback(
    (col: Collection) => {
      if (activeSession && activeSession.messages.length === 0) {
        setCollection(col);
        patchSession(activeSession.id, (s) => ({ ...s, collection: col }));
      } else {
        addSession(col); // never mix collections inside one thread
      }
    },
    [activeSession, addSession, patchSession],
  );

  const deleteSession = useCallback(
    (id: string) => {
      if (id === activeId) stop();
      const rest = sessions.filter((s) => s.id !== id);
      if (rest.length === 0) {
        const s = newSession(collection);
        setSessions([s]);
        setActiveId(s.id);
      } else {
        setSessions(rest);
        if (id === activeId) {
          setActiveId(rest[0].id);
          setCollection(rest[0].collection);
        }
      }
    },
    [activeId, collection, newSession, sessions, stop],
  );

  const renameSession = useCallback(
    (id: string, title: string) => {
      const t = title.trim();
      if (t) patchSession(id, (s) => ({ ...s, title: t }));
    },
    [patchSession],
  );

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
        e.preventDefault();
        sendQuery(draft);
      }
    },
    [draft, sendQuery],
  );

  // Esc stops generation from anywhere.
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape" && ctrlRef.current) ctrlRef.current.abort();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  const activeCollection = activeSession?.collection ?? collection;
  const lastAssistantId = [...(activeSession?.messages ?? [])]
    .reverse()
    .find((m) => m.role === "assistant")?.id;

  return (
    <div className={`apex-chat ${sidebarOpen ? "" : "apex-chat--collapsed"}`}>
      <aside className="apex-sidebar">
        <button type="button" className="apex-newchat" onClick={() => addSession(collection)}>
          + New chat
        </button>

        <div className="apex-sidebar-section">
          <div className="apex-sidebar-label">Collection</div>
          {COLLECTIONS.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`apex-collection ${activeCollection === c.id ? "apex-collection--on" : ""}`}
              onClick={() => switchCollection(c.id)}
              title={c.hint}
            >
              {c.label}
            </button>
          ))}
        </div>

        <div className="apex-sidebar-section apex-sidebar-history">
          <div className="apex-sidebar-label">History</div>
          {sessions.map((s) => (
            <SessionItem
              key={s.id}
              session={s}
              active={s.id === activeId}
              onOpen={() => {
                if (s.id !== activeId) stop();
                setActiveId(s.id);
                setCollection(s.collection);
              }}
              onRename={(t) => renameSession(s.id, t)}
              onDelete={() => deleteSession(s.id)}
            />
          ))}
        </div>

        <div className="apex-sidebar-section apex-sidebar-bottom">
          <a className="apex-traces-link" href="/traces" target="_blank" rel="noreferrer">
            View trace reviewer →
          </a>
        </div>
      </aside>

      <main className="apex-main">
        <header className="apex-topbar">
          <button
            type="button"
            className="apex-burger"
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label="toggle sidebar"
          >
            ☰
          </button>
          <h1 className="apex-title">
            apex-rag-omni{" "}
            <span className={`apex-pill apex-pill--${activeCollection}`}>
              {colLabel(activeCollection)}
            </span>
          </h1>
          <SettingsChip
            apiBase={apiBase}
            apiKey={apiKey}
            onBaseChange={setApiBase}
            onKeyChange={setApiKey}
          />
        </header>

        <div className="apex-scroll" ref={scrollerRef} onScroll={onScroll}>
          <div className="apex-thread">
            {activeSession && activeSession.messages.length === 0 && (
              <div className="apex-empty">
                <h2>What can I help you find?</h2>
                <p>
                  Searching <strong>{colLabel(activeCollection)}</strong>. Every answer cites
                  its sources, or is refused.
                </p>
                <div className="apex-starters">
                  {STARTERS[activeCollection].map((s) => (
                    <button key={s} type="button" className="apex-starter" onClick={() => sendQuery(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {activeSession?.messages.map((m) => (
              <MessageRow
                key={m.id}
                msg={m}
                sessionId={activeSession.id}
                isLastAssistant={m.id === lastAssistantId}
                busy={busy}
                onRegenerate={() => regenerate(m.id)}
                onFeedback={(v) => sendFeedback(m.id, v)}
              />
            ))}
          </div>
        </div>

        {!atBottom && (
          <button type="button" className="apex-jump" onClick={scrollToBottom} aria-label="scroll to latest">
            ↓
          </button>
        )}

        <form
          className="apex-inputbar"
          onSubmit={(e) => {
            e.preventDefault();
            sendQuery(draft);
          }}
        >
          <div className="apex-inputwrap">
            <textarea
              ref={inputRef}
              className="apex-input"
              placeholder={`Ask ${colLabel(activeCollection)}…`}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              maxLength={2000}
              disabled={!activeSession}
              aria-label="message"
            />
            {busy ? (
              <button type="button" className="apex-send apex-send--stop" onClick={stop} aria-label="stop generating" title="Stop (Esc)">
                ■
              </button>
            ) : (
              <button type="submit" className="apex-send" disabled={!draft.trim() || !activeSession} aria-label="send">
                ↑
              </button>
            )}
          </div>
          <div className="apex-fineprint">
            Answers are grounded in retrieved sources. Enter to send · Shift+Enter for a new line
          </div>
        </form>
      </main>
    </div>
  );
}

/* ---------- Sidebar item (rename / delete) ---------- */

function SessionItem({
  session, active, onOpen, onRename, onDelete,
}: {
  session: ChatSession;
  active: boolean;
  onOpen: () => void;
  onRename: (t: string) => void;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState(session.title);
  const commit = () => {
    setEditing(false);
    if (val.trim() && val.trim() !== session.title) onRename(val);
    else setVal(session.title);
  };
  if (editing) {
    return (
      <input
        className="apex-session-edit"
        autoFocus
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            setVal(session.title);
            setEditing(false);
          }
        }}
        aria-label="rename chat"
      />
    );
  }
  return (
    <div className={`apex-session-row ${active ? "apex-session-row--on" : ""}`}>
      <button
        type="button"
        className="apex-session"
        onClick={onOpen}
        onDoubleClick={() => {
          setVal(session.title);
          setEditing(true);
        }}
        title="Double-click to rename"
      >
        {session.title}
      </button>
      <button
        type="button"
        className="apex-session-del"
        onClick={() => {
          if (session.messages.length === 0 || window.confirm("Delete this chat?")) onDelete();
        }}
        aria-label={`delete chat ${session.title}`}
        title="Delete chat"
      >
        ×
      </button>
    </div>
  );
}

/* ---------- Message row ---------- */

function MessageRow({
  msg, sessionId, isLastAssistant, busy, onRegenerate, onFeedback,
}: {
  msg: ChatMessage;
  sessionId: string;
  isLastAssistant: boolean;
  busy: boolean;
  onRegenerate: () => void;
  onFeedback: (v: "up" | "down") => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const isUser = msg.role === "user";
  const spans = msg.spans ?? [];

  const onCite = useCallback(
    (n: number) => {
      setExpanded(true);
      // wait for the panel to mount before scrolling
      requestAnimationFrame(() => {
        const el = document.getElementById(`apex-source-${sessionId}-${msg.id}-${n}`);
        if (!el) return;
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.classList.add("apex-source--flash");
        setTimeout(() => el.classList.remove("apex-source--flash"), 1200);
      });
    },
    [msg.id, sessionId],
  );

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(msg.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      /* clipboard unavailable (insecure context) */
    }
  }, [msg.text]);

  if (isUser) {
    return (
      <div className="apex-msg apex-msg--user">
        <div className="apex-bubble apex-bubble--user">{msg.text}</div>
      </div>
    );
  }

  const done = !msg.pending && !msg.streaming && !msg.error;
  return (
    <div className="apex-msg apex-msg--assistant">
      <div className="apex-avatar" aria-hidden>A</div>
      <div className="apex-msg-body">
        {msg.pending && (
          <div className="apex-pending" aria-label="thinking">
            <span className="apex-dot" /><span className="apex-dot" /><span className="apex-dot" />
          </div>
        )}

        {msg.error && <div className="apex-error-inline">⚠ {msg.error}</div>}

        {!msg.error && msg.refused && !msg.pending && (
          <div className="apex-refused">
            I can't answer that from the available sources
            {msg.refusalReason ? ` (${msg.refusalReason})` : ""}.
          </div>
        )}

        {!msg.error && !msg.refused && msg.text && (
          <div className={`apex-answer ${msg.streaming ? "apex-answer--streaming" : ""}`}>
            {renderRich(msg.text, spans.length, onCite)}
            {msg.streaming && <span className="apex-caret" aria-hidden />}
          </div>
        )}

        {msg.stopped && <div className="apex-stopped">Stopped</div>}

        {done && !msg.refused && msg.groundedness != null && (
          <div
            className={`apex-ground ${msg.groundedness >= 0.8 ? "apex-ground--ok" : "apex-ground--warn"}`}
            title="Share of each claim's content found in the sources it cites, with numbers checked exactly"
          >
            {msg.groundedness >= 0.8 ? "✓ Grounded" : "⚠ Weakly grounded"} · {Math.round(msg.groundedness * 100)}%
          </div>
        )}
        {done && msg.flags?.includes("prompt_injection") && (
          <div className="apex-ground apex-ground--bad">⛔ Blocked: looks like a prompt-injection attempt</div>
        )}

        {spans.length > 0 && !msg.pending && (
          <>
            <button type="button" className="apex-sources-toggle" onClick={() => setExpanded((v) => !v)}>
              {expanded ? "▾" : "▸"} Sources ({spans.length})
            </button>
            {expanded && (
              <div className="apex-sources">
                {spans.map((s, i) => (
                  <div key={i} id={`apex-source-${sessionId}-${msg.id}-${i + 1}`} className="apex-source">
                    <div className="apex-source-head">
                      <span className="apex-source-n">[{i + 1}]</span>
                      <span className="apex-source-id">{s.title || s.doc_id}</span>
                      <span className="apex-source-score">score {s.score.toFixed(4)}</span>
                    </div>
                    <div className="apex-source-text">{s.text}</div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {(done || msg.stopped || msg.error) && (
          <div className="apex-actions">
            {!msg.error && msg.text && (
              <button type="button" className="apex-act" onClick={copy} aria-label="copy answer" title="Copy">
                {copied ? "✓" : "⧉"}
              </button>
            )}
            {done && msg.traceId && (
              <>
                <button
                  type="button"
                  className={`apex-act ${msg.feedback === "up" ? "apex-act--on" : ""}`}
                  onClick={() => onFeedback("up")}
                  aria-label="good answer"
                  aria-pressed={msg.feedback === "up"}
                  title="Good answer"
                >
                  👍
                </button>
                <button
                  type="button"
                  className={`apex-act ${msg.feedback === "down" ? "apex-act--down" : ""}`}
                  onClick={() => onFeedback("down")}
                  aria-label="bad answer"
                  aria-pressed={msg.feedback === "down"}
                  title="Bad answer"
                >
                  👎
                </button>
              </>
            )}
            {isLastAssistant && !busy && (
              <button type="button" className="apex-act" onClick={onRegenerate} aria-label="regenerate" title="Regenerate">
                ↻
              </button>
            )}
            {msg.timing && (
              <span className="apex-msg-time" title={msg.traceId}>
                {msg.timing.total_ms.toFixed(0)} ms
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- Settings chip ---------- */

function SettingsChip({
  apiBase, apiKey, onBaseChange, onKeyChange,
}: {
  apiBase: string;
  apiKey: string;
  onBaseChange: (s: string) => void;
  onKeyChange: (s: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [baseInput, setBaseInput] = useState(apiBase);
  const [keyInput, setKeyInput] = useState(apiKey);
  const [saved, setSaved] = useState(false);

  useEffect(() => setBaseInput(apiBase), [apiBase]);
  useEffect(() => setKeyInput(apiKey), [apiKey]);

  const save = useCallback(() => {
    const b = baseInput.trim().replace(/\/+$/, "");
    const k = keyInput.trim();
    try {
      window.localStorage.setItem(API_BASE_STORAGE_KEY, b);
      window.localStorage.setItem(STORAGE_KEY, k);
    } catch {
      /* ignore */
    }
    onBaseChange(b);
    onKeyChange(k);
    setSaved(true);
    setTimeout(() => setSaved(false), 1200);
  }, [baseInput, keyInput, onBaseChange, onKeyChange]);

  return (
    <div className="apex-settings">
      <button type="button" className="apex-settings-btn" onClick={() => setOpen((v) => !v)} aria-label="settings">
        ⚙
      </button>
      {open && (
        <div className="apex-settings-panel">
          <label className="apex-settings-label" htmlFor="apex-chat-base">API base</label>
          <input
            id="apex-chat-base"
            className="apex-settings-input"
            value={baseInput}
            onChange={(e) => setBaseInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && save()}
            placeholder="http://localhost:8000"
          />
          <label className="apex-settings-label" htmlFor="apex-chat-key">X-API-Key</label>
          <input
            id="apex-chat-key"
            className="apex-settings-input"
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && save()}
            placeholder="devkey-change-me"
          />
          <button type="button" className="apex-settings-save" onClick={save}>
            {saved ? "saved" : "save"}
          </button>
        </div>
      )}
    </div>
  );
}
