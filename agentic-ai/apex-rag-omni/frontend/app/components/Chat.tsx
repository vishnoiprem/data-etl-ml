"use client";

/**
 * apex-rag-omni — Chat-style query UI.
 *
 * ChatGPT-like layout:
 *   - Left sidebar: collection selector (hr_policies / tech_docs /
 *     product_docs), a "+ new chat" action, and a "view traces" link.
 *   - Main column: scrollable thread (oldest at the bottom), empty
 *     state with three starter questions on first load.
 *   - Sticky input bar at the bottom: textarea (grows to 4 lines),
 *     collection chip, send button, Enter to send / Shift+Enter for
 *     newline.
 *
 * Each assistant message shows the answer with `[doc_N]` tokens turned
 * into clickable citation chips, plus a collapsible "Sources" panel
 * listing the cited spans (doc_id, text, score). Latency and trace_id
 * are shown on hover.
 *
 * Auth: the API key and base URL are read from localStorage (set
 * once in the header — see the saved-controls logic below). Same
 * shape as ApexRagOmni.tsx.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

type Collection = "hr_policies" | "tech_docs" | "product_docs";

interface Span {
  doc_id: string;
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
}

interface QueryResponse {
  trace_id: string;
  evidence: Evidence;
  timing_ms: {
    hybrid_ms: number;
    rerank_ms: number;
    answer_ms: number;
    total_ms: number;
  };
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  collection: Collection;
  // Only set on assistant messages:
  response?: QueryResponse;
  // Set while the request is in flight:
  pending?: boolean;
  error?: string;
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
  { id: "hr_policies",   label: "HR Policies",     hint: "PTO, benefits, conduct" },
  { id: "tech_docs",     label: "Tech Docs",       hint: "services, APIs, runbooks" },
  { id: "product_docs",  label: "Product Docs",    hint: "features, releases" },
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

function readKey(): string {
  if (typeof window === "undefined") return DEFAULT_API_KEY;
  return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_API_KEY;
}
function readApiBase(): string {
  if (typeof window === "undefined") return DEFAULT_API_BASE;
  return window.localStorage.getItem(API_BASE_STORAGE_KEY) ?? DEFAULT_API_BASE;
}
function loadSessions(): ChatSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(SESSIONS_STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as ChatSession[];
  } catch {
    return [];
  }
}
function saveSessions(sessions: ChatSession[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions));
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10);
}

function titleFor(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return "New chat";
  return trimmed.length > 40 ? trimmed.slice(0, 40) + "…" : trimmed;
}

/**
 * Render an assistant answer string, converting each `[doc_N]` token
 * into a numbered citation chip that scrolls to the corresponding
 * source card on click.
 */
function renderAnswerWithCitations(
  answer: string,
  spanCount: number,
  onCitationClick: (n: number) => void,
): React.ReactNode[] {
  // Tokens like `[doc_1]` (1-based, as produced by the answerer).
  const re = /\[doc_(\d+)\]/g;
  const out: React.ReactNode[] = [];
  let lastIndex = 0;
  let i = 0;
  for (const m of answer.matchAll(re)) {
    const start = m.index ?? 0;
    if (start > lastIndex) {
      out.push(answer.slice(lastIndex, start));
    }
    const n = parseInt(m[1], 10);
    const valid = n >= 1 && n <= spanCount;
    out.push(
      <button
        key={`cite-${i}-${start}`}
        type="button"
        className={`apex-cite ${valid ? "" : "apex-cite--invalid"}`}
        onClick={() => valid && onCitationClick(n)}
        title={valid ? `Jump to source ${n}` : "Citation out of range"}
        disabled={!valid}
      >
        {n}
      </button>,
    );
    lastIndex = start + m[0].length;
    i++;
  }
  if (lastIndex < answer.length) {
    out.push(answer.slice(lastIndex));
  }
  return out;
}

export default function Chat() {
  const [apiKey, setApiKey] = useState<string>(DEFAULT_API_KEY);
  const [apiBase, setApiBase] = useState<string>(DEFAULT_API_BASE);
  const [collection, setCollection] = useState<Collection>("hr_policies");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [draft, setDraft] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const inFlightRef = useRef<AbortController | null>(null);

  // Hydrate from localStorage on mount.
  useEffect(() => {
    setApiKey(readKey());
    setApiBase(readApiBase());
    const loaded = loadSessions();
    if (loaded.length > 0) {
      setSessions(loaded);
      setActiveId(loaded[0].id);
    } else {
      createSession("hr_policies", loaded).then(() => {});
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Persist sessions whenever they change.
  useEffect(() => {
    if (sessions.length > 0) saveSessions(sessions);
  }, [sessions]);

  // Auto-scroll to the bottom on new messages.
  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [sessions, activeId]);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeId) ?? null,
    [sessions, activeId],
  );

  const createSession = useCallback(
    async (col: Collection, base?: ChatSession[]) => {
      const list = base ?? sessions;
      const id = uid();
      const newSession: ChatSession = {
        id,
        title: "New chat",
        collection: col,
        createdAt: Date.now(),
        messages: [],
      };
      const next = [newSession, ...list];
      setSessions(next);
      setActiveId(id);
      setCollection(col);
      return newSession;
    },
    [sessions],
  );

  const updateActiveSession = useCallback(
    (updater: (s: ChatSession) => ChatSession) => {
      setSessions((prev) =>
        prev.map((s) => (s.id === activeId ? updater(s) : s)),
      );
    },
    [activeId],
  );

  const switchCollection = useCallback(
    (col: Collection) => {
      setCollection(col);
      if (activeSession) {
        updateActiveSession((s) => ({ ...s, collection: col }));
      } else {
        createSession(col);
      }
    },
    [activeSession, createSession, updateActiveSession],
  );

  const sendQuery = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || !activeSession) return;
      const userMsg: ChatMessage = {
        id: uid(),
        role: "user",
        text: trimmed,
        collection: activeSession.collection,
      };
      const pendingMsg: ChatMessage = {
        id: uid(),
        role: "assistant",
        text: "",
        collection: activeSession.collection,
        pending: true,
      };
      updateActiveSession((s) => ({
        ...s,
        title: s.messages.length === 0 ? titleFor(trimmed) : s.title,
        messages: [...s.messages, userMsg, pendingMsg],
      }));
      setDraft("");
      inputRef.current?.focus();

      // Abort any prior in-flight request (safety, shouldn't happen).
      inFlightRef.current?.abort();
      const ctrl = new AbortController();
      inFlightRef.current = ctrl;

      try {
        const res = await fetch(`${apiBase}/query`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": apiKey,
          },
          body: JSON.stringify({
            collection: activeSession.collection,
            query: trimmed,
          }),
          signal: ctrl.signal,
        });
        if (res.status === 403) {
          throw new Error(
            "API key rejected. Open Settings (top right) and set the matching X-API-Key.",
          );
        }
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${await res.text()}`);
        }
        const data = (await res.json()) as QueryResponse;
        updateActiveSession((s) => ({
          ...s,
          messages: s.messages.map((m) =>
            m.id === pendingMsg.id
              ? { ...m, pending: false, response: data, text: data.evidence.answer }
              : m,
          ),
        }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Request failed";
        updateActiveSession((s) => ({
          ...s,
          messages: s.messages.map((m) =>
            m.id === pendingMsg.id
              ? { ...m, pending: false, error: msg, text: msg }
              : m,
          ),
        }));
      }
    },
    [activeSession, apiBase, apiKey, updateActiveSession],
  );

  const onSubmit = useCallback(
    (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      sendQuery(draft);
    },
    [draft, sendQuery],
  );

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendQuery(draft);
      }
    },
    [draft, sendQuery],
  );

  const scrollToCitation = useCallback((n: number) => {
    const el = document.getElementById(`apex-source-${activeId}-${n}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("apex-source--flash");
      setTimeout(() => el.classList.remove("apex-source--flash"), 1200);
    }
  }, [activeId]);

  const starters = STARTERS[activeSession?.collection ?? collection];

  return (
    <div className={`apex-chat ${sidebarOpen ? "" : "apex-chat--collapsed"}`}>
      {/* Sidebar */}
      <aside className="apex-sidebar">
        <button
          type="button"
          className="apex-newchat"
          onClick={() => createSession(collection)}
        >
          + New chat
        </button>

        <div className="apex-sidebar-section">
          <div className="apex-sidebar-label">Collection</div>
          {COLLECTIONS.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`apex-collection ${
                collection === c.id ? "apex-collection--on" : ""
              }`}
              onClick={() => switchCollection(c.id)}
              title={c.hint}
            >
              {c.label}
            </button>
          ))}
        </div>

        <div className="apex-sidebar-section">
          <div className="apex-sidebar-label">History</div>
          {sessions.length === 0 && (
            <div className="apex-sidebar-empty">no chats yet</div>
          )}
          {sessions.map((s) => (
            <button
              key={s.id}
              type="button"
              className={`apex-session ${
                s.id === activeId ? "apex-session--on" : ""
              }`}
              onClick={() => {
                setActiveId(s.id);
                setCollection(s.collection);
              }}
            >
              {s.title}
            </button>
          ))}
        </div>

        <div className="apex-sidebar-section apex-sidebar-bottom">
          <a
            className="apex-traces-link"
            href="/traces"
            target="_blank"
            rel="noreferrer"
          >
            View trace reviewer →
          </a>
        </div>
      </aside>

      {/* Main */}
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
            apex-rag-omni · <span className={`apex-pill apex-pill--${collection}`}>
              {COLLECTIONS.find((c) => c.id === collection)?.label}
            </span>
          </h1>
          <SettingsChip
            apiBase={apiBase}
            apiKey={apiKey}
            onBaseChange={setApiBase}
            onKeyChange={setApiKey}
          />
        </header>

        <div className="apex-scroll" ref={scrollerRef}>
          {activeSession && activeSession.messages.length === 0 && (
            <div className="apex-empty">
              <h2>Ask a question</h2>
              <p>
                You are chatting with{" "}
                <strong>
                  {COLLECTIONS.find((c) => c.id === collection)?.label}
                </strong>
                . Answers are grounded in the cited sources below each reply.
              </p>
              <div className="apex-starters">
                {starters.map((s, i) => (
                  <button
                    key={i}
                    type="button"
                    className="apex-starter"
                    onClick={() => sendQuery(s)}
                  >
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
              onCitation={scrollToCitation}
            />
          ))}
        </div>

        <form className="apex-inputbar" onSubmit={onSubmit}>
          <textarea
            ref={inputRef}
            className="apex-input"
            placeholder={`Ask ${COLLECTIONS.find((c) => c.id === collection)?.label.toLowerCase()}…`}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            disabled={!activeSession}
          />
          <button
            type="submit"
            className="apex-send"
            disabled={!draft.trim() || !activeSession}
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}

/* ---------- Message row ---------- */

function MessageRow({
  msg,
  sessionId,
  onCitation,
}: {
  msg: ChatMessage;
  sessionId: string;
  onCitation: (n: number) => void;
}) {
  const [expanded, setExpanded] = useState<boolean>(false);
  const isUser = msg.role === "user";

  const resp = msg.response;
  const spans = resp?.evidence.spans ?? [];
  const refused = resp?.evidence?.refused ?? false;
  const timing = resp?.timing_ms;
  const traceId = resp?.trace_id;

  return (
    <div className={`apex-msg apex-msg--${msg.role}`}>
      <div className="apex-msg-meta">
        {isUser ? "you" : "apex-rag-omni"}
        {resp && (
          <span className="apex-msg-time" title={traceId}>
            · {timing?.total_ms?.toFixed(0) ?? "?"} ms
          </span>
        )}
      </div>

      <div className={`apex-bubble apex-bubble--${msg.role}`}>
        {msg.pending && (
          <div className="apex-pending">
            <span className="apex-dot" />
            <span className="apex-dot" />
            <span className="apex-dot" />
          </div>
        )}

        {msg.error && <div className="apex-error-inline">error: {msg.error}</div>}

        {!msg.pending && !msg.error && isUser && <div>{msg.text}</div>}

        {!msg.pending && !msg.error && !isUser && resp && (
          <>
            {refused ? (
              <div className="apex-refused">
                refused: {resp.evidence.refusal_reason ?? "insufficient evidence"}
              </div>
            ) : (
              <div className="apex-answer">
                {renderAnswerWithCitations(resp.evidence.answer, spans.length, onCitation)}
              </div>
            )}

            {spans.length > 0 && (
              <button
                type="button"
                className="apex-sources-toggle"
                onClick={() => setExpanded((v) => !v)}
              >
                {expanded ? "▾" : "▸"} Sources ({spans.length})
              </button>
            )}

            {expanded && spans.length > 0 && (
              <div className="apex-sources">
                {spans.map((s, i) => {
                  const n = i + 1;
                  return (
                    <div
                      key={n}
                      id={`apex-source-${sessionId}-${n}`}
                      className="apex-source"
                    >
                      <div className="apex-source-head">
                        <span className="apex-source-n">[{n}]</span>
                        <span className="apex-source-id">{s.doc_id}</span>
                        <span className="apex-source-score">
                          score {s.score.toFixed(4)}
                        </span>
                      </div>
                      <div className="apex-source-text">{s.text}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ---------- Settings chip ---------- */

function SettingsChip({
  apiBase,
  apiKey,
  onBaseChange,
  onKeyChange,
}: {
  apiBase: string;
  apiKey: string;
  onBaseChange: (s: string) => void;
  onKeyChange: (s: string) => void;
}) {
  const [open, setOpen] = useState<boolean>(false);
  const [baseInput, setBaseInput] = useState<string>(apiBase);
  const [keyInput, setKeyInput] = useState<string>(apiKey);
  const [saved, setSaved] = useState<boolean>(false);

  useEffect(() => setBaseInput(apiBase), [apiBase]);
  useEffect(() => setKeyInput(apiKey), [apiKey]);

  const save = useCallback(() => {
    const b = baseInput.trim().replace(/\/+$/, "");
    const k = keyInput.trim();
    if (typeof window !== "undefined") {
      window.localStorage.setItem(API_BASE_STORAGE_KEY, b);
      window.localStorage.setItem(STORAGE_KEY, k);
    }
    onBaseChange(b);
    onKeyChange(k);
    setSaved(true);
    setTimeout(() => setSaved(false), 1200);
  }, [baseInput, keyInput, onBaseChange, onKeyChange]);

  return (
    <div className="apex-settings">
      <button
        type="button"
        className="apex-settings-btn"
        onClick={() => setOpen((v) => !v)}
        aria-label="settings"
      >
        ⚙
      </button>
      {open && (
        <div className="apex-settings-panel">
          <label className="apex-settings-label" htmlFor="apex-chat-base">
            API base
          </label>
          <input
            id="apex-chat-base"
            className="apex-settings-input"
            value={baseInput}
            onChange={(e) => setBaseInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") save();
            }}
            placeholder="http://localhost:8000"
          />
          <label className="apex-settings-label" htmlFor="apex-chat-key">
            X-API-Key
          </label>
          <input
            id="apex-chat-key"
            className="apex-settings-input"
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") save();
            }}
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