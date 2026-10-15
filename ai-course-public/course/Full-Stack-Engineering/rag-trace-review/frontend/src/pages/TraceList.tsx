import { useMemo, useState } from 'react';
import { useInfiniteTraces, useSubmitFeedback } from '../hooks/useInfiniteTraces';
import { TraceTable } from '../components/TraceRow';
import { FilterBar } from '../components/FilterBar';
import { TraceDetail } from './TraceDetail';
import type { TraceFilters, TraceSummary } from '../types';

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

  function handleRowClick(id: string) {
    setSelected(id);
  }

  async function optimisticRate(id: string, rating: 'up' | 'down') {
    try {
      await submit.mutateAsync({ id, rating });
    } catch {
      // rollback handled by hook
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
      <div>
        <h1 className="text-xl font-bold mb-2">RAG Traces</h1>
        <FilterBar initial={filters} onChange={setFilters} />
        {isLoading && <div className="p-4">Loading…</div>}
        {isError && (
          <div className="p-4 text-red-600">{(error as Error).message}</div>
        )}
        <div className="mt-2">
          <TraceTable rows={rows} onSelect={handleRowClick} selectedId={selected ?? undefined} />
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
              onClick={() => optimisticRate(selected, 'up')}
              className="px-2 py-1 border rounded"
            >
              👍
            </button>
            <button
              onClick={() => optimisticRate(selected, 'down')}
              className="px-2 py-1 border rounded"
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
