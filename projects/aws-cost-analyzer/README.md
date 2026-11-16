# AWS Cost Analyzer — S3 cost root-cause analysis

**Find where the S3 money went, and why.**

You open the Cost Explorer console, filter to `TagKey INCLUDES ["Data", "Data-Squad"]`,
and the bill is up. The console tells you *that* you spent. It never tells you *why*.

This tool answers the four questions the console won't:

| # | Question | Detector |
|---|---|---|
| **D1** | Which bucket or prefix grew, and by how much? | `growth` |
| **D2** | Which access pattern cost the money? | `access` |
| **D3** | Which lifecycle rule is missing or mis-scoped? | `lifecycle` |
| **D4** | Which tag or squad is doing the spending? | `allocation` |

---

## The one design decision that matters

**The model explains. Python decides.**

A local LLM (Ollama, optional) writes one paragraph of prose explaining a finding
and how to fix it. It cannot change a severity, a dollar figure, a basis, a
confidence, a recommendation, or a finding ID. That is enforced structurally, not
by convention:

- The router returns a **string**. There is no path by which a model returns a number.
- `apply_narrative()` writes exactly one field: `finding.narrative`.
- A test feeds a router that returns `"$9,999,999.99 ... Severity should be high ...
  Savings: $500,000"` and asserts every other field is byte-identical afterwards.

So the analysis is deterministic Python you can read, argue with, and test. The
prose is a convenience on top of it.

Every dollar figure carries its **basis**, so a reader can always tell a
measurement from a calculation:

| Basis | Meaning |
|---|---|
| `measured` | The number appears on the bill. |
| `modelled` | An observed volume multiplied by a rate from the rate card. |
| `upper_bound` | A ceiling on something that could not be measured. |

The wording is **"avoidable cost at the observed volume"** — never "savings".
You cannot measure money you did not spend.

---

## Quick start

```bash
cd projects/aws-cost-analyzer

make up      # install dependencies into the shared parent venv
make test    # 301 tests — offline, no credentials, no network
make demo    # end-to-end analysis on the synthetic corpus
make eval    # the acceptance gates
make lint    # ruff
```

`make demo` needs nothing: no AWS account, no API key, no model server. It
analyses a synthetic six-month corpus and writes `reports/cost_analyzer_report.{json,txt}`.

To pull your own data:

```bash
make fetch   # needs AWS credentials -> data/snapshots/*.json
```

Then analyse the snapshot:

```bash
python -m aws_cost_analyzer.cli analyze --latest
python -m aws_cost_analyzer.cli analyze --snapshot data/snapshots/xxx.json
python -m aws_cost_analyzer.cli analyze --demo --json
```

---

## The eval harness is the proof

A detector tested on real data proves nothing, because nobody knows whether it
found a growth pattern or invented one. So the ground truth is known **by
construction**: a synthetic six-month corpus with planted anomalies **and planted
decoys**.

The decoys matter as much as the anomalies. Each sits *just below* a plausible
threshold, so a detector that fires on them is demonstrably crying wolf:

- a bucket that grew 100% but only to $30
- a bucket that grew 60% but is seasonal — it grew in the same month last year
- a squad that doubled from $12 to $36
- a bucket that is simply stable

```
  [PASS] min_growth_recall                  1.0000 >= 1.00   1/1 planted growth anomalies found
  [PASS] min_access_recall                  1.0000 >= 1.00   1/1 planted access anomalies found
  [PASS] min_lifecycle_recall               1.0000 >= 1.00   1/1 planted lifecycle anomalies found
  [PASS] min_allocation_recall              1.0000 >= 1.00   1/1 planted allocation anomalies found
  [PASS] min_target_match                   1.0000 >= 1.00   4/4 anomalies matched by exact target
  [PASS] max_false_positives                0.0000 <= 0.00   0 decoy(s) fired
  [PASS] max_unbacked_modelled              0.0000 <= 0.00   0 modelled figure(s) with no volume evidence
  [PASS] max_savings_without_basis          0.0000 <= 0.00   0 savings figure(s) with no basis
  [PASS] max_savings_to_measured_ratio      0.0016 <= 1.00   claimed 27.00 against 16,858.00 measured (0.16%)
  [PASS] min_tag_filter_match               1.0000 >= 1.00   the console's TagKey INCLUDES maps to the API's CONTAINS
  [PASS] min_ce_normalizer_rows             1.0000 >= 1.00   1 row(s) from one period

Acceptance: PASS
```

Three of these gates are worth explaining, because they are what make the
harness meaningful rather than ceremonial:

- **`min_target_match = 1.00`** — recall alone is cheap. "Some S3 bucket grew"
  scores 1.00. Requiring the *exact* target string forces real attribution.
- **`max_false_positives = 0`** — the decoys are the test.
- **`max_savings_to_measured_ratio = 1.00`** — structural, not fixture-dependent.
  The tool may not claim more avoidable cost than the measured spend it came
  from. This catches the "modelled $400,000 on a $12,000 bucket" failure mode.

LLM prose quality is **not** gated. The narrative is unverifiable text, and a
gate on it would be a gate on taste.

---

## Four AWS landmines this project steps over

These were all verified against the API rather than assumed, and each one
fails *silently* — no error, just wrong numbers.

### 1. `INCLUDES` is a console-only operator

The console URL encodes:

```
filter=[{ dimension: { id: "TagKey" }, operator: "INCLUDES", values: ["Data", "Data-Squad"] }]
```

`INCLUDES` is **not** in the API's `MatchOptions` enum. The valid set is
`EQUALS, ABSENT, STARTS_WITH, ENDS_WITH, CONTAINS, CASE_SENSITIVE,
CASE_INSENSITIVE, GREATER_THAN_OR_EQUAL`. The API equivalent of the console's
`INCLUDES` is **`CONTAINS`**.

This translation lives in exactly one place (`tag_filter.py`) and is locked by
a fixture-equality regression test. It is the single most likely way to
quietly show you different numbers than the console does.

### 2. `TimePeriod.End` is exclusive

Your window ends `2026-10-31`. Sending that literally makes **October vanish
with no error at all**. The fetcher sends `End="2026-11-01"` instead.

### 3. `GroupBy` keys are positional

`Groups[].Keys[i]` corresponds to `GroupDefinitions[i]`, not to a name. So
`CostRecord.group` is a **tuple**, never a dict: a `GroupBy=[SERVICE]` layout
and a `GroupBy=[SERVICE, TAG]` layout are different dimension spaces and must
not be flattened into one namespace.

### 4. moto does not implement Cost Explorer

moto 5.x implements S3 lifecycle, `list_objects_v2` and CloudWatch metrics
faithfully — but `ce.get_cost_and_usage` returns an **empty** `ResultsByTime`
and `get_cost_and_usage_with_resources` raises `ParamValidationError`.

So **every Cost Explorer test runs against a recorded payload**, never moto.
Testing CE against moto would have produced tests that pass while asserting
nothing.

---

## Honest constraints

These are properties of the tool, stated rather than hidden:

- **Cost Explorer data lags 24h+, and the current month is `Estimated`.**
  Incomplete periods are excluded *entirely* — never divided, never compared —
  and **the dropped periods are named** in the report.
- **The rate card is illustrative, us-east-1, hand-checked** as of 2026-11-16.
  It is not fetched from the Pricing API and is not authoritative for billing.
  Every modelled figure is labelled `modelled`, and a region mismatch is
  always stated in the report header.
- **"Avoidable cost at the observed volume", never "savings".** There is no
  measured saving, because you cannot measure money you did not spend.
- **A modelled figure must carry a volume `Evidence` item.** A modelled number
  with no volume is a guess wearing a number. The eval gate
  `max_unbacked_modelled = 0` enforces this.
- **Tag coverage is measured and stated.** If the tagged total covers less than
  90% of the unfiltered service total, the gap is reported and confidence is
  capped at 0.60.
- **The narrative is unverifiable prose.** The deterministic `summary` is
  authoritative and is printed first; the model cannot change a finding.
- **Lifecycle transitions honour AWS's real constraints**: 30/90-day minimum
  ages, a 128 KB floor for Infrequent Access (below which you are billed at
  128 KB anyway), and **retrieval charges subtracted** from the saving. If the
  net is ≤ 0, nothing is emitted — a Glacier transition that cancels its own
  saving is not a recommendation.
- **Prefix byte counts are estimates.** Exact per-prefix bytes need S3
  Inventory or Storage Lens. v1 gives bucket-level *measured* bytes and
  prefix-level *estimated* shares, labelled `measured` vs `upper_bound`.
- **Access logs may be off.** CloudWatch `AWS/S3` request metrics are
  **per-bucket only** — they cannot name a prefix. Only S3 server access logs
  can. When logging is disabled the tool says so and asks you to enable it,
  rather than passing bucket-level counts off as prefix-level ones. And when
  the log totals disagree with CloudWatch by more than 20%, coverage is
  incomplete and confidence is capped at 0.50.
- **`REST.GET.BUCKET` is a LIST, not a GET.** It is billed at roughly ten
  times the GET rate. Getting this wrong inverts the finding.
- **The tool is read-only by construction.** There is no code path that can
  delete a bucket, write a lifecycle rule, or put an object. `ALLOWED_ACTIONS`
  contains only `Get*`, `List*` and `Describe*`, and a test asserts it.

---

## Layout

```
projects/aws-cost-analyzer/
├── README.md · Makefile · pytest.ini · conftest.py · pyproject.toml
├── requirements.txt · app.py                  # FastAPI app
├── data/
│   └── snapshots/       # live pulls (git-ignored — real account data)
├── reports/             # generated (git-ignored)
├── scripts/
│   ├── fetch_aws.py     # the ONLY script that builds real AWS clients
│   └── run_demo.py      # offline end-to-end
├── src/aws_cost_analyzer/
│   ├── config.py        # settings, thresholds, the exclusive-end rule
│   ├── models.py        # CostRecord, Evidence, Finding
│   ├── pricing.py       # rate card, the measured/modelled split
│   ├── tag_filter.py    # the INCLUDES -> CONTAINS translation
│   ├── ce_normalizer.py # AWS's nested ResultsByTime -> flat CostRecords
│   ├── aws_client.py    # DI'd boto3 clients, --dry-run, pagination
│   ├── snapshots.py     # read/write snapshots
│   ├── narrative.py     # LLMRouter / StubRouter / OllamaRouter
│   ├── report.py        # text + JSON report
│   ├── evaluation.py    # planted corpus + acceptance gates
│   ├── cli.py           # the command line
│   └── detectors/
│       ├── growth.py · access.py · lifecycle.py · allocation.py
│       └── registry.py  # run all four, stable finding ids
└── tests/               # 14 files, 301 tests
    └── fixtures/        # recorded CE payloads (tracked)
```

### Two rules the code follows everywhere

**`fetch_aws.py` is the only script that constructs a real AWS client.**
Everything else reads a snapshot. An analysis is therefore always
reproducible from something on disk — you can re-run it six months later and
get the same answer.

**`fetch_aws.py --dry-run` prints every API call the run *would* make**,
including the exact filter payload, without making any of them. A mistyped
window or a wrong filter is visible before it becomes a snapshot.

---

## The API

```bash
uvicorn app:app --reload
```

| Route | What it gives you |
|---|---|
| `GET /health` | Snapshot count, rate-card region, router name |
| `GET /findings?detector=growth` | Findings with summary, evidence, and every figure's basis |
| `GET /report` | The same view as the console URL, offline |
| `GET /detectors` | The four detectors and what each one claims |

---

## What this project deliberately does not promise

1. **Per-prefix *measured* bytes.** That needs S3 Inventory or Storage Lens.
   v1 gives bucket-level measured bytes and prefix-level estimated shares,
   labelled as such.
2. **Naming the job that hammered a prefix.** That needs S3 server access
   logging, which most accounts have off. The tool detects that and says so.
3. **A model that finds things Python did not.** The model writes the
   explanation; the analysis is deterministic Python you can read and argue
   with.
