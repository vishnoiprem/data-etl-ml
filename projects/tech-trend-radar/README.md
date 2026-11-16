# tech-trend-radar

> **Finds what is *accelerating* in tech across many developer platforms — and shows you the evidence for every claim.** No API key, no Docker, no cloud. `pip install`, `pytest`, `uvicorn`.

It exists to make one thing concrete: **how a raw feed of posts becomes a ranked, checkable claim that a topic is trending — and how much of that claim is actually supported.**

The distinction that drives the whole design: a topic that is *suddenly accelerating* beats one that is merely *loud*. Volume is easy — count the mentions. Acceleration means comparing the rate of mentions in a recent window against the rate in the baseline before it, and that is what separates "Kubernetes is popular" from "Kubernetes started being talked about three days ago."

## The core idea

```
mentions/hour in last 72h
────────────────────────────  =  ratio   →  this is the burst signal
mentions/hour in prior 168h
```

A topic with a ratio of 4.0 that has only 6 mentions is more interesting than one with 300 mentions and a ratio of 1.0. The second is just a popular topic. The first is a *burst*, and that is what a trend radar is for.

The score then blends three things, and the breakdown is returned with every result so the arithmetic can be checked:

| Component | Weight | What it captures |
| --- | --- | --- |
| **Acceleration** | `ratio × 0.6` (capped at 10×) | The burst itself. Volume-gated: if `ratio < 1.0` the topic scores **0**, however many mentions it has. |
| **Volume** | `log1p(recent) × 0.8` | Evidence weight. A burst of 2 mentions is not a trend. Log-scaled so 30 mentions is not 15× better than 2. |
| **Corroboration** | `+0.35` per extra platform (max 3) | Independence. The same topic on three platforms is a real signal; on one it is probably a community's local obsession. |

## Features

| | |
| --- | --- |
| **Six live sources, zero credentials** | Hacker News, GitHub, Stack Overflow, dev.to, YouTube, RSS/Atom. Reddit is supported but only activates when `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` are set — the adapter is absent from the registry entirely without them. |
| **Burst detection, not counting** | Rate over the recent window vs. the baseline, with Laplace smoothing so a brand-new topic gets a large but finite score instead of infinity. |
| **Evidence on every claim** | Each trend carries the mention counts, the platform list, a plain-English rationale, and links to the source posts. |
| **Honest confidence** | A topic seen on one platform is labelled *"Single platform only — this may be local to that community rather than a wider trend."* It is not dressed up as a trend. |
| **Survives dead sources** | One failing API produces a failed `FetchResult`, not an exception. The run continues and reports which source died. |
| **GitHub spam filtering** | Star-farmed repos, suffix-swap reposts and topic-stuffed repos are removed by five independent heuristics — see below. |
| **Semantic topic matching** | A post about a technology the vocabulary has never heard of still contributes to the nearest topic the radar tracks. Local open-weights embeddings, no API key, degrades to lexical-only when the model is missing. |
| **No LLM in the ranking** | The score is plain Python. See "Not this" below. |
| **Offline demo + snapshot seam** | `make fetch` writes an append-only snapshot; `make demo` and the tests read it. Tests need no network and no key. |

## Current live run

Real numbers from `make fetch` → `make eval` on 2026-11-16, against the public APIs, from the snapshot `data/snapshots/snapshot_20261115T232713Z.json`:

```
925 posts from 6 live sources, 0 failed
  hackernews 123 · github 60 · stackoverflow 597 · devto 100 · youtube 15 · rss 30

rank  topic    score  recent  baseline  ratio  platforms  confidence
 1    nvidia     8.46       8         0  16.00  3          high
 2    openai     5.41       3         0   6.00  3          medium
 3    amazon     5.06       3         0   6.00  2          medium
 4    apple      5.06       3         0   6.00  2          medium
 5    gemma      4.71       3         0   6.00  1          medium
 6    anthropic  4.35      12         4   2.67  3          high
 7    rust       3.01       7         6   1.08  3          high
 8    deepseek   2.60       4         2   1.60  2          medium
 9    token      2.53       3         2   1.20  3          medium
```

The top five are all new in the window — nothing in the baseline at all — and corroborated across two or three platforms. `token` is the instructive one: 3 recent mentions, but 2 in the baseline too, so it is *steady* rather than *accelerating*, and it lands at the bottom with a ratio of 1.20 despite being the most-mentioned topic in the corpus.

`nvidia` reaches a ratio of 16 because the semantic layer resolved *"Jensen Huang might return to Nvidia as CEO"* — a headline with no lexical handle on the technology in it, but unmistakably about it.

**The ranking changes as the corpus changes.** These numbers are from one collection run; a fresh `make fetch` produces a different ranking, which is the correct behaviour, not a bug. Earlier runs the same day surfaced entirely different topics — `react`, `token`, `llm`, `gemma` — and one run was dominated by a GitHub topic-stuffing farm before the filters in the next section were added. Treat the numbers above as an illustration of the output shape, not as a fixed benchmark.

### Evaluation

`make eval` is a gate, not a report — it exits non-zero when a threshold is missed. Measured against the snapshot above:

| Evaluation | Result | Threshold |
| --- | --- | --- |
| **Burst detection accuracy** | `1.0` — 4/4 accelerating topics in the top 4 | ≥ 0.9 |
| **Ranking precision@10** | `0.9`–`1.0` across runs | measured, not gated |
| **Ranking MRR** | `1.0` | measured, not gated |
| **Ranking NDCG@10** | `0.94`–`1.0` across runs | measured, not gated |
| **Source coverage** | 6 live sources, 924–927 posts | ≥ 4 sources, ≥ 100 posts |

The ranking metrics were `0.5`–`0.6` precision and `0.65`–`0.73` NDCG before the semantic layer landed, and `0.9`–`1.0` and `0.94`–`1.0` after. `MRR = 1.0` was stable either way, because the top-ranked topic was always in the gold set. The gold set itself is whatever the corpus happens to contain, so these are measurements of a corpus, not a benchmark — the numbers move when the corpus moves, which is why they are quoted as a range.

An evaluation with no snapshot to measure is reported as `SKIP` rather than `FAIL` — a missing input is not a failed measurement, and the gate has to stay usable before the first `make fetch`.

Burst accuracy is measured on a **synthetic corpus whose ground truth is known by construction** — topics that accelerate versus topics that are steady, spread evenly *by rate* across both windows. This is the only honest way to measure burst detection without hand-labelling a live corpus, and it tests the *detector* rather than the vocabulary.

Ranking metrics are deliberately **not** gated: what counts as "good" depends entirely on what the live corpus happens to contain, and a hard threshold there would just be a threshold on the live data's shape.

## Run it

```bash
make up           # install dependencies into the shared parent venv
make up-semantic  # also install the semantic layer (pulls in torch, ~2 GB)
make test         # 208 tests — offline, no API key, no network
make demo         # offline end-to-end walkthrough from a recorded snapshot
make fetch        # hit the live public APIs, write a snapshot
make eval         # the evaluation harness (exits non-zero on failure)
make api          # FastAPI on :8000
make lint         # ruff
```

The semantic layer is an **optional** install. `make up` gives you the full radar minus the embedding model; `make up-semantic` adds it. It is optional because `sentence-transformers` pulls in torch, which is a ~2 GB download that would otherwise dominate every install and every CI run. Without it the radar runs on the lexical extractor alone — fewer topics found, and no matching of a technology the vocabulary has never heard of. Nothing breaks; the difference is reported through `/health` and in the CLI output.

### CLI

```bash
python -m tech_trend_radar trends --limit 10      # the ranked trends
python -m tech_trend_radar topics rust            # one topic in detail
python -m tech_trend_radar sources                # source coverage
python -m tech_trend_radar report --out r.md      # markdown report
python -m tech_trend_radar json --limit 20        # machine-readable
```

Every command accepts `--offline` to read the last saved snapshot instead of collecting live.

### API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Status, post count, live sources, window sizes, semantic-layer state |
| GET | `/sources` | Per-source coverage — post count, ok/failed, error text |
| GET | `/trends` | Ranked trends. Filters: `limit`, `platform`, `min_score` |
| GET | `/topics/{topic}` | One topic with the posts and links that support it |
| POST | `/refresh` | Re-collect live |
| GET | `/report` | The markdown report as JSON |

```bash
curl localhost:8000/trends?limit=5
curl localhost:8000/topics/token
curl -X POST localhost:8000/refresh
```

Swagger UI: <http://localhost:8000/docs>

## How a topic is extracted

Extraction is four independent signals, unioned. This was the most-iterated part of the project — roughly ten rounds, each driven by inspecting the actual live ranking rather than by guessing.

1. **Known vocabulary** — a curated list of real technologies, including multi-word entries (`machine learning`, not just `machine` and `learning` separately).
2. **Structural n-grams** — capitalised phrases that recur across posts, with five rules that each fix a specific failure:
   - a capitalised word only names a topic if it **starts a sentence** (`"Working with docker today"` → no topic);
   - after trimming leading stopwords the phrase **head must still be capitalised** (`"Working with docker"` → no topic);
   - n-grams emit **every prefix** of the meaningful word run, and a phrase is dropped when a shorter recurring phrase is its prefix (`"The Widgetron release notes"` → `Widgetron`);
   - a run **stops at a known technology** (`"LLM works best locally"` → `LLM`, not `LLM works`);
   - **post-type prefixes are not topics** (`"Ask HN:"` names the kind of post, not a technology).
3. **Platform tags** — Stack Overflow and dev.to tags, minus a stoplist of community meta-tags (`discuss`, `career`, `beginners`).
4. **A semantic match** — a post about a technology the vocabulary has never heard of still lands near its nearest known neighbour, and contributes a mention to it.

Alongside that: source names and feed names are blocked (`hackernews`, `techcrunch`, `theverge`), publisher `<category>` values are demoted to metadata rather than treated as topics, person names are filtered prefix-aware so `Elon` is dropped but `Elon Musk Foundation` is not, and generic nouns that headlines capitalise constantly (`ghost`, `browser`, `server`, `cloud`) are excluded — "The Ghost in the Machine" is a film title, not a trend in ghost technology.

### The semantic signal

The three lexical signals only find topics they already know about. A post about a runtime released last week, named in a way the vocabulary cannot parse, contributes nothing — and if enough posts are like that, a real trend stays invisible. The fourth signal closes that gap.

A post title is embedded with a local sentence-transformer (`all-MiniLM-L6-v2`, open weights, no API key) and matched against the known technologies by cosine similarity.

**The descriptors matter more than the model.** Embedding the bare word `"rust"` gives a vector near every English sentence that uses the word "rust". Embedding `"the Rust systems programming language"` gives a vector near other programming languages. So each vocabulary entry carries a short descriptor, and the descriptor is what gets embedded.

**The threshold is deliberately high.** A title that is not about technology at all still has a nearest neighbour, and it scores about 0.11. A title about a technology the vocabulary happens to miss scores 0.40–0.63. The threshold sits at **0.35**, in the gap between the two:

| Title | Nearest match | Score |
| --- | --- | --- |
| "Introducing Zephyr, a new systems programming language" | `rust` | 0.65 |
| "All AI-generated code should be Open Source" | `copilot` | 0.60 |
| "What thousands of conversations look like inside a language model" | `llm` | 0.58 |
| "I built an open-source multi-agent DAG orchestrator and AST RAG engine" | `langgraph` | 0.40 |
| "Finally finished my morning run and made breakfast" | *(nothing)* | 0.11 |

**The signal never overrides a lexical one.** The evidence trail shows the word that actually appeared — `"rust"`, not `semantic match (0.65)`. More than that: **a semantic match is only added to a post the lexical extractor could not resolve at all.** Where the lexical signals have an opinion, they keep it.

That rule is not cosmetic — it is load-bearing for the acceleration math. A post that already mentions `docker` must not *also* count as a mention of `kubernetes` just because the two are adjacent to an embedding. Doing so inflates `kubernetes`'s count in *both* windows, and a topic whose counts are inflated in both windows has its burst flattened. Measured on the burst fixture: without the rule, "Everything about docker you need to know" also counted as `kubernetes`, pushing kubernetes from 9 recent / 1 baseline to 15 / 7 and dropping its ratio from 6.0 to 2.0 — enough to push a genuinely accelerating topic out of the top four. With the rule, burst detection accuracy is back to 1.0.

**The layer degrades.** If `sentence-transformers` is not installed, or the model weights cannot be loaded, the matcher reports itself unavailable and the radar runs on the lexical extractor alone. `/health` says which mode is live:

```json
{"semantic": {"enabled": true, "model": "sentence-transformers/all-MiniLM-L6-v2", "threshold": 0.35}}
```

Measured on a live 927-post snapshot, the layer resolved **45 posts the lexical extractor could not**, and took the ranked list from 6 topics to 10:

| Title | Resolved to |
| --- | --- |
| "Jensen Huang might return to Nvidia as CEO" | `nvidia` |
| "Huang Discusses Comeback as Nvidia Chief with Allies" | `nvidia` |
| "The Humans Are Coming for A.I.'S Jobs in *We Were Here*" | `anthropic` |
| "DefCon: Breaking into Amazon Lockers by Any Means Necessary" | `amazon` |
| "Please Implement a Quorum Database" | `duckdb`, `mysql` |
| "Show HN: Skillset: Easily curate and install agent skills" | `langgraph`, `mcp` |
| "All AI-generated code should be Open Source" | `copilot`, `cursor` |

The ranking improved as a side effect: `precision@10` went from 0.5–0.6 to **1.0**, and `NDCG@10` from 0.65–0.73 to **1.0**.

It also produces false positives. "The Lyttle Lytton Contest 2026 winners" scores 0.42 against `pytorch`; "Eclipse Mosquitto – An open source MQTT broker" scores 0.38 against `gitlab` and `kafka`. The threshold is tuned to catch genuine near-misses, and it catches some that are not.

## The GitHub spam problem

GitHub's `stars:>20` floor is not a filter. Star-farmed repositories pass it easily, and the farms also inflate fork counts, so neither absolute floors nor ratios are sufficient on their own. Five independent heuristics are applied, and it took measuring the actual spam to know which ones mattered:

| Heuristic | Spam observed | Real repo observed |
| --- | --- | --- |
| Fork/star ratio floor (`≥ 0.02`) | 5 forks / 670 stars = 0.0075 | 594 forks / 8,829 stars = 0.067 |
| **Same repo name under many owner accounts** | 12 owners | 1 owner |
| **Same repo *stem* under many owners** | 9 × `blender-ai-copilot-*` | 1 owner |
| **Topic stuffing** (more than 8 topics) | 12–21 topics | 1–3 topics |
| Fork-owner diversity via `/forks` | — | 100 distinct accounts |

Three of these were added after looking at a live snapshot, and each one was a different shape of the same problem:

- **The duplicate-name check** caught copies of one repo under many *owners*, but missed the commoner form: the same project reposted under a different **name suffix**. One snapshot held nine `blender-ai-copilot-*` repositories with 489–498 stars each — close enough that the star counts gave them away. Stripping a known filler suffix word and counting the stems catches them.
- **Topic stuffing** is the cheapest way to game a topic aggregator. GitHub allows 20 topics, and each one becomes a mention of a different topic — so one repository can report itself as twenty different trends. Genuine repositories in the same snapshot carried 1–3 topics; the stuffed ones carried 12–21. A repository over the cap is dropped outright.

The filters are applied to the **source**, not to the extracted topics. Removing the farm upstream means the junk never reaches the ranking; cleaning it up afterwards would leave the radar reporting trends that no real repository supports.

## Layout

```text
projects/tech-trend-radar/
├── app.py                      FastAPI layer: service singleton, filters, endpoints
├── conftest.py                 puts src/ on sys.path so pytest runs from anywhere
├── Makefile                    up / up-semantic / test / demo / fetch / eval / report / api / lint
├── requirements.txt            lower bounds only, with a comment on each
├── requirements-semantic.txt   the optional embedding model, kept out of the base install
├── pytest.ini                  testpaths + addopts
├── pyproject.toml              ruff config
├── scripts/
│   ├── fetch_snapshots.py      the only script that touches the network
│   └── run_demo.py             offline end-to-end walkthrough + report writer
├── src/tech_trend_radar/
│   ├── config.py               settings, windows, weights, env-var loading
│   ├── models.py               Post, FetchResult, stable post ids, JSON round-trip
│   ├── http.py                 one HTTP client: timeouts, retry with backoff
│   ├── collector.py            run the adapters, build and save the snapshot
│   ├── topics.py               the extraction layer: vocabulary + n-grams + tags
│   ├── semantic.py             local embedding matcher: title → nearest known tech
│   ├── burst.py                rates, ratios, cross-platform corroboration
│   ├── ranking.py              composite score, breakdown, summary, rationale
│   ├── evaluation.py           the acceptance harness
│   ├── cli.py                  the command-line interface
│   └── sources/
│       ├── base.py             adapter protocol; exceptions become failed results
│       ├── hackernews.py       Firebase front page + Algolia date sweep
│       ├── github.py           absolute-date query + five spam filters
│       ├── stackoverflow.py     one query per tag (a 5-tag union returns 0)
│       ├── devto.py            one call with the `tags` union parameter
│       ├── rss.py              RSS 2.0 + Atom via the stdlib; YouTube feeds
│       └── reddit.py            OAuth; absent from the registry without creds
├── data/snapshots/             append-only collection snapshots
├── reports/                    generated trend report + eval JSON
└── tests/                      205 tests, no network, no key
```

## What is real vs. designed

| Layer | Status |
| --- | --- |
| Six source adapters | **Working** against the live public APIs |
| Burst detection and ranking | **Working** — deterministic Python, unit-tested |
| Explanation and evidence | **Working** |
| GitHub spam filtering | **Working**, five heuristics, measured against real spam |
| Semantic topic matching | **Working** — local open-weights embeddings; measured against live posts. Optional install. |
| CLI, FastAPI app, demo script | **Working** |
| Evaluation harness | **Working** — burst accuracy is a gate with a synthetic ground truth |
| Reddit adapter | **Working but inert** — requires credentials; not exercised by the default run |
| The embedding model download | **Optional** — the layer degrades to lexical-only without it |

## Honest constraints

- **The ranking is deterministic Python. There is no LLM anywhere in the decision path.** The explanations are template-generated from the counts that produced the ranking — nothing "narrates" anything, because there is no language model in the loop at all. That is a deliberate trade: a scoring layer you can unit-test and audit is worth more than one you cannot. The embedding model is not a language model — it produces vectors, not text, and it never sees the ranking.
- **The live ranking changes between collection runs.** The numbers above are one run against one corpus, not a fixed benchmark.
- **The semantic layer is a nearest-neighbour guess, and it is wrong sometimes.** It maps an unknown technology onto the closest known one, which is the right move when the alternative is missing the topic entirely — but "The Lyttle Lytton Contest 2026 winners" lands on `pytorch` at 0.42. The threshold sits high enough to keep non-technical titles out, not high enough to make every match correct.
- **The semantic layer needs the model weights.** On first use it downloads ~90 MB from Hugging Face. After that it runs offline. Without it the radar is lexical-only, which is a real degradation, not a cosmetic one — it is the difference between finding `deno` in the corpus and not finding it. The install is optional for the same reason: `sentence-transformers` pulls in torch, and a ~2 GB dependency is not something to put in everyone's base install.
- **CI proves the degraded path.** The CI workflow installs the base requirements only, so the suite that runs on every push is the lexical-only one. The semantic tests skip themselves when the model is not cached. That is the right thing for CI to prove — most users will not have the model — but it does mean the semantic layer's own tests are not gated by CI. They run locally with `make up-semantic`.
- **Ranking metrics are measured, not gated.** `precision@10 ≈ 0.5` reflects a 13-topic gold set against 5 ranked topics, not a quality claim.
- **The burst-detection fixture is synthetic.** It measures the detector against a ground truth that is known by construction. It does not prove the detector works on messy real-world text — that is what the live run is for.
- **Reddit is untested in CI.** It needs OAuth credentials that a hermetic test suite cannot have.

## Not this

- **Not a tweet-sentiment bot.** There is a separate `realtime-crypto-sentiment` project that does single-platform X.com analysis. This one is multi-platform and count-independent.
- **Not a chatbot.** No LLM call, no prompt, no model endpoint. The output is a ranked list with evidence.
- **Not "top mentions".** Raw volume is deliberately gated behind acceleration — a topic with ratio 0.9 scores zero no matter how many mentions it has.
- **Not a keyword counter.** The topic layer is where the real work is, and where most of the iteration went. The embedding model extends it, but it does not replace it — the deterministic rules still own every topic the vocabulary recognises.
- **Not a tutorial.** Every number in the scoring function is a deliberate choice with a stated reason.
- **Not a social-media sentiment analyser.** It ranks topics; it does not score opinions about them.

## Interview notes

**Why acceleration instead of raw volume?**
Volume measures popularity, which is slow-moving and already well-served by existing trend lists. Acceleration measures *change*, and change is what makes a radar useful — a topic that tripled in three days is a different event from a topic that is always busy. Gating on acceleration is also what stops the radar from being a list of things everyone already knows. The cost: a topic that breaks late in the baseline window can be under-ranked, and genuinely steady topics never appear at all. That is the intended behaviour.

**Why Laplace smoothing on the baseline?**
A topic with 4 recent mentions and 0 baseline mentions has an undefined ratio. Raw, it is infinite, and the top of the ranking fills with topics that were mentioned once. `baseline_rate + 0.5` makes the ratio finite and large-but-bounded, so a new topic ranks above a fading one without permanently occupying the number-one slot. The prior is small enough not to distort topics with a real baseline.

**Why is corroboration worth 0.35 per platform?**
Because the failure mode of a multi-source radar is correlated noise — one community's enthusiasm leaking into the aggregation. A topic appearing on dev.to, Hacker News and Stack Overflow is three independent observations; the same topic on all three is one observation reported three times, which happens when a single viral post is syndicated. The bonus is capped at three platforms so a topic cannot buy its way to the top by being present on many low-quality feeds.

**Why is the score a weighted blend instead of a learned model?**
There is no labelled training set, and the thing being ranked — "is this topic accelerating" — has a transparent definition you can write down in three lines. A learned ranker would need labels nobody has, would be untestable against a known ground truth, and would hide its own arithmetic. The blend's weights are exposed in the `breakdown` field of every API response, so a disagreement with a ranking can be settled by reading three numbers.

**How do you know the detector actually detects bursts?**
The evaluation harness builds a corpus where the ground truth is known by construction: accelerating topics get a burst of recent mentions and almost none in the baseline, steady topics get a flat rate across both windows. Spreading the steady topics evenly *by rate* rather than by count matters, because the two windows are different lengths (72h vs 168h) — matching counts would make every steady topic look like it was accelerating. Accuracy is currently 1.0 against a threshold of 0.9, and `make eval` exits non-zero if it slips.

**Why not let an LLM pick the topics?**
Because the extraction rules are the part that has to be right, and an LLM's output on 900 titles is not a repeatable answer — it varies with the prompt, the model version, and the sampling seed. It would also make the "why is this trending?" answer and the ranking itself the same unverifiable blob. Keeping them separate means the ranking is auditable and the explanation is derived from the same numbers that produced the ranking. The semantic layer is a *countermeasure* to that, not a step towards it: an embedding model produces a vector and a similarity score, both of which are inspectable numbers, and it never touches the ranking. It also runs locally with open weights, so there is no prompt to vary and no endpoint to be down.

**Why descriptors instead of embedding the vocabulary words directly?**
Because several of the vocabulary words are ordinary English words. The vector for the bare word "rust" sits near every sentence that uses the word to mean corrosion; the vector for "the Rust systems programming language" sits near other programming languages. The same applies to "go", "next", "rust", "swift". Embedding the *descriptor* rather than the name is what makes the nearest-neighbour match mean something — and it is why the vocabulary needs a hand-written descriptor per entry, which is a real maintenance cost the lexical extractor does not have.

**Why 0.35, and not something lower?**
Because a threshold that is too low turns the layer into noise. Measured on a probe set: a title about a technology the vocabulary misses scores 0.40–0.63 against its nearest neighbour, and a title about nothing technical — a post about breakfast — still scores about 0.11 against *something*. The threshold has to sit in that gap, and 0.35 does with margin on both sides. The cost of sitting that high is that genuinely-adjacent technologies are missed; the cost of sitting lower is that the whole corpus starts contributing spurious mentions, and a topic's count stops meaning anything.

**How do you deal with spam, given that any of these signals can be gamed?**
Every one of them, and none of them alone. Stars can be bought, so the fork ratio and the fork-owner diversity check. Repository names can be swapped, so the name-stem check. Topics can be stuffed to 20, so there is a hard cap. Each heuristic was added after measuring the actual spam in a live snapshot, which is why there are five rather than one: a single one would have been defeated by the next variation. The general principle is that the filters act on the **source** rather than on the extracted topics. Cleaning up afterwards would let the radar report trends that no real repository supports, and the ranking would still look plausible — which is the worst failure mode for a tool whose whole promise is that its claims are checkable.

**Why does the harness report a missing snapshot as SKIP rather than FAIL?**
Because they are different things. A missing snapshot means the measurement never ran — there is nothing to fail. Failing it would make `make eval` unusable in exactly the situation where it is most useful to run it: before the first `make fetch`. A snapshot that *is* present but has three sources and forty posts is a genuine coverage failure and still fails the gate.

**Where would this break at scale?**
The collector holds every post in memory and the snapshot is a single JSON file — fine for ~1,000 posts, wrong for 100,000. Topic extraction is O(posts × n-grams) in pure Python with no caching. There is no incremental state, so every run re-reads and re-scores the whole window. There is no rate-limit coordination across concurrent collectors, no circuit breaker for a source that fails slowly, and no scheduling — `make fetch` is manual. The window boundaries are hard-coded at collection time, so a snapshot older than 72 hours has an empty recent window by definition. The GitHub fork-diversity check costs one request per candidate and leans on GitHub's 60-requests-per-hour unauthenticated budget, which is the real ceiling on how large the candidate set can get. The semantic layer embeds the whole corpus in one batch — 926 titles took 3.8 seconds on CPU — but that batch is held in memory too, so it inherits the same ceiling as the collector.

---

**Last updated:** 2026-11-16
**License:** MIT — use freely in your own courses, prototypes, and products.

---

**Last updated:** 2026-11-15
**License:** MIT — use freely in your own courses, prototypes, and products.
