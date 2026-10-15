# Day 11 — Optimistic UI

## 1. Analogy
Optimistic UI is **lying to the user in a helpful way**. You assume the message delivered, and you show the user the result immediately. If it didn't, you quietly say "actually, that didn't work."

## 2. Technical concept
1. User clicks.
2. We patch the **cache** (TanStack Query) to reflect the new state.
3. We send the request.
4. On success, the server's response is canonical; we invalidate or merge.
5. On error, we **roll back** the cache to the snapshot we took in step 2.

## 3. Why
A round-trip to the server is 100–500ms. Optimistic UI feels instant.

## 4. Data flow
onMutate → snapshot → setQueryData → mutationFn → onSuccess/onError (rollback) → onSettled (invalidate).

## 5. Example (already in `useInfiniteTraces.ts`)
```ts
onMutate: async ({ id, rating }) => {
  await qc.cancelQueries({ queryKey: ['traces'] });
  const snapshots = qc.getQueriesData({ queryKey: ['traces'] });
  // patch each query
  return { snapshots };
},
onError: (_e, _v, ctx) => { ctx?.snapshots.forEach(([k, d]) => qc.setQueryData(k, d)); },
onSettled: () => qc.invalidateQueries({ queryKey: ['traces'] }),
```

## 6. Line-by-line
- `cancelQueries` prevents a refetch from overwriting our patch.
- `getQueriesData` returns every cached page.
- `setQueryData` writes the patched value.
- Returning the snapshot lets `onError` roll back.

## 7. I/O
- Click 👍 → instant emoji.
- Server fails → emoji reverts, error toast.

## 8. Bugs
- Forgetting `cancelQueries` → race.
- Forgetting snapshot → permanent wrong state.
- Not invalidating on success → stale forever.

## 9. Tests
Use a mock mutation that throws; assert the cache reverts.

## 10. Performance
- Optimistic updates are basically free.
- Invalidation triggers a refetch; debounce if expensive.

## 11. Five Q&As
1. **What if the user double-clicks?** Disable the button or guard inside the mutation.
2. **What if the server returns a different value?** Reconcile in `onSettled`.
3. **What if the request ordering matters?** Use idempotency keys on the server.
4. **When NOT to use optimistic?** Money transfers. Always show the truth.
5. **What is the staleness window?** How long the optimistic state lives.

## 12. Coding assignment
Add a `useDeleteOptimistic` mutation that removes a row from the table immediately.

## 13. Solution
```ts
export function useDeleteTrace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => fetch(`${BASE}/traces/${id}`, {method:'DELETE'}),
    onMutate: async (id) => {
      await qc.cancelQueries({queryKey:['traces']});
      const snaps = qc.getQueriesData({queryKey:['traces']});
      snaps.forEach(([k, d]) => qc.setQueryData(k, {...d, pages: d.pages.map(p => ({...p, items: p.items.filter(t => t.trace_id !== id)}))}));
      return { snaps };
    },
    onError: (_e, _v, ctx) => ctx?.snaps.forEach(([k,d]) => qc.setQueryData(k, d)),
    onSettled: () => qc.invalidateQueries({queryKey:['traces']}),
  });
}
```
- 0: doesn't compile
- 4: removes from cache
- 6: rollback
- 8: cancel before patch
- 10: handles delete API endpoint

**Time: 90 min**