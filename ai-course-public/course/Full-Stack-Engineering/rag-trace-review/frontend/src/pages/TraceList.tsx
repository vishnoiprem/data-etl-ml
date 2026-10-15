import { useMemo, useState } from 'react';
import { useInfiniteTraces, useSubmitFeedback } from '../hooks/useInfiniteTraces';
import { TraceTable } from '../components/TraceRow';
import { FilterBar } from '../components/FilterBar';
import { TraceDetail } from './TraceDetail';
import type { Rating, TraceFilters, TraceSummary } from '../types';

export function TraceList() {
  const [filters, setFilters] = useState<TraceFilters>({});
  const [selected, setSelected] = useState<string | null>(null);
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteTraces(filters);
  const submit = useSubmitFeedback();

  const rows: TraceSummary[] = useMemo(
    () => data?.pages.flatMap((p) => p.items) ?? [],
    [data]
  );

  function rate(id: string, rating: Rating) {
    submit.mutate({ id, rating });
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
      <div>
        <h1 className="text-xl font-bold mb-2">RAG Traces</h1>
        <FilterBar initial={filters} onChange={setFilters} />
        {isLoading && <div className="p-4">Loading…</div>}
        {isError && (
          <div className="p-4 text-red-600" role="alert">{(error as Error).message}</div>
        )}
        <div className="mt-2">
          <TraceTable rows={rows} onSelect={setSelected} selectedId={selected ?? undefined} />
        </div>
        <div className="flex gap-2 items-center mt-2">
          <button
            disabled={!hasNextPage || isFetchingNextPage}
            onClick={() => fetchNextPage()}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            {isFetchingNextPage ? 'Loading…' : hasNextPage ? 'Load more' : 'End'}
          </button>
          <span className="text-xs text-gray-500">
            {rows.length} loaded · {data?.pages.length ?? 0} pages
          </span>
        </div>
        {selected && (
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => rate(selected, 'up')}
              disabled={submit.isPending}
              className="px-2 py-1 border rounded"
              aria-label="Thumbs up"
            >
              👍
            </button>
            <button
              onClick={() => rate(selected, 'down')}
              disabled={submit.isPending}
              className="px-2 py-1 border rounded"
              aria-label="Thumbs down"
            >
              👎
            </button>
          </div>
        )}
      </div>
      <div className="border-l pl-4">
        {selected ? (
          <TraceDetail traceId={selected} />
        ) : (
          <div className="text-gray-500 p-4">Select a trace to inspect</div>
        )}
      </div>
    </div>
  );
}
