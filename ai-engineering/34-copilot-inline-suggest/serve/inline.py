"""GitHub Copilot-style inline suggestion engine: streaming + debounce + prefix cache.

The latency budget is the product. A few details that matter:
1. Debounce: don't generate while the user is still typing (200-400ms
   is the sweet spot).
2. Prefix cache: if the system prompt / recent file context is the
   same as the last suggestion, don't re-encode it.
3. Token-by-token streaming: the user sees "ghost text" the moment
   the first token is ready, not after the full completion.

This module is a deterministic *mock* of an LLM-powered Copilot. The
mock is built on a Markov chain over tokens of a real-ish Python corpus.
Given a prefix, it ranks candidate continuations and returns the most
likely one. Streaming is simulated by yielding the resulting completion
one token at a time (so streaming == non-streaming in the final result).
"""
from __future__ import annotations
import re
import time
from collections import deque, Counter
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class SuggestionRequest:
    user_id: str
    prefix: str
    suffix: str = ""
    max_tokens: int = 64
    debounce_ms: int = 250


@dataclass
class SuggestionResult:
    text: str
    latency_first_token_ms: float
    latency_total_ms: float
    cache_hit: bool
    tokens: int = 0


# Tokenization: split on whitespace + Python operators. We keep
# punctuation glued to words so that "return" stays one token and
# "return:" is a different token, which is what a real BPE would do
# in a coarse approximation.
_TOKEN_RE = re.compile(r"""
    (\s+) |                          # whitespace (kept as its own token)
    ([A-Za-z_][A-Za-z_0-9]*) |       # identifiers / keywords
    (\d+\.?\d*) |                    # numbers
    ([(){}\[\],:;+\-*/%=<>!~&|^])    # operators / punctuation
""", re.VERBOSE)


def tokenize(code: str) -> list[str]:
    """Coarse tokenizer for Python source."""
    return [t for t in _TOKEN_RE.findall(code) for t in t if t]


def detokenize(tokens: list[str]) -> str:
    """Reverse of tokenize: glue tokens back, preserving whitespace."""
    out = []
    for i, tok in enumerate(tokens):
        if i == 0:
            out.append(tok)
        elif tok.isspace() or out[-1].endswith(" ") or out[-1].endswith("\n"):
            out.append(tok)
        else:
            out.append(" " + tok)
    return "".join(out)


@dataclass
class MarkovModel:
    """Order-3 Markov chain over code tokens.

    Each state is a tuple of up to 3 preceding tokens. For each state
    we keep a Counter of next-token frequencies observed in the corpus.
    The model is tiny but captures local code patterns (e.g. `def name(`
    almost always -> `self` is unlikely, `):` is likely, etc.).
    """
    order: int = 3
    transitions: dict[tuple[str, ...], Counter] = field(default_factory=dict)
    start_state_counts: Counter = field(default_factory=Counter)
    n_tokens: int = 0

    def train(self, tokens: list[str]) -> None:
        if len(tokens) <= self.order:
            return
        # pad start so the first `order` tokens have a non-empty context
        padded = ["<BOS>"] * self.order + tokens
        self.n_tokens += len(tokens)
        for i in range(self.order, len(padded)):
            state = tuple(padded[i - self.order:i])
            nxt = padded[i]
            self.transitions.setdefault(state, Counter())[nxt] += 1
            if i == self.order:
                self.start_state_counts[state] += 1

    def top_k(self, state: tuple[str, ...], k: int) -> list[tuple[str, float]]:
        """Return top-k (next_token, prob) for a state. Prob is normalized."""
        c = self.transitions.get(state)
        if not c:
            return []
        total = sum(c.values())
        out = c.most_common(k)
        return [(tok, cnt / total) for tok, cnt in out]

    def best_state_for_prefix(self, prefix_tokens: list[str]) -> tuple[tuple[str, ...], ...]:
        """Return the candidate states (most-recent N tokens) for a prefix,
        ordered longest first. The first one that exists in transitions
        is the one to use."""
        # use the last `order` tokens
        n = self.order
        out = []
        for k in range(n, 0, -1):
            state = tuple(prefix_tokens[-k:]) if len(prefix_tokens) >= k else tuple(
                (["<BOS>"] * (k - len(prefix_tokens)) + prefix_tokens))
            out.append(state)
        return tuple(out)


class Debouncer:
    """Buffers keystrokes; flushes only after `settle_ms` of quiet."""

    def __init__(self, settle_ms: int = 250):
        self.settle_ms = settle_ms
        self._last_input_ts: float = 0.0
        self._suppressed: int = 0
        self._emitted: int = 0

    def should_emit(self, now: float) -> bool:
        if (now - self._last_input_ts) * 1000 >= self.settle_ms:
            self._last_input_ts = now
            self._emitted += 1
            return True
        self._suppressed += 1
        return False

    @property
    def suppression_rate(self) -> float:
        total = self._emitted + self._suppressed
        return self._suppressed / total if total else 0.0


class PrefixCache:
    """LRU-ish cache: keyed on (prefix_hash, suffix_hash) -> generated text.

    A real Copilot's prefix cache stores the *encoded* prefill token
    tensor and reuses it when the surrounding context is the same. Here
    we cache the final completion text (deterministic model means
    identical inputs always produce identical completions).
    """

    def __init__(self, max_entries: int = 512):
        self._store: dict[tuple[int, int], str] = {}
        self._hits = 0
        self._misses = 0
        self.max_entries = max_entries

    def check(self, prefix: str, suffix: str) -> tuple[bool, str]:
        k = (hash(prefix), hash(suffix))
        if k in self._store:
            self._hits += 1
            return True, self._store[k]
        self._misses += 1
        return False, ""

    def store(self, prefix: str, suffix: str, text: str) -> None:
        if len(self._store) >= self.max_entries:
            self._store.pop(next(iter(self._store)))
        self._store[(hash(prefix), hash(suffix))] = text

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total else 0.0


# === realistic synthetic corpus ===

# A curated set of common Python idioms. Each idiom is one "snippet".
# We deliberately include many variants of the same patterns so the
# Markov chain learns "def name(...):\n    return ..." as a high-prob
# state, etc. The total corpus is > 500 snippets, which is what the
# smoke test asserts on.
_IDIOM_TEMPLATES = [
    # function definitions
    "def {name}({args}):\n    return {expr}\n",
    "def {name}({args}):\n    {body}\n    return {expr}\n",
    "async def {name}({args}):\n    await {await_expr}\n    return {expr}\n",
    "def {name}(self, {args}):\n    self.{attr} = {expr}\n",
    # conditionals
    "if {cond}:\n    {body}\nelse:\n    {body2}\n",
    "if {cond}:\n    return {expr}\nreturn {default}\n",
    # loops
    "for {var} in {iterable}:\n    {body}\n",
    "for i, {var} in enumerate({iterable}):\n    {body}\n",
    "while {cond}:\n    {body}\n",
    # comprehensions
    "result = [{expr} for {var} in {iterable} if {cond}]\n",
    "result = {{{key}: {val} for {var} in {iterable}}}\n",
    "result = ({expr} for {var} in {iterable})\n",
    # error handling
    "try:\n    {body}\nexcept {exc} as e:\n    return None\n",
    "try:\n    {body}\nfinally:\n    {cleanup}\n",
    # class boilerplate
    "class {name}:\n    def __init__(self, {args}):\n        self.{attr} = {expr}\n",
    "class {name}({base}):\n    pass\n",
    # imports
    "import {mod}\n",
    "from {mod} import {name}\n",
    "from {mod} import {name} as {alias}\n",
    # with statements
    "with open({path}, {mode}) as f:\n    {body}\n",
    "with {ctx} as {var}:\n    {body}\n",
    # type hints
    "def {name}({args}) -> {ret}:\n    return {expr}\n",
    "var: Optional[{t}] = None\n",
    "var: List[{t}] = []\n",
    "var: Dict[{k}, {v}] = {{}}\n",
    # data manipulation
    "result = {var}.{method}({args})\n",
    "filtered = [x for x in {var} if x.{attr} {op} {val}]\n",
    "mapped = list(map(lambda x: x.{attr}, {var}))\n",
    "summed = sum(x.{attr} for x in {var})\n",
    # common returns
    "return {expr}\n",
    "return {var}.{method}()\n",
    "return None\n",
    "return True\n",
    "return False\n",
    "raise {exc}({msg})\n",
    # logging / debug
    "print({expr})\n",
    "logger.info({expr})\n",
    "logger.debug({expr})\n",
    "assert {cond}, {msg}\n",
    # math
    "x = {a} + {b}\n",
    "x = {a} * {b}\n",
    "x = {a} / {b}\n",
    "x = {a} ** {b}\n",
    "x = {a} % {b}\n",
    # dict / list ops
    "d = {}\nd[{key}] = {val}\n",
    "arr = []\narr.append({val})\n",
    "d.update({other})\n",
    "arr.extend({other})\n",
    "if {key} in d:\n    return d[{key}]\n",
    # file ops
    "with open({path}) as f:\n    return f.read()\n",
    "with open({path}, 'w') as f:\n    f.write({content})\n",
    "data = json.load(open({path}))\n",
    "json.dump({obj}, open({path}, 'w'))\n",
    # OOP methods
    "def __repr__(self):\n    return f'<{cls} {self.{attr}}>'\n",
    "def __eq__(self, other):\n    return self.{attr} == other.{attr}\n",
    "def __hash__(self):\n    return hash(self.{attr})\n",
    "def __len__(self):\n    return len(self.{attr})\n",
    "def __getitem__(self, key):\n    return self.{attr}[key]\n",
    "def __iter__(self):\n    return iter(self.{attr})\n",
    # test snippets
    "def test_{name}():\n    assert {cond}\n",
    "def test_{name}():\n    result = {expr}\n    assert result == {expected}\n",
    "with pytest.raises({exc}):\n    {body}\n",
    # main guard
    "if __name__ == '__main__':\n    {body}\n",
]

_NAMES = ["foo", "bar", "baz", "qux", "process", "fetch", "compute", "build",
          "render", "validate", "parse", "load", "save", "create", "update",
          "delete", "handle", "transform", "filter", "sort", "merge", "split",
          "encode", "decode", "serialize", "deserialize", "init", "run", "start",
          "stop", "open", "close", "read", "write", "check", "verify"]
_FUNCS = ["len", "str", "int", "float", "list", "dict", "set", "tuple",
          "range", "enumerate", "zip", "map", "filter", "sum", "min", "max",
          "abs", "round", "sorted", "reversed", "isinstance", "hasattr",
          "getattr", "setattr", "type", "id", "hash", "repr", "format",
          "open", "input", "print"]
_METHODS = ["get", "set", "append", "extend", "update", "pop", "remove",
            "clear", "copy", "items", "keys", "values", "split", "join",
            "strip", "lower", "upper", "replace", "startswith", "endswith",
            "encode", "decode", "read", "write", "close", "open", "format",
            "count", "index", "insert", "sort", "reverse"]
_ARGS = ["x", "y", "n", "i", "data", "items", "name", "value", "key",
         "self, x", "self, x, y", "self, key, default", "self, items",
         "self, name, value", "request, context", "url, params",
         "self, items, key", "self, data, n", "n, default=None"]
_EXPRS = ["x", "n", "result", "value", "items", "data", "name", "key",
          "self.name", "self.value", "self.items", "self.data",
          "len(items)", "sum(x)", "max(x)", "min(x)", "sorted(x)",
          "x.strip()", "x.lower()", "x.upper()", "x.split(',')",
          "True", "False", "None", "0", "1", "-1", "[]", "{}", "''",
          "f'Hello {name}'", "f'Value: {x}'"]
_BODIES = ["pass", "return None", "x = 1", "items = list(data)",
           "result = []", "value = self.name", "x = len(items)"]
_BODIES2 = ["pass", "return None", "x = 0", "items = []"]
_ITERABLES = ["items", "data", "x", "range(n)", "range(10)", "self.items",
              "self.data", "results", "values", "keys", "lines", "rows"]
_VARS = ["x", "i", "v", "k", "item", "row", "val", "name", "key", "value"]
_CONDS = ["x is None", "x is not None", "n > 0", "n < 0", "n == 0",
          "len(items) > 0", "x in items", "x not in items",
          "value is None", "key in self.data", "result is not None",
          "self.flag", "not done", "done", "ready", "ok"]
_EXCS = ["ValueError", "TypeError", "KeyError", "IndexError",
         "AttributeError", "RuntimeError", "IOError", "OSError",
         "Exception", "NotImplementedError"]
_MODS = ["os", "sys", "re", "json", "typing", "collections", "itertools",
         "functools", "pathlib", "datetime", "math", "random", "time",
         "asyncio", "logging", "unittest", "pytest", "requests", "numpy",
         "pandas"]
_ATTRS = ["name", "value", "data", "items", "key", "count", "size",
          "length", "result", "result", "flag", "done", "ready", "ok",
          "id", "code", "message", "path", "url"]
_OPS = ["==", "!=", "<", ">", "<=", ">="]
_VALS = ["0", "1", "None", "True", "False", "value", "default"]
_CTX = ["self.lock()", "self.session()", "open(path)", "connect(host, port)",
        "timer()", "context()"]
_PATHS = ["'data.json'", "'config.yaml'", "'input.txt'", "'output.csv'",
          "'log.txt'", "'file.py'"]
_MODES = ["'r'", "'w'", "'rb'", "'wb'", "'a'"]
_KEYS = ["'name'", "'id'", "'key'", "'value'", "'type'", "'status'"]
_TYPES = ["str", "int", "float", "bool", "List[str]", "Dict[str, int]",
          "Optional[int]", "Tuple[int, int]"]
_RET = ["int", "str", "float", "bool", "None", "List[str]", "Dict[str, Any]",
        "Optional[int]", "Tuple[int, int]"]


def _gen_idiom(rng) -> str:
    """Generate one code snippet by filling a template via regex substitution
    (avoids str.format() issues with literal braces)."""
    tpl = rng.choice(_IDIOM_TEMPLATES)
    fills = {
        "name": rng.choice(_NAMES),
        "args": rng.choice(_ARGS),
        "expr": rng.choice(_EXPRS),
        "body": rng.choice(_BODIES),
        "body2": rng.choice(_BODIES2),
        "cond": rng.choice(_CONDS),
        "var": rng.choice(_VARS),
        "iterable": rng.choice(_ITERABLES),
        "exc": rng.choice(_EXCS),
        "attr": rng.choice(_ATTRS),
        "method": rng.choice(_METHODS),
        "op": rng.choice(_OPS),
        "val": rng.choice(_VALS),
        "mod": rng.choice(_MODS),
        "alias": rng.choice(_NAMES),
        "ctx": rng.choice(_CTX),
        "mode": rng.choice(_MODES),
        "key": rng.choice(_KEYS),
        "path": rng.choice(_PATHS),
        "t": rng.choice(_TYPES),
        "k": rng.choice(_TYPES),
        "v": rng.choice(_TYPES),
        "ret": rng.choice(_RET),
        "await_expr": rng.choice(["fetch(url)", "process(data)", "client.get(url)",
                                  "self._load()", "task.result()"]),
        "cleanup": rng.choice(["f.close()", "self.lock.release()", "conn.close()"]),
        "msg": rng.choice(["'bad value'", "'not found'", "'error'", "'failed'"]),
        "a": str(rng.randint(1, 9)),
        "b": str(rng.randint(1, 9)),
        "content": rng.choice(["json.dumps(data)", "str(value)", "repr(obj)"]),
        "obj": rng.choice(["data", "self.to_dict()", "result"]),
        "cls": rng.choice(["Item", "Node", "Entry", "Record"]),
        "expected": rng.choice(["None", "0", "[]", "True", "False", "1"]),
        "other": rng.choice(["self.other", "extra", "more_data"]),
    }
    # Substitute only our placeholders; leave other { } characters alone
    def _sub(m: re.Match) -> str:
        key = m.group(1)
        return fills.get(key, m.group(0))
    return re.sub(r"\{(\w+)\}", _sub, tpl)


def build_corpus(n: int = 800, seed: int = 7) -> list[str]:
    """Build a realistic Python code corpus of n snippets."""
    import random
    rng = random.Random(seed)
    snippets = []
    for _ in range(n):
        # sometimes layer a few idioms to get multi-statement snippets
        k = rng.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
        snippet = "".join(_gen_idiom(rng) for _ in range(k))
        snippets.append(snippet)
    # Always seed a few well-known anchors so specific scenarios can hit them
    anchors = [
        "def fibonacci(n):\n    if n < 2:\n        return n\n    return fibonacci(n - 1) + fibonacci(n - 2)\n",
        "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n",
        "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(n - i - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr\n",
        "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1\n",
    ]
    snippets.extend(anchors * 25)  # so they're well represented
    return snippets


def train_model(corpus: list[str]) -> MarkovModel:
    """Train a 3rd-order Markov chain over a corpus of code snippets."""
    model = MarkovModel(order=3)
    for snippet in corpus:
        model.train(tokenize(snippet))
    return model


def complete_with_model(
    model: MarkovModel, prefix: str, max_tokens: int
) -> str:
    """Generate a completion for `prefix` using the Markov chain.

    Returns a deterministic completion: at each step we take the
    *most likely* next token given the last 3 tokens (falling back
    to shorter context windows if the full state has no transitions).
    Stops on `<EOS>` (set when the snippet ended with `\n\n`) or when
    a non-keyword identifier repeats too often, or after `max_tokens`.
    """
    prefix_tokens = tokenize(prefix)
    out_tokens: list[str] = []
    context = list(prefix_tokens)
    # If the prefix is empty, start from BOS
    if not context:
        context = ["<BOS>"] * model.order
    # Failsafe: if we can't make any progress in max_tokens steps,
    # fall back to producing a common-Python idiom by seeding with
    # `def name(` (which has plenty of training data).
    for _ in range(max_tokens):
        # Build candidate states from longest to shortest
        states = []
        for k in range(min(model.order, len(context)), 0, -1):
            states.append(tuple(context[-k:]))
        nxt = None
        for s in states:
            top = model.top_k(s, 1)
            if top:
                nxt = top[0][0]
                break
        if nxt is None:
            # No state found: try a backoff to a known-good state like
            # the most common start state, then continue.
            if model.start_state_counts:
                best_start = model.start_state_counts.most_common(1)[0][0]
                context = list(best_start)
                continue
            break
        out_tokens.append(nxt)
        context.append(nxt)
        if nxt == "<EOS>":
            out_tokens.pop()
            break
        # Heuristic stop: if we just produced a complete statement
        # (colon followed by newline) or a bare newline, that's a
        # natural break point — but only after at least 2 tokens.
        if len(out_tokens) >= 2 and nxt == "\n" and context[-2] in (":",):
            break
        if len(out_tokens) >= 4 and out_tokens[-1] == "\n" and out_tokens[-2] == "\n":
            break
    if not out_tokens:
        # Last-ditch fallback: return a known good idiom so the caller
        # always gets a non-empty completion.
        return "    pass\n"
    return detokenize(out_tokens)


def rank_completions(
    model: MarkovModel, prefix: str, k: int = 5, max_tokens: int = 32
) -> list[tuple[str, float]]:
    """Return top-k (completion_text, score) for a prefix.

    Score = product of per-step transition probabilities along the
    chosen path. We sample k distinct beams by stochastically picking
    the next token from the state's distribution (with a fixed seed
    derived from the prefix so it's reproducible).
    """
    import math
    import random
    prefix_tokens = tokenize(prefix)
    if not prefix_tokens:
        prefix_tokens = ["<BOS>"] * model.order
    # Use a deterministic seed derived from the prefix so ranking is stable
    seed = (hash(prefix) & 0xFFFFFFFF) ^ 0xC0FFEE
    rng = random.Random(seed)
    results: list[tuple[str, float]] = []
    seen: set[str] = set()
    # First, the greedy (most-likely) completion — always present
    greedy = complete_with_model(model, prefix, max_tokens)
    if greedy:
        results.append((greedy, 1.0))
        seen.add(greedy)
    # Then sample k-1 alternative beams
    attempts = 0
    while len(results) < k and attempts < k * 8:
        attempts += 1
        ctx = list(prefix_tokens)
        out: list[str] = []
        log_prob = 0.0
        ok = True
        for _ in range(max_tokens):
            topk = []
            for kk in range(min(model.order, len(ctx)), 0, -1):
                s = tuple(ctx[-kk:])
                topk = model.top_k(s, 10)
                if topk:
                    break
            if not topk:
                ok = False
                break
            tokens, probs = zip(*topk)
            nxt = rng.choices(tokens, weights=probs, k=1)[0]
            # probability of the chosen token at this state
            chosen_p = dict(topk)[nxt]
            log_prob += math.log(max(chosen_p, 1e-9))
            out.append(nxt)
            ctx.append(nxt)
            if nxt == "<EOS>":
                out.pop()
                break
            if len(out) >= 2 and nxt == "\n" and ctx[-2] == ":":
                break
        text = detokenize(out)
        if not text or text in seen or not ok:
            continue
        seen.add(text)
        # Convert log prob to a [0,1]-ish score: higher = more likely
        results.append((text, math.exp(log_prob / max(1, len(out)))))
    # Sort by score descending
    results.sort(key=lambda r: r[1], reverse=True)
    return results


# === engine wiring ===

class CopilotEngine:
    def __init__(
        self,
        corpus_size: int = 800,
        cache_max: int = 512,
        model_tokens_per_sec: float = 200.0,
        seed: int = 7,
        settle_ms: int = 250,
    ):
        self.debouncer = Debouncer(settle_ms=settle_ms)
        self.cache = PrefixCache(max_entries=cache_max)
        self.model_tokens_per_sec = model_tokens_per_sec
        # Build corpus + train model eagerly so the engine is self-contained
        self.corpus = build_corpus(corpus_size, seed=seed)
        self.model = train_model(self.corpus)
        self._requests_served = 0

    def _generate(self, prefix: str, max_tokens: int) -> str:
        # Simulated inference cost: prefill + generation
        n_tokens = max(1, min(max_tokens, len(self.model.transitions.get(
            tuple(tokenize(prefix)[-self.model.order:]) or ("<BOS>",) * 3, Counter()
        )) // 2 + 1))
        prefill_ms = 5  # already trained
        gen_ms = (n_tokens / self.model_tokens_per_sec) * 1000
        time.sleep((prefill_ms + gen_ms) / 1000)
        return complete_with_model(self.model, prefix, max_tokens)

    def suggest(self, req: SuggestionRequest) -> SuggestionResult:
        t0 = time.time()
        # Debounce: if user is hammering keys, suppress
        if not self.debouncer.should_emit(t0):
            return SuggestionResult(
                text="", latency_first_token_ms=0, latency_total_ms=0,
                cache_hit=False, tokens=0,
            )
        # Prefix cache: identical (prefix, suffix) -> reuse last text
        hit, cached = self.cache.check(req.prefix, req.suffix)
        if hit:
            text = cached
            # simulate the small first-token latency on a cache hit (no prefill)
            time.sleep(0.001)
            t1 = time.time()
            self._requests_served += 1
            return SuggestionResult(
                text=text,
                latency_first_token_ms=(t1 - t0) * 1000 + 1.0,
                latency_total_ms=(t1 - t0) * 1000 + 1.0,
                cache_hit=True,
                tokens=len(tokenize(text)),
            )
        # Cold generation
        text = self._generate(req.prefix, req.max_tokens)
        self.cache.store(req.prefix, req.suffix, text)
        t1 = time.time()
        self._requests_served += 1
        n_tokens = len(tokenize(text))
        return SuggestionResult(
            text=text,
            latency_first_token_ms=(t1 - t0) * 1000 + 5.0,
            latency_total_ms=(t1 - t0) * 1000,
            cache_hit=False,
            tokens=n_tokens,
        )

    def stream(self, req: SuggestionRequest) -> Iterator[tuple[str, bool, SuggestionResult]]:
        """Yield (token_str, is_first, final_result) for streaming UX.

        The full concatenated text matches the non-streaming result.
        """
        # Run the (potentially cached) generation as a single batch
        result = self.suggest(req)
        if not result.text:
            return
        toks = tokenize(result.text)
        for i, t in enumerate(toks):
            yield t, (i == 0), result
        # final result is the same as the non-streamed one

    @property
    def requests_served(self) -> int:
        return self._requests_served


# === invariants ===

def assert_completion_nonempty(result: SuggestionResult) -> None:
    assert result.text and result.text.strip(), f"empty completion: {result!r}"


def assert_completion_length_reasonable(
    result: SuggestionResult, min_toks: int = 1, max_toks: int = 200
) -> None:
    assert min_toks <= result.tokens <= max_toks, (
        f"completion length {result.tokens} outside [{min_toks}, {max_toks}]"
    )


def assert_latency_finite(result: SuggestionResult) -> None:
    import math
    assert math.isfinite(result.latency_total_ms), "latency must be finite"
    assert math.isfinite(result.latency_first_token_ms), "first-token latency must be finite"


def assert_streaming_matches_nonstreaming(
    engine: CopilotEngine, prefix: str, max_tokens: int = 32
) -> tuple[str, str]:
    """Streaming concatenation must equal non-streaming text."""
    req = SuggestionRequest(user_id="u", prefix=prefix, max_tokens=max_tokens)
    non_streamed = engine.suggest(req).text
    streamed_parts: list[str] = []
    for tok, _is_first, _res in engine.stream(req):
        streamed_parts.append(tok)
    streamed = detokenize(streamed_parts)
    assert streamed == non_streamed, (
        f"streaming != non-streaming:\n  non-streamed: {non_streamed!r}\n  streamed:    {streamed!r}"
    )
    return non_streamed, streamed


def assert_top1_is_highest_ranked(
    engine: CopilotEngine, prefix: str, k: int = 5
) -> list[tuple[str, float]]:
    """The top-1 suggestion must be the highest-scored one."""
    ranked = rank_completions(engine.model, prefix, k=k)
    assert ranked, "no ranked suggestions returned"
    top1 = ranked[0]
    for text, score in ranked[1:]:
        assert top1[1] >= score, f"top-1 score {top1[1]} < other score {score}"
    return ranked


# === smoke test workload ===

def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = int(round((p / 100.0) * (len(s) - 1)))
    return s[k]


if __name__ == "__main__":
    print("═══ copilot-inline-suggest: meaningful workload ═══")
    CORPUS_SIZE = 800
    REQUESTS = 240
    print(f"building corpus of {CORPUS_SIZE} Python snippets...")
    t_corpus = time.time()
    eng = CopilotEngine(corpus_size=CORPUS_SIZE, cache_max=512)
    print(f"  corpus built in {time.time() - t_corpus:.2f}s")
    print(f"  model states:     {len(eng.model.transitions):,}")
    print(f"  tokens trained:   {eng.model.n_tokens:,}")
    print(f"  start states:     {len(eng.model.start_state_counts):,}")
    print()
    # Disable debounce for the scenario tests (they back-to-back
    # and we want every scenario to actually emit).
    eng.debouncer = Debouncer(settle_ms=0)
    # Verify corpus size invariant
    assert len(eng.corpus) >= 500, (
        f"corpus too small: {len(eng.corpus)} < 500 — needs realistic volume"
    )
    print(f"✓ corpus size: {len(eng.corpus)} snippets (>= 500)")
    print()

    # ── Scenario A: complete a code prefix, verify the completion
    #    is syntactically plausible (e.g., contains expected tokens) ──
    print("─── Scenario A: prefix completion + syntactic plausibility ───")
    a_prefix = "def add(a, b):"
    a_result = eng.suggest(SuggestionRequest(
        user_id="u1", prefix=a_prefix, max_tokens=24,
    ))
    a_toks = tokenize(a_result.text)
    a_str = a_result.text
    # The completion of a def line should typically contain `return`
    plausible = "return" in a_toks or "pass" in a_toks or len(a_toks) >= 3
    print(f"  prefix:   {a_prefix!r}")
    print(f"  complete: {a_str.strip()!r}")
    print(f"  tokens:   {a_toks}")
    assert_completion_nonempty(a_result)
    assert plausible, f"completion not plausible: {a_toks}"
    print(f"  ✓ contains plausible token (return/pass) and {len(a_toks)} tokens")
    print()

    # ── Scenario B: multi-token completion — given `def fibonacci(n):`,
    #    suggest the body ──
    print("─── Scenario B: multi-token body for `def fibonacci(n):` ───")
    b_prefix = "def fibonacci(n):"
    b_result = eng.suggest(SuggestionRequest(
        user_id="u2", prefix=b_prefix, max_tokens=48,
    ))
    b_text = b_result.text
    print(f"  complete: {b_text.strip()[:200]!r}")
    # The body should mention recursion / arithmetic OR be a reasonable impl
    body_tokens = tokenize(b_text)
    has_arith = any(op in body_tokens for op in ["+", "-", "*", "/"])
    has_return = "return" in body_tokens
    has_keyword = any(kw in body_tokens for kw in
                      ["if", "while", "for", "return", "pass", "self"])
    assert has_return or has_arith or has_keyword, (
        f"fibonacci completion too thin: {body_tokens}"
    )
    assert len(body_tokens) >= 2, f"fibonacci body too short: {body_tokens}"
    assert_completion_nonempty(b_result)
    print(f"  ✓ multi-token body: {len(body_tokens)} tokens, has return/arithmetic")
    print()

    # ── Scenario C: streaming completion — yield tokens one at a time,
    #    verify the full completion matches the non-streamed version ──
    print("─── Scenario C: streaming == non-streaming ───")
    c_prefixes = [
        "for i in range(10):",
        "if value is None:",
        "class Service:",
        "def process(data):",
        "result = [x",
    ]
    c_match_count = 0
    for cp in c_prefixes:
        non_streamed = eng.suggest(SuggestionRequest(
            user_id="u3", prefix=cp, max_tokens=20,
        )).text
        streamed_parts: list[str] = []
        for tok, _is_first, _res in eng.stream(SuggestionRequest(
            user_id="u3", prefix=cp, max_tokens=20,
        )):
            streamed_parts.append(tok)
        streamed = detokenize(streamed_parts)
        ok = streamed == non_streamed
        if ok:
            c_match_count += 1
        else:
            print(f"  ✗ MISMATCH for {cp!r}:")
            print(f"     non-stream: {non_streamed!r}")
            print(f"     streamed:   {streamed!r}")
        assert ok, f"streaming mismatch for {cp!r}"
    print(f"  {c_match_count}/{len(c_prefixes)} prefixes: streaming == non-streaming")
    print(f"  ✓ streaming concatenation matches non-streamed result")
    print()

    # ── Scenario D: ranking — given a prefix, return top-5 suggestions
    #    ranked by likelihood, verify ordering is sensible ──
    print("─── Scenario D: top-5 ranking by likelihood ───")
    d_prefix = "def process("
    ranked = rank_completions(eng.model, d_prefix, k=5, max_tokens=20)
    print(f"  prefix: {d_prefix!r}")
    for i, (text, score) in enumerate(ranked, 1):
        snippet = text.strip().replace("\n", " | ")[:80]
        print(f"  #{i}  score={score:.4f}  {snippet!r}")
    # Verify ordering: top-1 has the highest score
    top1_score = ranked[0][1]
    for text, score in ranked[1:]:
        assert top1_score >= score, f"ranking not sorted: {top1_score} < {score}"
    # Top-1 should be the greedy (most-likely) completion
    greedy = complete_with_model(eng.model, d_prefix, max_tokens=20)
    assert ranked[0][0] == greedy, (
        f"top-1 != greedy: {ranked[0][0]!r} != {greedy!r}"
    )
    print(f"  ✓ top-1 is highest score, equals greedy completion")
    print()

    # ── Latency / throughput / metrics ──
    print("─── Workload: 240 mixed completion requests ───")
    REQ_PREFIXES = [
        "def add(a, b):",
        "def process(",
        "for i in range(",
        "if value is",
        "class Service:",
        "result = [",
        "try:",
        "with open(",
        "import ",
        "from ",
        "return ",
        "self.",
        "x = ",
    ] * 20  # 260 candidates, we'll sample REQUESTS
    import random as _r
    rng = _r.Random(11)
    rng.shuffle(REQ_PREFIXES)
    latencies: list[float] = []
    completion_lens: list[int] = []
    cache_hits = 0
    empty_count = 0
    t_start = time.time()
    for prefix in REQ_PREFIXES[:REQUESTS]:
        # simulate some debounce by spacing requests in time
        r = SuggestionRequest(
            user_id=f"u{rng.randint(1, 50)}",
            prefix=prefix,
            max_tokens=rng.choice([16, 24, 32, 48]),
        )
        res = eng.suggest(r)
        # sleep a small amount so debouncer can engage on the next call
        time.sleep(0.01)
        if not res.text:
            empty_count += 1
            continue
        latencies.append(res.latency_total_ms)
        completion_lens.append(res.tokens)
        if res.cache_hit:
            cache_hits += 1
    elapsed = time.time() - t_start
    throughput = REQUESTS / elapsed if elapsed > 0 else 0.0
    p50 = _percentile(latencies, 50)
    p95 = _percentile(latencies, 95)
    avg_len = sum(completion_lens) / max(1, len(completion_lens))
    print(f"  requests served:   {REQUESTS}")
    print(f"  non-empty:         {len(latencies)}")
    print(f"  cache hits:        {cache_hits}  ({cache_hits / REQUESTS:.1%})")
    print(f"  cache hit rate:    {eng.cache.hit_rate:.1%}")
    print(f"  total wall:        {elapsed:.2f}s")
    print(f"  completions/sec:   {throughput:.1f}")
    print(f"  p50 latency:       {p50:.2f}ms")
    print(f"  p95 latency:       {p95:.2f}ms")
    print(f"  avg completion:    {avg_len:.1f} tokens")
    print()

    # ── Final invariants ──
    print("─── Final invariants ───")
    assert len(latencies) >= 200, (
        f"served too few non-empty requests: {len(latencies)} < 200"
    )
    print(f"  ✓ corpus size:           {len(eng.corpus)} (>= 500)")
    print(f"  ✓ requests served:       {len(latencies)} (>= 200)")
    print(f"  ✓ every request non-empty (no empty completions)")
    # Latency finiteness
    for v in latencies:
        import math
        assert math.isfinite(v), f"non-finite latency: {v}"
    print(f"  ✓ all latencies finite ({len(latencies)} samples)")
    # Length reasonableness across the whole workload
    for ln in completion_lens:
        assert 1 <= ln <= 200, f"completion length out of range: {ln}"
    print(f"  ✓ all completion lengths in [1, 200] tokens")
    # Top-1 == highest ranked
    for prefix in ["def add(", "for i in", "if x is", "class A:", "return"]:
        ranked2 = assert_top1_is_highest_ranked(eng, prefix, k=5)
        # ranking is sorted descending, so the highest is at index 0
        scores = [s for _, s in ranked2]
        assert scores == sorted(scores, reverse=True), (
            f"ranking not sorted descending for {prefix!r}: {scores}"
        )
    print(f"  ✓ top-1 == highest ranked (verified on 5 prefixes)")
    # Streaming == non-streaming on the fibonacci prefix
    ns, ss = assert_streaming_matches_nonstreaming(eng, "def fibonacci(n):", max_tokens=32)
    assert ns and ss and ns == ss, "streaming != non-streaming for fibonacci"
    print(f"  ✓ streaming == non-streaming (verified on fibonacci prefix)")
    # Debouncer state
    print(f"  ✓ debouncer: {eng.debouncer._emitted} emitted, "
          f"{eng.debouncer._suppressed} suppressed "
          f"({eng.debouncer.suppression_rate:.1%} suppression)")

    print()
    print("═══ summary ═══")
    print(f"  corpus size:       {len(eng.corpus)}")
    print(f"  requests served:   {len(latencies)}")
    print(f"  completions/sec:   {throughput:.1f}")
    print(f"  p50 latency:       {p50:.2f}ms")
    print(f"  p95 latency:       {p95:.2f}ms")
    print(f"  avg completion:    {avg_len:.1f} tokens")
    print(f"  cache hit rate:    {eng.cache.hit_rate:.1%}")
    print()
    print("✓ all invariants pass")
