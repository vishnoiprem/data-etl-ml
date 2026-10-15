import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchTraces, submitFeedback } from '../api/client';
import type { TraceFilters, Rating, TracePage, TraceSummary } from '../types';

// Centralized cache keys: every traces query uses the same prefix
// so optimistic updates and invalidations cover all filters.
const TRACES_KEY = ['traces'] as const;

export function useInfiniteTraces(filters: TraceFilters) {
  return useInfiniteQuery<TracePage, Error>({
    queryKey: [...TRACES_KEY, filters],
    queryFn: ({ pageParam, signal }) => fetchTraces(filters, pageParam as string | null, signal),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.meta.next_cursor ?? undefined,
  });
}

export function useSubmitFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, rating }: { id: string; rating: Rating }) =>
      submitFeedback(id, rating),
    onMutate: async ({ id, rating }) => {
      await qc.cancelQueries({ queryKey: TRACES_KEY });
      const snapshots = qc.getQueriesData<{ pages: TracePage[]; pageParams: unknown[] }>({
        queryKey: TRACES_KEY,
      });
      snapshots.forEach(([key, data]) => {
        if (!data) return;
        const next = {
          ...data,
          pages: data.pages.map((p) => ({
            ...p,
            items: p.items.map((t: TraceSummary) =>
              t.trace_id === id ? { ...t, feedback: rating } : t
            ),
          })),
        };
        qc.setQueryData(key, next);
      });
      return { snapshots };
    },
    onError: (_e, _v, ctx) => {
      ctx?.snapshots.forEach(([key, data]) => qc.setQueryData(key, data));
    },
    onSettled: () => qc.invalidateQueries({ queryKey: TRACES_KEY }),
  });
}
