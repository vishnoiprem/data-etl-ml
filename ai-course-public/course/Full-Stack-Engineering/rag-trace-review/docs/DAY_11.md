# Day 11 — Optimistic UI
**Module 11** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Optimistic UI is **lying to the user in a helpful way**. You assume the message delivered and you show the user the result immediately. If it didn't, you quietly say "actually, that didn't work."

It's like texting "delivered" before the cell tower confirms. If the tower says no, you show "not delivered" and try again.

---

## 2. Technical concepts (20 min)

1. User clicks.
2. We patch the **cache** (TanStack Query) to reflect the new state.
3. We send the request.
4. On success, the server's response is canonical; we invalidate or merge.
5. On error, we **roll back** the cache to the snapshot we took in step 2.

```ts
onMutate: async ({ id, rating }) => {
  await qc.cancelQueries({ queryKey: ['traces'] });
  const snapshots = qc.getQueriesData({ queryKey: ['traces'] });
  // patch each cached page
  return { snapshots };
},
onError: (_e, _v, ctx) => { ctx?.snapshots.forEach(([k, d]) => qc.setQueryData(k, d)); },
onSettled: () => qc.invalidateQueries({ queryKey: ['traces'] }),
```

### When NOT to use it
- Money transfers (always show the truth).
- Anything that triggers an irreversible external action.
- Anything where the rollback is expensive.

### Race conditions
- Cancel in-flight queries before patching: `qc.cancelQueries`.
- Use idempotency keys on the server for non-idempotent operations.

---

## 3. Coding (30 min)

Open `frontend/src/hooks/useInfiniteTraces.ts`. Read the optimistic update.

Add a `useDeleteTrace` mutation that removes a row from every cached page immediately.

```ts
export function useDeleteTrace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => fetch(`${BASE}/traces/${id}`, { method: 'DELETE' }),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: TRACES_KEY });
      const snaps = qc.getQueriesData({ queryKey: TRACES_KEY });
      snaps.forEach(([k, d]: any) => qc.setQueryData(k, { ...d, pages: d.pages.map((p: TracePage) => ({ ...p, items: p.items.filter(t => t.trace_id !== id) })) }));
      return { snaps };
    },
    onError: (_e, _v, ctx) => ctx?.snaps.forEach(([k, d]: any) => qc.setQueryData(k, d)),
    onSettled: () => qc.invalidateQueries({ queryKey: TRACES_KEY }),
  });
}
```

### Sample I/O
- Click delete → row disappears instantly.
- Server fails → row reappears.

### Line-by-line
- `cancelQueries` prevents a refetch from overwriting the patch.
- `getQueriesData` returns every cached page.
- Returning the snapshot lets `onError` roll back.

---

## 4. Debugging & tests (20 min)

### Bug 1: forgot `cancelQueries`
**Symptom:** optimistic state overwritten by a refetch.
**Fix:** call `cancelQueries` first.

### Bug 2: forgot snapshot
**Symptom:** cache permanently wrong on error.
**Fix:** return `{ snapshots }` from `onMutate`.

### Bug 3: not invalidating on success
**Symptom:** server data doesn't reach the UI.
**Fix:** `onSettled` invalidates.

### Bug 4: duplicate clicks
**Fix:** disable the button with `mutation.isPending` or guard inside the mutation.

### Test
```ts
test('rolls back on failure', async () => {
  server.use(rest.put('/traces/t1/feedback', (req, res, ctx) => res(ctx.status(500))));
  // click + assert revert
});
```

---

## 5. Mock interview practice (20 min)

**Q1 — "What if the user double-clicks?"**
> Disable the button or guard inside the mutation.

**Q2 — "What if the server returns a different value?"**
> Reconcile in `onSettled` with a refetch.

**Q3 — "When NOT to use optimistic?"**
> Money transfers. Always show the truth.

**Q4 — "What is the staleness window?"**
> How long the optimistic state lives before the server overrides it.

**Q5 — "What's the difference between `onSuccess` and `onSettled`?"**
> `onSuccess` runs only on success; `onSettled` runs always (success or error).

---

## 6. Success criteria check
- [ ] I can write a mutation with onMutate/onError/onSettled.
- [ ] I can cancel in-flight queries.
- [ ] I can roll back on error.
- [ ] I can disable a button while pending.
- [ ] I can test the rollback.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

## 8. Coding assignment
**Add a `useUndoFeedback` mutation that reverses the last feedback change within 5 seconds.**

### Rubric (0–10)
- 0: doesn't compile
- 4: shows toast
- 6: undo button works
- 8: 5s timeout
- 10: keyboard shortcut + accessible

### Solution
```ts
const lastRef = useRef<{id:string; prev: Rating|null} | null>(null);
function withUndo(id: string, rating: Rating) {
  const prev = lastRef.current?.prev ?? null;
  submit.mutate({ id, rating });
  lastRef.current = { id, prev };
  setTimeout(() => { lastRef.current = null; }, 5000);
}
```

**Time: 90 min**