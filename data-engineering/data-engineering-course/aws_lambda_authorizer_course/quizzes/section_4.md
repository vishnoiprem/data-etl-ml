# Section 4 Quiz — Request-Parameter Authorizer & Policy Cache

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** What does the `IdentitySource` define for a REQUEST
authorizer?

- A. The IAM role the authorizer assumes
- B. The fields from the request that make up the cache key
- C. The authorizer's source code
- D. The Lambda function's environment variables

<details><summary>Show answer</summary>

**B — The fields from the request that make up the cache key.**
For a request with `IdentitySource =
"method.request.querystring.user,method.request.querystring.token"`
and a request `?user=alice&token=xyz`, the cache key is
`alice,xyz`.

</details>

---

**Q2.** What's the maximum value of `ReauthorizeEvery`?

- A. 60 seconds
- B. 300 seconds (5 minutes)
- C. 3600 seconds (1 hour)
- D. 86400 seconds (24 hours)

<details><summary>Show answer</summary>

**C — 3600 seconds (1 hour).** The default is 300 s (5 minutes).
The minimum is 0 (no cache).

</details>

---

**Q3.** In a REQUEST authorizer event, how are HTTP header names
cased?

- A. The case the client used
- B. Lowercased
- C. Uppercased
- D. Camel-cased

<details><summary>Show answer</summary>

**B — Lowercased.** Always `headers.get("x-tenant")`, not
`headers.get("X-Tenant")`.

</details>

---

**Q4.** Which of these is **not** a valid `IdentitySource` value?

- A. `method.request.header.Authorization`
- B. `method.request.querystring.token`
- C. `requestContext.identity.sourceIp`
- D. `body`

<details><summary>Show answer</summary>

**D — `body`.** Bodies are large and variable; using the body as
a cache key would defeat the cache. None of the other three are
valid in the strict grammar either, but the closest valid form
would be `method.request.header.*` or `method.request.querystring.*`.

</details>

---

**Q5.** In the in-process LRU cache, what's the purpose of
`OrderedDict.move_to_end`?

- A. To sort entries by value
- B. To refresh the LRU position so a hot key doesn't get evicted
- C. To delete the entry
- D. To free memory

<details><summary>Show answer</summary>

**B — To refresh the LRU position so a hot key doesn't get
evicted.** When the cache is full, the entry that hasn't been
touched the longest is the next to be evicted.

</details>

---

**Q6.** Why do you need a `Lock` around the in-process cache?

- A. Lambda execution environments are single-threaded, so locks are unnecessary
- B. Lambda execution environments are multi-threaded; shared state must be guarded
- C. To prevent the cache from being deleted
- D. To enforce TTL

<details><summary>Show answer</summary>

**B — Lambda execution environments are multi-threaded; shared
state must be guarded.** Without a lock, two threads can read
and write the same entry simultaneously, causing race conditions.

</details>

---

**Q7.** What's the maximum stale-token exposure for an authorizer
with a 5-minute access token, a 5-minute `ReauthorizeEvery`, and a
5-minute internal cache TTL?

- A. 5 minutes
- B. 10 minutes
- C. 15 minutes
- D. The minimum of the three, i.e. 5 minutes

<details><summary>Show answer</summary>

**D — The minimum of the three, i.e. 5 minutes.** The bottleneck
is the shortest of the three TTLs. A revoked token is honored
for at most 5 minutes.

</details>

---

**Q8.** What happens to the in-process cache on a cold start?

- A. It's restored from the previous execution environment
- B. It's empty; the first request is always a miss
- C. It's loaded from S3
- D. The authorizer errors out

<details><summary>Show answer</summary>

**B — It's empty; the first request is always a miss.** Lambda
execution environments are not persisted across cold starts.

</details>

---

**Q9.** What's the right `IdentitySource` pattern when the same user
has multiple concurrent tokens (e.g. one per device)?

- A. `method.request.querystring.token` (token only)
- B. `method.request.querystring.user,method.request.querystring.token` (both)
- C. `method.request.querystring.user` (user only)
- D. The empty string (no cache)

<details><summary>Show answer</summary>

**B — Both.** Caching on the user alone would let device A's
expired token be honored by device B's request. Caching on both
keeps the entries distinct.

</details>

---

**Q10.** Why might you include `stageVariables` in the cache key?

- A. To save CloudWatch log space
- B. Because different stages may have different signing keys; otherwise a `staging` token could be honored on `prod`
- C. To reduce latency
- D. To avoid needing an environment variable

<details><summary>Show answer</summary>

**B — Because different stages may have different signing keys;
otherwise a `staging` token could be honored on `prod`.** A
common bug is to forget this when the same authorizer Lambda
serves multiple stages.

</details>

---

**Q11.** What is the difference between `queryStringParameters` and
`multiValueQueryStringParameters`?

- A. There is no difference
- B. Single-value form joins multi-value params with commas; multi-value form keeps them as a list
- C. Multi-value form joins with commas; single-value form keeps them as a list
- D. The single-value form is deprecated

<details><summary>Show answer</summary>

**B — Single-value form joins multi-value params with commas;
multi-value form keeps them as a list.** For most cases the
single-value form is sufficient.

</details>

---

**Q12.** When should the in-process LRU be `OrderedDict`-backed
rather than a plain `dict`?

- A. Always — the cost is identical
- B. Only when you need O(1) `move_to_end()` and `popitem(last=…)` for LRU semantics
- C. Only for caches larger than 1 GB
- D. Only on Python 2

<details><summary>Show answer</summary>

**B — Only when you need O(1) `move_to_end()` and
`popitem(last=…)` for LRU semantics.** Since Python 3.7, `dict` is
also insertion-ordered, but `move_to_end` is still
`OrderedDict`-only.

</details>
