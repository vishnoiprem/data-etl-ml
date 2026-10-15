import { useQuery } from '@tanstack/react-query';
import { fetchTrace, submitFeedback } from '../api/client';
import { useState } from 'react';

interface Props {
  traceId: string;
}

export function TraceDetail({ traceId }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['trace', traceId],
    queryFn: ({ signal }) => fetchTrace(traceId, signal),
    enabled: !!traceId,
  });
  const [busy, setBusy] = useState<'up' | 'down' | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function rate(rating: 'up' | 'down') {
    setErr(null);
    setBusy(rating);
    try {
      await submitFeedback(traceId, rating);
      // soft reload
      window.location.reload();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  if (isLoading) return <div className="p-4">Loading trace…</div>;
  if (error) return <div className="p-4 text-red-600">{(error as Error).message}</div>;
  if (!data) return null;

  return (
    <div className="p-4 space-y-3" data-testid="trace-detail">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-lg font-semibold">{data.trace_id}</h2>
          <div className="text-xs text-gray-500">
            {data.created_at} · {data.prompt_version} · {data.status} · {data.latency_ms}ms ·{' '}
            {data.token_usage} tokens
          </div>
        </div>
        <div className="flex gap-2">
          <button
            disabled={busy !== null}
            onClick={() => rate('up')}
            className="px-3 py-1 border rounded hover:bg-green-50"
          >
            👍 Up
          </button>
          <button
            disabled={busy !== null}
            onClick={() => rate('down')}
            className="px-3 py-1 border rounded hover:bg-red-50"
          >
            👎 Down
          </button>
        </div>
      </div>
      {err && <div className="text-red-600 text-sm">{err}</div>}
      <section>
        <h3 className="font-semibold">User query</h3>
        <p className="bg-gray-50 p-2 rounded">{data.user_query}</p>
      </section>
      <section>
        <h3 className="font-semibold">Prompt</h3>
        <pre className="bg-gray-50 p-2 rounded text-xs whitespace-pre-wrap">
          {data.prompt}
        </pre>
      </section>
      <section>
        <h3 className="font-semibold">Retrieved chunks</h3>
        <ul className="space-y-1">
          {data.retrieved_chunks.map((c) => (
            <li key={c.chunk_id} className="bg-gray-50 p-2 rounded text-sm">
              <span className="font-mono text-xs">{c.chunk_id}</span> · score {c.score} ·{' '}
              {c.text}
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="font-semibold">Model response</h3>
        <p className="bg-gray-50 p-2 rounded">{data.model_response}</p>
      </section>
      <section>
        <h3 className="font-semibold">Citations</h3>
        <ul className="text-sm list-disc pl-5">
          {data.citations.map((c) => (
            <li key={c.chunk_id}>
              {c.source} → {c.chunk_id} (score {c.score})
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
