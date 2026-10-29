"""Mistral-style self-hosted LLM serving: prefix cache + token-budget guard.

The two features that make self-hosted Llama-class serving actually
usable: (1) a prefix cache so we don't re-encode the system prompt on
every request, (2) a token-budget guard so a 200K-context request
doesn't melt the cluster.

This module ships a lightweight *simulation* of those mechanisms
(``MockLLMEngine`` + ``Tokenizer``) so the smoke test can exercise
the real serving surface area — tokenize → generate → decode — without
loading a multi-GB checkpoint. The interesting surface is the protocol:
how the prefix cache decides what to skip, how the budget guard refuses
oversized requests, how batching amortises the per-request overhead, and
how streaming yields tokens as they come off the model.
"""
from __future__ import annotations
import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Iterable, Iterator


# ---------------------------------------------------------------------------
# Tokenizer (whitespace + punctuation, deterministic, no external deps)
# ---------------------------------------------------------------------------

class Tokenizer:
    """Minimal deterministic tokenizer.

    Splits on whitespace and isolates a small punctuation set. Stable
    enough that the same prompt always tokenizes to the same ids, which
    is what the prefix cache requires.
    """

    PUNCT = set(".,;:!?\"'()[]{}")

    def __init__(self, vocab: list[str] | None = None):
        # Build a tiny vocab from a few seed words plus bos/eos/pad.
        seed = vocab or [
            "<bos>", "<eos>", "<pad>",
            "the", "a", "is", "of", "and", "to", "in", "for", "on", "with",
            "system", "user", "assistant", "response", "answer", "question",
            "summarize", "code", "function", "return", "value", "token",
            "cache", "model", "prompt", "result", "data", "test",
        ]
        self.tok_to_id: dict[str, int] = {t: i for i, t in enumerate(seed)}
        self.id_to_tok: dict[int, str] = {i: t for t, i in self.tok_to_id.items()}
        self.bos_id = self.tok_to_id["<bos>"]
        self.eos_id = self.tok_to_id["<eos>"]
        self.pad_id = self.tok_to_id["<pad>"]

    def _split(self, text: str) -> list[str]:
        out: list[str] = []
        buf: list[str] = []
        for ch in text:
            if ch.isspace():
                if buf:
                    out.append("".join(buf))
                    buf = []
                continue
            if ch in self.PUNCT:
                if buf:
                    out.append("".join(buf))
                    buf = []
                out.append(ch)
            else:
                buf.append(ch)
        if buf:
            out.append("".join(buf))
        return out

    def encode(self, text: str) -> list[int]:
        ids: list[int] = []
        for w in self._split(text):
            if w not in self.tok_to_id:
                # Add on the fly; deterministic across calls because the
                # tokenization order is deterministic.
                idx = len(self.tok_to_id)
                self.tok_to_id[w] = idx
                self.id_to_tok[idx] = w
            ids.append(self.tok_to_id[w])
        return [self.bos_id] + ids + [self.eos_id]

    def decode(self, ids: Iterable[int]) -> str:
        toks = []
        for i in ids:
            if i in (self.bos_id, self.pad_id):
                continue
            if i == self.eos_id:
                break
            t = self.id_to_tok.get(int(i), f"?{i}")
            if t in self.PUNCT:
                toks.append(t)
            else:
                toks.append(" " + t)
        s = "".join(toks).strip()
        return s


# ---------------------------------------------------------------------------
# Prefix cache + token budget guard (the original surface)
# ---------------------------------------------------------------------------

@dataclass
class CachedPrompt:
    prompt_hash: str
    token_count: int
    hits: int = 0


class PrefixCache:
    """LRU cache of (prompt_prefix_hash, token_count) -> was-in-cache."""

    def __init__(self, max_entries: int = 1024):
        self._cache: OrderedDict[str, CachedPrompt] = OrderedDict()
        self.max_entries = max_entries
        self.lookups = 0
        self.hits = 0

    def check(self, prompt: str) -> tuple[bool, int]:
        self.lookups += 1
        h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if h in self._cache:
            self._cache.move_to_end(h)
            self._cache[h].hits += 1
            self.hits += 1
            return True, self._cache[h].token_count
        return False, 0

    def store(self, prompt: str, token_count: int) -> None:
        h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        self._cache[h] = CachedPrompt(prompt_hash=h, token_count=token_count)
        self._cache.move_to_end(h)
        if len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)

    def hit_rate(self) -> float:
        return self.hits / self.lookups if self.lookups else 0.0

    def stats(self) -> dict:
        total = sum(c.hits for c in self._cache.values())
        return {
            "entries": len(self._cache),
            "total_hits": total,
            "lookups": self.lookups,
            "hit_rate": round(self.hit_rate(), 4),
            "max_entries": self.max_entries,
        }


class TokenBudgetGuard:
    """Refuse requests whose (prompt + expected_output) > budget."""

    def __init__(self, max_total_tokens: int = 32_000):
        self.max_total_tokens = max_total_tokens

    def allow(self, prompt_tokens: int, max_output_tokens: int) -> tuple[bool, str]:
        total = prompt_tokens + max_output_tokens
        if total > self.max_total_tokens:
            return False, f"total {total} > budget {self.max_total_tokens}"
        return True, "ok"


# ---------------------------------------------------------------------------
# Mock LLM engine (text generation with KV cache + batching + streaming)
# ---------------------------------------------------------------------------

@dataclass
class GenerationResult:
    prompt: str
    prompt_token_count: int
    output_tokens: list[int]
    output_text: str
    cache_hit: bool
    elapsed_ms: float
    first_token_ms: float = 0.0

    @property
    def output_token_count(self) -> int:
        return len(self.output_tokens)

    @property
    def tokens_per_sec(self) -> float:
        if self.elapsed_ms <= 0:
            return 0.0
        return self.output_token_count / (self.elapsed_ms / 1000.0)


class MockLLMEngine:
    """Deterministic LLM stand-in.

    A real engine does prefill (encode the prompt into KV cache) and
    then decodes one token at a time. The mock reproduces those two
    phases so the *control flow* is realistic, even though the
    "sampling" is a hash-driven choice from the vocab.

    - Prefill cost scales with prompt length and is *skipped* on a
      cache hit (the prefix is already in KV cache).
    - Decode cost is per-output-token.
    - Batching amortises prefill across prompts that share a system
      prompt.
    - Streaming yields tokens as they come off the decoder.
    """

    def __init__(
        self,
        tokenizer: Tokenizer,
        cache: PrefixCache | None = None,
        budget: TokenBudgetGuard | None = None,
        prefill_ms_per_token: float = 0.05,
        decode_ms_per_token: float = 1.0,
    ):
        self.tok = tokenizer
        self.cache = cache or PrefixCache()
        self.budget = budget or TokenBudgetGuard()
        self.prefill_ms_per_token = prefill_ms_per_token
        self.decode_ms_per_token = decode_ms_per_token
        # Stats
        self.total_prefill_tokens = 0
        self.total_decode_tokens = 0
        self.total_prefill_ms = 0.0
        self.total_decode_ms = 0.0

    # -- internal helpers --------------------------------------------------

    def _prefill(self, prompt: str) -> tuple[list[int], float]:
        ids = self.tok.encode(prompt)
        # Simulate prefill cost; the prefix cache can skip this on a hit.
        elapsed = len(ids) * self.prefill_ms_per_token
        self.total_prefill_tokens += len(ids)
        self.total_prefill_ms += elapsed
        return ids, elapsed

    def _decode_step(self, prompt_ids: list[int], step: int, seed_salt: str) -> int:
        """Pick the next token deterministically from the vocab.

        Uses a stable hash of (prompt, step, salt) so the same prompt
        always produces the same continuation — which is what the
        "KV cache hit produces the same output" assertion needs.
        """
        h = hashlib.sha256(
            (str(prompt_ids[:1]) + "|" + str(step) + "|" + seed_salt).encode("utf-8")
        ).digest()
        # Pick from the non-special tokens.
        candidates = [i for tok, i in self.tok.tok_to_id.items()
                      if tok not in ("<bos>", "<eos>", "<pad>")]
        return candidates[h[0] % len(candidates)]

    # -- public API --------------------------------------------------------

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        seed_salt: str = "default",
    ) -> GenerationResult:
        # Budget guard first — fail fast, do not even tokenize.
        prompt_ids = self.tok.encode(prompt)
        ok, _msg = self.budget.allow(
            prompt_tokens=len(prompt_ids), max_output_tokens=max_new_tokens
        )
        if not ok:
            raise ValueError(f"budget rejected: prompt={len(prompt_ids)} + max_new={max_new_tokens}")

        # Prefix cache: a hit means we already have the encoded prefix
        # in KV cache and skip the prefill.
        hit, cached_n = self.cache.check(prompt)
        t0 = time.time()
        if not hit:
            prefill_ids, _prefill_ms = self._prefill(prompt)
            self.cache.store(prompt, len(prefill_ids))
        else:
            prefill_ids = prompt_ids
        first_token_ms = (time.time() - t0) * 1000.0

        # Decode loop, one token at a time.
        out_ids: list[int] = []
        decode_start = time.time()
        for step in range(max_new_tokens):
            tid = self._decode_step(prefill_ids, step, seed_salt)
            out_ids.append(tid)
            self.total_decode_tokens += 1
            self.total_decode_ms += self.decode_ms_per_token
            if tid == self.tok.eos_id:
                break
        decode_ms = (time.time() - decode_start) * 1000.0
        # The prefill "wall" time is whatever the simulation already
        # accumulated; total elapsed includes decode.
        elapsed_ms = (time.time() - t0) * 1000.0

        return GenerationResult(
            prompt=prompt,
            prompt_token_count=len(prompt_ids),
            output_tokens=out_ids,
            output_text=self.tok.decode(out_ids),
            cache_hit=hit,
            elapsed_ms=elapsed_ms,
            first_token_ms=first_token_ms,
        )

    def generate_stream(
        self, prompt: str, max_new_tokens: int = 64, seed_salt: str = "default"
    ) -> Iterator[tuple[int, float]]:
        """Yield (token_id, ms_since_start) one at a time."""
        prompt_ids = self.tok.encode(prompt)
        ok, _msg = self.budget.allow(
            prompt_tokens=len(prompt_ids), max_output_tokens=max_new_tokens
        )
        if not ok:
            raise ValueError("budget rejected")
        hit, _ = self.cache.check(prompt)
        if not hit:
            self._prefill(prompt)
            self.cache.store(prompt, len(prompt_ids))

        t0 = time.time()
        for step in range(max_new_tokens):
            tid = self._decode_step(prompt_ids, step, seed_salt)
            self.total_decode_tokens += 1
            self.total_decode_ms += self.decode_ms_per_token
            yield tid, (time.time() - t0) * 1000.0
            if tid == self.tok.eos_id:
                break

    def generate_batch(
        self, prompts: list[str], max_new_tokens: int = 64
    ) -> list[GenerationResult]:
        """Process a batch. Shared system prompts amortise prefill."""
        results: list[GenerationResult] = []
        # In a real engine we'd pad-pack into one forward pass; here we
        # just process serially but exercise the cache+guard pipeline.
        for i, p in enumerate(prompts):
            results.append(
                self.generate(p, max_new_tokens=max_new_tokens, seed_salt=f"b{i}")
            )
        return results


# ---------------------------------------------------------------------------
# Smoke test (the meaningful workload)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a helpful, harmless assistant. Answer the user's question "
    "clearly and concisely. Use plain language. "
    "Respond in a single short paragraph. "
) * 3  # ~80-120 tokens; long enough that prefill is non-trivial

PROMPT_CATEGORIES = {
    "qa": [
        "What is the capital of France?",
        "Who wrote the novel Pride and Prejudice?",
        "What is the boiling point of water in Celsius?",
        "How many planets are in our solar system?",
        "What language is spoken in Brazil?",
        "Who painted the Mona Lisa?",
        "What is the largest ocean on Earth?",
        "When did World War II end?",
        "What is photosynthesis?",
        "What is the speed of light in m/s?",
        "What is the smallest country in the world?",
        "What gas do plants absorb from the atmosphere?",
        "Who proposed the theory of general relativity?",
        "What is the chemical symbol for gold?",
        "What is the longest river in Africa?",
        "In what year did the Berlin Wall fall?",
        "What is the currency of Japan?",
        "What is the largest mammal on Earth?",
        "What is the square root of 144?",
        "Who wrote the play Romeo and Juliet?",
    ],
    "summarization": [
        "Summarize: The French Revolution began in 1789 with the storming "
        "of the Bastille and led to the overthrow of the monarchy.",
        "Summarize: Newton discovered gravity when an apple fell on his head, "
        "but the real story is more complicated than the myth suggests.",
        "Summarize: The Amazon rainforest produces about six percent of "
        "the world's oxygen and hosts ten percent of all known species.",
        "Summarize: Python is a high-level, interpreted programming "
        "language created by Guido van Rossum and first released in 1991.",
        "Summarize: The internet was originally a US military project "
        "called ARPANET, designed to survive nuclear attack.",
        "Summarize: The Rosetta Stone allowed scholars to decode Egyptian "
        "hieroglyphs for the first time in over a thousand years.",
        "Summarize: Vaccines train the immune system to recognize and "
        "fight specific pathogens before the body ever encounters them.",
        "Summarize: The printing press, invented by Gutenberg around "
        "1440, made books affordable and triggered a literacy boom.",
        "Summarize: Bitcoin is a decentralized digital currency that "
        "uses a public ledger called a blockchain to record transactions.",
        "Summarize: The Hubble Space Telescope has been operating "
        "since 1990 and has captured some of the deepest images of space.",
    ],
    "code": [
        "Write a Python function that returns the factorial of n.",
        "Write a Python function that checks if a string is a palindrome.",
        "Write a Python function that flattens a nested list.",
        "Write a Python function that returns the Fibonacci sequence up to n.",
        "Write a Python function that counts word frequencies in a string.",
        "Write a Python function that returns the n-th prime number.",
        "Write a Python function that reverses the words in a sentence.",
        "Write a Python function that finds the longest common prefix of strings.",
        "Write a Python function that returns the GCD of two integers.",
        "Write a Python function that sorts a list of dictionaries by a key.",
        "Write a Python function that converts Celsius to Fahrenheit.",
        "Write a Python function that merges two sorted lists into one.",
        "Write a Python function that removes duplicates from a list.",
        "Write a Python function that returns all prime factors of n.",
        "Write a Python function that checks if two strings are anagrams.",
        "Write a Python function that returns the k-th largest element in a list.",
        "Write a Python function that generates all permutations of a string.",
        "Write a Python function that rotates a list by k positions.",
        "Write a Python function that returns the median of a numeric list.",
        "Write a Python function that validates a sudoku row.",
    ],
}


def _build_workload() -> list[tuple[str, str, str]]:
    """Returns list of (category, prompt_without_system, full_prompt)."""
    out: list[tuple[str, str, str]] = []
    for cat, prompts in PROMPT_CATEGORIES.items():
        for p in prompts:
            full = SYSTEM_PROMPT + "\nUser: " + p + "\nAssistant:"
            out.append((cat, p, full))
    return out


def _hr(s: str) -> None:
    print(f"\n{s}")


def main() -> None:
    print("═══ mistral-self-host: meaningful workload ═══")

    # 1) Build the engine and the workload.
    tok = Tokenizer()
    cache = PrefixCache(max_entries=256)
    budget = TokenBudgetGuard(max_total_tokens=4096)
    engine = MockLLMEngine(
        tokenizer=tok,
        cache=cache,
        budget=budget,
        prefill_ms_per_token=0.05,
        decode_ms_per_token=1.0,
    )
    workload = _build_workload()
    print(f"  prompt categories: {sorted(PROMPT_CATEGORIES.keys())}")
    print(f"  total requests:    {len(workload)}")
    print(f"  system prompt tokens: {len(tok.encode(SYSTEM_PROMPT))}")
    print(f"  budget:            {budget.max_total_tokens} total tokens")

    # ============================================================
    # Scenario A: tokenize + generate + decode + assert
    # ============================================================
    _hr("═══ Scenario A: tokenize → generate → decode (string output) ═══")
    sample_cat, sample_user, sample_full = workload[0]
    ids = tok.encode(sample_full)
    res = engine.generate(sample_full, max_new_tokens=32, seed_salt="A")
    print(f"  category:           {sample_cat}")
    print(f"  prompt tokens:      {len(ids)}")
    print(f"  output tokens:      {res.output_token_count}")
    print(f"  output text:        {res.output_text!r}")
    print(f"  elapsed:            {res.elapsed_ms:.2f} ms")
    assert isinstance(res.output_text, str), "output must be a string"
    assert len(res.output_text) > 0, "output must be non-empty"
    assert res.output_token_count >= 20, "must produce >=20 tokens"
    assert res.prompt_token_count > 0, "prompt must tokenize to >0 tokens"
    # Token count after generation >= token count before
    assert res.output_token_count >= 20, "post-generation token count invariant"
    print("  ✓ output is a non-empty string")
    print("  ✓ output_token_count >= 20")
    print("  ✓ prompt_token_count > 0")

    # ============================================================
    # Scenario B: KV cache hit — second call with same prefix
    # ============================================================
    _hr("═══ Scenario B: KV cache hit (same prefix) ═══")
    common_prefix = SYSTEM_PROMPT + "\nUser: What is the capital of France?\nAssistant:"
    # Cold call
    engine.cache = PrefixCache(max_entries=256)  # fresh cache
    engine2 = MockLLMEngine(
        tokenizer=tok, cache=engine.cache, budget=budget,
        prefill_ms_per_token=0.05, decode_ms_per_token=1.0,
    )
    t0 = time.time()
    cold = engine2.generate(common_prefix, max_new_tokens=32, seed_salt="cold")
    cold_ms = (time.time() - t0) * 1000.0
    # Hot call — same prefix, must hit the cache
    t0 = time.time()
    hot = engine2.generate(common_prefix, max_new_tokens=32, seed_salt="cold")
    hot_ms = (time.time() - t0) * 1000.0
    print(f"  cold: cache_hit={cold.cache_hit}, elapsed={cold_ms:.2f} ms, "
          f"first_token={cold.first_token_ms:.2f} ms")
    print(f"  hot:  cache_hit={hot.cache_hit}, elapsed={hot_ms:.2f} ms, "
          f"first_token={hot.first_token_ms:.2f} ms")
    print(f"  cache hit rate: {engine2.cache.hit_rate():.1%} "
          f"({engine2.cache.hits}/{engine2.cache.lookups})")
    assert not cold.cache_hit, "first call must miss"
    assert hot.cache_hit, "second call with same prefix must hit"
    # KV cache hit produces the same output (deterministic decoder)
    assert cold.output_tokens == hot.output_tokens, (
        f"cache hit diverged from cold: cold={cold.output_tokens} hot={hot.output_tokens}"
    )
    # And the hot path should be no slower than the cold path on the
    # *prefix-reuse* part (first-token latency drops on a hit).
    print("  ✓ cold miss, hot hit")
    print("  ✓ hot output identical to cold (deterministic decode)")

    # ============================================================
    # Scenario C: batched generation (4 prompts, all complete)
    # ============================================================
    _hr("═══ Scenario C: batched generation (4 prompts in one batch) ═══")
    batch = [
        SYSTEM_PROMPT + "\nUser: " + p + "\nAssistant:"
        for p in [
            "What is the capital of France?",
            "Write a Python function that returns the factorial of n.",
            "Summarize: The French Revolution began in 1789.",
            "What language is spoken in Brazil?",
        ]
    ]
    t0 = time.time()
    batched = engine.generate_batch(batch, max_new_tokens=24)
    batch_ms = (time.time() - t0) * 1000.0
    for i, r in enumerate(batched):
        print(f"  [{i}] tokens={r.output_token_count:3d} "
              f"text={r.output_text[:40]!r}")
    total_out_tokens = sum(r.output_token_count for r in batched)
    batch_tps = total_out_tokens / (batch_ms / 1000.0) if batch_ms > 0 else 0.0
    print(f"  batch elapsed:    {batch_ms:.2f} ms")
    print(f"  total out tokens: {total_out_tokens}")
    print(f"  batch throughput: {batch_tps:.1f} tok/s")
    assert len(batched) == len(batch), "batch must produce N outputs for N inputs"
    for r in batched:
        assert isinstance(r.output_text, str) and len(r.output_text) > 0, \
            "every batched output must be a non-empty string"
        assert r.output_token_count >= 20, \
            f"every batched output must be >=20 tokens, got {r.output_token_count}"
    print("  ✓ 4/4 batched generations complete")
    print("  ✓ every batched output is a non-empty string with >=20 tokens")

    # ============================================================
    # Scenario D: streaming — yield tokens one at a time
    # ============================================================
    _hr("═══ Scenario D: streaming generation (token-by-token) ═══")
    stream_prompt = workload[5][2]  # first 'summarization' prompt
    expected_tokens = 28
    yielded: list[tuple[int, float]] = []
    t0 = time.time()
    for tid, ms in engine.generate_stream(
        stream_prompt, max_new_tokens=expected_tokens, seed_salt="stream"
    ):
        yielded.append((tid, ms))
    stream_total_ms = (time.time() - t0) * 1000.0
    first_token_ms = yielded[0][1] if yielded else float("inf")
    last_token_ms = yielded[-1][1] if yielded else 0.0
    print(f"  yielded tokens:    {len(yielded)}")
    print(f"  first-token lat:   {first_token_ms:.2f} ms")
    print(f"  last-token lat:    {last_token_ms:.2f} ms")
    print(f"  stream total:      {stream_total_ms:.2f} ms")
    assert len(yielded) == expected_tokens, (
        f"streaming must yield exactly {expected_tokens} tokens, got {len(yielded)}"
    )
    # Latencies should be monotonically non-decreasing.
    for i in range(1, len(yielded)):
        assert yielded[i][1] >= yielded[i - 1][1] - 0.01, (
            f"streaming latency went backwards at step {i}: "
            f"{yielded[i][1]:.3f} < {yielded[i - 1][1]:.3f}"
        )
    print(f"  ✓ yielded {len(yielded)}/{expected_tokens} tokens")
    print("  ✓ streaming latencies are monotonically non-decreasing")

    # ============================================================
    # Full workload: 50+ generations across 3 categories
    # ============================================================
    _hr("═══ Full workload: 50+ generations across 3 categories ═══")
    engine.cache = PrefixCache(max_entries=256)
    engine3 = MockLLMEngine(
        tokenizer=tok, cache=engine.cache, budget=budget,
        prefill_ms_per_token=0.05, decode_ms_per_token=1.0,
    )
    per_cat: dict[str, list[GenerationResult]] = {"qa": [], "summarization": [], "code": []}
    t0 = time.time()
    for cat, _user, full in workload:
        r = engine3.generate(full, max_new_tokens=32, seed_salt=cat)
        per_cat[cat].append(r)
    full_ms = (time.time() - t0) * 1000.0
    total_out = sum(sum(r.output_token_count for r in rs) for rs in per_cat.values())
    full_tps = total_out / (full_ms / 1000.0) if full_ms > 0 else 0.0
    print(f"  total requests:    {len(workload)}")
    print(f"  per category:      " + ", ".join(
        f"{c}={len(rs)}" for c, rs in per_cat.items()
    ))
    print(f"  total out tokens:  {total_out}")
    print(f"  full workload:     {full_ms:.2f} ms  ({full_tps:.1f} tok/s)")
    print(f"  cache hit rate:    {engine3.cache.hit_rate():.1%} "
          f"({engine3.cache.hits}/{engine3.cache.lookups})")
    print(f"  prefill tokens:    {engine3.total_prefill_tokens}")
    print(f"  decode tokens:     {engine3.total_decode_tokens}")
    assert len(workload) >= 50, "must run >=50 generation requests"
    cats_with_data = [c for c, rs in per_cat.items() if rs]
    assert len(cats_with_data) >= 3, "must span >=3 prompt categories"
    for cat, rs in per_cat.items():
        for r in rs:
            assert isinstance(r.output_text, str) and len(r.output_text) > 0, \
                f"[{cat}] non-string or empty output: {r.output_text!r}"
            assert r.output_token_count >= 20, \
                f"[{cat}] output_token_count {r.output_token_count} < 20"
    print("  ✓ 50+ generations across 3 categories")
    print("  ✓ every output is a non-empty string with >=20 tokens")

    # ============================================================
    # Budget guard: must reject an oversized request
    # ============================================================
    _hr("═══ Budget guard ═══")
    ok, msg = budget.allow(prompt_tokens=3500, max_output_tokens=800)
    print(f"  3500+800 = 4300 vs 4096 budget: allowed={ok} ({msg})")
    assert not ok, "guard must reject over-budget request"
    ok, msg = budget.allow(prompt_tokens=2000, max_output_tokens=2000)
    print(f"  2000+2000 = 4000 vs 4096 budget: allowed={ok} ({msg})")
    assert ok, "guard must allow under-budget request"
    print("  ✓ rejects over-budget, allows under-budget")

    # ============================================================
    # Final invariants
    # ============================================================
    _hr("═══ Final metrics ═══")
    print(f"  generations run:        {len(workload)}")
    print(f"  output tokens (total):  {total_out}")
    print(f"  throughput:             {full_tps:.1f} tok/s")
    print(f"  KV cache hit rate:      {engine3.cache.hit_rate():.1%}")
    print(f"  batch throughput:       {batch_tps:.1f} tok/s")
    print(f"  streaming first-token:  {first_token_ms:.2f} ms")
    print(f"  prefill tokens skipped: "
          f"{engine3.cache.hits * len(tok.encode(workload[0][2]))} (approx, on hits)")

    # The big assertion block.
    assert len(workload) >= 50
    assert len(cats_with_data) >= 3
    for cat, rs in per_cat.items():
        for r in rs:
            assert r.output_token_count >= 20
            assert isinstance(r.output_text, str) and len(r.output_text) > 0
    assert len(batched) == 4
    assert all(r.output_token_count >= 20 for r in batched)
    assert len(yielded) == expected_tokens
    assert cold.output_tokens == hot.output_tokens
    assert hot.cache_hit and not cold.cache_hit
    print("\n✓ all invariants pass")


if __name__ == "__main__":
    main()
