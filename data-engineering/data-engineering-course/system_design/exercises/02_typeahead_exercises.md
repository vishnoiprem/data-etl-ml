# Exercises — Typeahead

## 1. Add typo correction
Right now "fals" gets no suggestions. Add Levenshtein distance-1
fallback: if the prefix has no node, try removing one character and
re-querying.

## 2. Add per-language dictionaries
Load multiple JSONL files (e.g. `dictionary_en.jsonl`, `dictionary_es.jsonl`).
Route by `Accept-Language` header. Document the shard strategy.

## 3. Add personalization
Track per-user query history; bias results toward prior queries'
top words.

## 4. Make K configurable per query
The path argument `&k=10` is already there — verify it.

## 5. Add an FST implementation
The trie is simple but bloated. Try replacing it with an FST (or
`marisa-trie` if you want to use a library) and measure the memory
delta.

## 6. Add a "did you mean" endpoint
If the user submits a query that exists nowhere (the trie has it as a
leaf but no prefix siblings), suggest a close match using edit
distance.

## 7. Add metrics for cache effectiveness
Expose `/metrics` cache hit rate. Set an alert when <80%.

## 8. Build a tiny frontend
Wrap the service in a 30-line HTML page that calls `/suggest?q=` on
every keydown and shows the dropdown.
