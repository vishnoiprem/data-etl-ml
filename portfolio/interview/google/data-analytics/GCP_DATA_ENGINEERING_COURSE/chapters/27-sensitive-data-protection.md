# 7.1 — Sensitive Data Protection & DLP

> **Section 7 · Governance, Security & BI · Lecture 7.1 · 8:00**

## 🎯 What you will learn

- What Sensitive Data Protection (DLP) is, and the inspect / de-identify model
- **InfoTypes**: the built-in catalogue, custom InfoTypes, and the `Likelihood` scoring that decides what counts as a finding
- **Templates**: the difference between a configured template and a de-identify template, and why it matters
- The **de-identification methods**: masking, character masking, tokenization, hashing, format-preserving encryption, replacement, and date shifting
- **Findings and redact findings** — a finding is a sensitive value *in context*, not a bare value
- The **jobs API**: `InspectContent` and `DeidentifyContent`, plus Cloud Storage scan jobs
- The overlap and word-boundary problem: why "Zip" fires when you mean a postcode
- The `L` mode versus `L`-basic configuration, and how it changes your findings
- The cost model, and where DLP cost surprises people
- When DLP is the right tool and when a regex is enough

---

## 🧠 Concept

### What DLP is, precisely

Sensitive Data Protection is a **managed detection and redaction service**. You describe what sensitive data looks like, and DLP either:

- **Inspects** content and reports **findings** — where sensitive data appears, and how confident it is — or
- **De-identifies** content by replacing sensitive values according to rules you define.

**The single most important idea in this chapter** is that DLP operates on **findings, not on values**.

> A **finding** is a *sensitive value in a context that matched an InfoType's pattern and likelihood threshold*.

The same string can be a finding or not, depending on context. `"4111 1111 1111 1111"` is a credit-card finding. `"4111111111111111"` with no formatting may not match the Luhn-checked regex. `"Zip"` is a finding for the `POSTAL_CODE` InfoType in some configurations and not in others. This contextual nature is why DLP behaves the way it does, and why tuning it is a real operational discipline.

**What DLP is not:**

- It is not a general-purpose regex engine with a UI. It is a probabilistic, context-aware classifier built on Google's models, plus an enormous catalogue of tuned regexes.
- It is not a data-cleanup tool. It finds and redacts; it does not validate business rules.
- It is not free. Inspection is priced per GB, with a monthly free allowance.

### The two operations

**Inspection** answers: *does this data contain anything sensitive?* The output is a list of findings, each with:
- The **InfoType** that matched (`PHONE_NUMBER`, `EMAIL_ADDRESS`, `CREDIT_CARD_NUMBER`, `US_SOCIAL_SECURITY_NUMBER`, ...).
- The **Likelihood** score — `LIKELY`, `VERY_LIKELY`, `POSSIBLE`, `UNLIKELY`, `VERY_UNLIKELY`.
- The **byte offsets** of the match within the content.
- The **redact** and **crypto key** fields for de-identification templates.

**De-identification** answers: *replace the sensitive parts according to my rules*. The output is the transformed content plus a list of the transform results.

The architectural insight: **de-identification is inspection plus a transformation.** Internally, DLP finds the sensitive spans and then applies the method from the template to each span. This is why a de-identify template needs a "deidentify" section and a "config" section, and why you can configure the *finding* behaviour (which InfoTypes, what likelihood) separately from the *transformation* behaviour.

### InfoTypes: the catalogue

An **InfoType** is a detector. Each one has:
- A **name** and an **id**.
- A **regular expression** or a set of patterns that identify candidate values.
- **Likelihood scoring** rules — how confident the detector is that a matched value is really of that type.
- Optionally, **validation rules** such as Luhn checksum for credit cards, or a length check.
- For some types, **context-based detection**: the detector looks at surrounding words ("social security number", "SSN", "telephone") to raise or lower confidence.

**The built-in catalogue** is large — over 200 InfoTypes. The important families:

| Family | Examples |
|---|---|
| **Identifiers** | `PERSON_NAME`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `US_SOCIAL_SECURITY_NUMBER`, `PASSPORT`, `DRIVER_LICENSE` |
| **Financial** | `CREDIT_CARD_NUMBER`, `IBAN_CODE`, `SWIFT_CODE`, `US_BANK_ACCOUNT_NUMBER`, `US_INVESTMENT_NUMBER`, `VAT_ID` |
| **Healthcare** | `MEDICAL_INFO` (the whole HIPAA identifier set), `US_NPI_NUMBER`, `ICD_CODE`, `DEA_NUMBER` |
| **Location** | `LOCATION`, `STREET_ADDRESS`, `POSTAL_CODE`, `IP_ADDRESS`, `URL`, `GEO_COORDINATES` |
| **Technical** | `HTTP_COOKIE`, `PASSWORD`, `AWS_ACCESS_KEY_ID`, `GITHUB_TOKEN`, `JSON_KEY` |
| **Business** | `DATE`, `TIME`, `AGE`, `GENDER`, `RACE`, `EMPLOYEE_ID`, `CUSTOMER_ID` |

**Two categories deserve special attention:**

- **`PHONE_NUMBER`** — Google's detector handles international formats, and it can distinguish a phone number from a numeric ID by context.
- **`POSTAL_CODE`** — this is where the infamous "Zip" false positive lives. More on that below.

### Custom InfoTypes

When the built-in catalogue does not cover your data, you build a **custom InfoType**. Two mechanisms:

**Regex-based custom InfoType.** You provide a pattern and a set of match patterns. DLP applies the regex, then scores each match using `likelihood` rules you define. The rules are:

- A **minimum likelihood** — matches below this are not reported.
- A **maximum likelihood** — matches above this are excluded (used to suppress confident-but-wrong matches).
- **"Boosted" likelihood** — if the matched value appears within N characters of a set of "boosting" words, its likelihood is raised. This is how you teach DLP that `"acct"` near a number means it is an account number.
- **"Redacted" likelihood** — if the matched value appears near one of a set of "redacting" words, its likelihood is lowered. This is how you teach DLP that `"zip code"` near a number is not a postcode but a compression factor.

**This boosting and redaction mechanism is the single most powerful feature of DLP for practical work**, and it is the answer to the "Zip" false positive.

**Stored InfoType.** You upload a dictionary of known values (customer IDs, employee IDs, your own reference numbers). DLP matches exact values and near-matches, with the ability to detect single-character typos in the dictionary. This is the right tool for "these are our internal account numbers" — a problem no regex solves.

### The `Likelihood` scoring

Every finding carries a likelihood: one of `VERY_UNLIKELY`, `UNLIKELY`, `POSSIBLE`, `LIKELY`, `VERY_LIKELY`.

**Why it exists:** because detectors are heuristic, DLP does not report every match. It reports matches it is confident about. The likelihood is the confidence.

**The threshold is per-InfoType and configurable** on a template:

```json
{
  "infoType": "EMAIL_ADDRESS",
  "minimumLikelihood": "LIKELY"
}
```

Setting `minimumLikelihood` to `VERY_LIKELY` reduces false positives and increases false negatives. Setting it to `POSSIBLE` or lower catches more, including more junk.

**The `L` mode versus `L`-basic configuration** — this is a real and slightly confusing terminology that trips people up:

- **`L`-basic** (the default for many InfoTypes): the detector uses only the pattern plus validation rules. A 16-digit string that passes Luhn is a credit card. It does not care what surrounds it.
- **`L` mode** (`"mode": "L"` in the InfoType's `detectionConfig`): the detector additionally applies **contextual analysis** — it looks at the surrounding text to adjust confidence. A number near the word "visa" is more likely a credit card; a number near "order" is less likely.

**The practical difference:**

| | `L`-basic | `L` mode |
|---|---|---|
| Context awareness | None | Reads surrounding words |
| False positives | Higher | Lower |
| False negatives | Lower | Higher (a true positive with no context can be missed) |
| Cost | Same | Slightly more per byte (more analysis) |
| Use when | You control the data shape | Data is free text or mixed |

**When to use `L` mode:** free-form text — support tickets, emails, chat logs, PDFs of contracts. When the data is a well-known structured column set — a CSV with an `email` column — the pattern is enough and `L` mode adds cost and latency for no benefit.

**The deep subtlety:** in `L` mode, a value with **no surrounding context at all** (a bare token in a CSV cell) can be down-weighted, because the detector has no evidence either way. If your structured data has no context and you enable `L` mode, you may lose real findings. This is the opposite of what people expect, and it is why the rule is "enable `L` mode for unstructured text, leave it off for structured data".

### Templates

A **template** is a reusable configuration. There are two kinds and the distinction is easy to get wrong.

**A configured template** ("configured inspect template") contains only **InfoType selections and likelihood settings**. It defines *what to look for* and *how confident you must be*. It has no de-identify section, because it does not transform anything. You use it with `InspectContent` and with Cloud Storage scan jobs.

**A de-identify template** contains **two sections**:

```json
{
  "deidentifyConfig": {
    "infoTypeTransformations": [
      {
        "infoType": "EMAIL_ADDRESS",
        "primitiveTransformation": {
          "replaceWithValue": {"value": "[REDACTED]"}
        }
      },
      {
        "infoType": "PHONE_NUMBER",
        "primitiveTransformation": {
          "characterMask": {
            "maskingCharacter": "*",
            "charactersToMask": 4,
            "charactersToSkip": 0,
            "reverseOrder": false
          }
        }
      }
    ],
    "deidentifyContentFound": "CRYPTO_REPLACE"
  },
  "config": {
    "infoTypes": [
      {"infoType": "EMAIL_ADDRESS", "minimumLikelihood": "LIKELY"},
      {"infoType": "PHONE_NUMBER", "minimumLikelihood": "LIKELY"}
    ]
  }
}
```

- **`config`** — the *detection* settings. Which InfoTypes, what minimum likelihood, and the `mode` for each.
- **`deidentifyConfig`** — the *transformation* settings. What to do with each InfoType, and what to do with content that was found but has no explicit rule (`deidentifyContentFound`).

**The `deidentifyContentFound` field is the safety net, and it is the most important line in the whole template.** It has two values:

- **`CRYPTO_REPLACE`** — replace every found value with a token. This is the **safe default**. Nothing found ever passes through untouched.
- **`REDACT`** — replace only the values that have an explicit transformation rule; found values without a rule are left as they are. **This is a data-leak footgun.** If you set `REDACT` and forget a rule, sensitive data leaves the system unmodified with no error.

**Always use `CRYPTO_REPLACE` unless you have a specific, audited reason not to.** This single setting is the difference between "sensitive data is guaranteed redacted" and "sensitive data is redacted except for the cases I did not think about".

### The de-identification methods

These are the **primitive transformations**. Each one is a different trade-off between reversibility, utility, and the risk of re-identification.

**1. Masking (`replaceWithValue`)**

Replace the entire matched span with a fixed string. `[REDACTED]`, `***`, `<PHONE>`.

- **Reversible?** No.
- **Utility?** Only the fact that something was there. You cannot group by the value, count distinct values, or join on it.
- **Use when** the value has no analytical value at all — a free-text field, a comment body.

**2. Character masking (`characterMask`)**

Mask a fixed number of characters, optionally skipping some from the left or the end.

- **Reversible?** No.
- **Utility?** Partial. You can still see the format and a suffix, so you can bucket, group by prefix, or verify a formatting pattern.
- **Use when** you need to preserve the *shape* — a partially masked card number still proves the format was right. This is what the course's `redact_pii(value, keep_last=4)` helper does.

**3. Tokenization (`cryptoTokenization`)**

Replace the value with a **deterministic token** — the same input always produces the same output, so you can group and join on it, but the token reveals nothing.

This is implemented as **Format-Preserving Encryption (FPE)**: a token is a ciphertext over a custom alphabet. Two properties follow:

- **Deterministic:** the same plaintext yields the same token. Group-by and joins still work.
- **Format-preserving:** the token has the same length and character class as the original. A 16-digit card number becomes a 16-digit token; a UK postcode becomes a valid-looking postcode.

Format preservation is a genuine engineering tool (you can still validate a token the way you validated the original), but it is also a **re-identification risk**: it preserves the *structure* of the data, which is itself information.

- **Use when** you need analytics on the sensitive value — distinct user counts, cohorting, per-entity revenue — without exposing the value.

**4. Format-Preserving Encryption (`replaceWithFfx`)**

Encrypts the value, preserving its format, using a key from Cloud KMS. The result is *reversible* by anyone with the key.

- **Reversible?** Yes, with the KMS key.
- **Use when** the original value must be recoverable — a token vault, a lookup table — but you do not want it in the analytics dataset. The encrypted value goes into the warehouse; the decryption happens in a tightly-controlled service.

**5. Hashing (`replaceWithHash`)**

Replace with a hash of the value, using a **keyed** hash (HMAC) so that an attacker without the key cannot confirm a guessed value.

- **Reversible?** No — but it is **verifiable**: you can re-hash a candidate and compare. This makes it a **pseudonym**, not an anonymisation.
- **Utility?** Excellent for joins and grouping.
- **Risk:** the output space is small for low-entropy inputs. A 4-digit PIN has 10,000 possible hashes — brute-forceable by anyone who can submit candidates and read the outputs. **Hashing is only safe for high-entropy values**, and "high entropy" means at least 64 bits of genuine randomness.
- **Use when** you need deterministic joins and the input has enough entropy. Otherwise use tokenization with FPE.

**6. Replacement with `redact`, `cryptonym`, `redact-deterministic`**

This is the modern, unified replacement mechanism, and it is worth understanding because it replaces the older primitives in new templates.

- **`redact`** — replace the value with a placeholder. The placeholder can be a fixed string or a **per-value token**. This is the recommended default for structured identifiers.
- **`cryptonym`** — replace with a **deterministic token** derived from a KMS key. Same input → same token, and the token is an encrypted value. This is the recommended way to keep analytics on pseudonymised identifiers.
- **`redact-deterministic`** — replace with a deterministic token, but with the *position* preserved in the token so that different values in the same record get distinguishable tokens.

**`cryptonym` is the modern answer to "I need to group by user_id but not expose it".** It requires a KMS key and a Cloud KMS CryptoKeyVersion resource; you must enable it in the template's `deidentifyConfig`.

**7. Date shifting (`shiftDate`)**

Shift a date by a consistent number of days.

- **The critical property:** the shift is **consistent per template/version**, not per value. Every date in a record moves by the same amount, so intervals and trends survive.
- **Use when** you need time-series analytics on dates (retention curves, seasonality) but must obscure the actual dates.
- **Risk:** dates are **quasi-identifiers**. Combined with other attributes they can re-identify individuals. A shifted date preserves the exact interval structure, which is more information than a year bucket — and year bucketing is the GDPR-preferred minimisation.

### Findings and redact findings

**A finding** is the record DLP produces for one detected sensitive span:

```json
{
  "infoType": "EMAIL_ADDRESS",
  "likelihood": "VERY_LIKELY",
  "detected": {"byteOffset": 12, "byteLength": 22, "unicodeSubstring": "alice@example.com"},
  "redacted": "[REDACTED]"
}
```

**The `byteOffset` / `byteLength` framing is important and often misunderstood.** Offsets are in **bytes**, not characters. In UTF-8, a character like `é` is 2 bytes and an emoji is 4. If you compute the substring with a character index, you will be off by a variable amount and extract the wrong text. Use byte offsets, or use the `unicodeSubstring` that DLP provides alongside them.

**A "redact finding"** is what DLP reports for a value that it found but redacted as part of a larger matched span. Concretely: if the pattern for `PHONE_NUMBER` matched a larger region that contains a `POSTAL_CODE`, DLP reports both, and the postal code is a *redact finding* — it was removed as a consequence of the phone-number redaction, not by its own rule.

**Why this matters operationally:** redact findings explain why a field is missing that you did not expect to be redacted. When you audit a de-identified dataset and find a column that is entirely `***`, the reason is usually a redact finding from an overlapping span, not a bug in your rule set.

**The overlap problem in detail.** Spans can nest. If a 20-character free-text field matches `CREDIT_CARD_NUMBER` on bytes 5–21, and `PHONE_NUMBER` on bytes 12–17, the two overlap. DLP resolves this by priority and by the order of the rules, and the result depends on the template. If you are de-identifying free text and your output looks wrong, **the overlap resolution is the first thing to check**, before you suspect your regex.

### The jobs API

Two request types do the work.

**`InspectContent`** — inspect a single piece of content.

```python
from google.cloud import dlp_v2

client = dlp_v2.DlpServiceClient()

response = client.inspect_content(
    request={
        "parent": "projects/my-project/locations/us-central1",
        "content": {"value": "Contact alice@example.com or call 555-123-4567"},
        "inspect_config": {
            "info_types": [
                {"info_type": "EMAIL_ADDRESS", "minimum_likelihood": "LIKELY"},
                {"info_type": "PHONE_NUMBER", "minimum_likelihood": "LIKELY"},
            ]
        },
    }
)

for finding in response.result.findings:
    print(f"{finding.info_type.name}: {finding.detected.unicode_substring}")
```

The response is a list of findings, each carrying the InfoType, the likelihood, the byte offsets, and the matched text:

```text
EMAIL_ADDRESS: alice@example.com
PHONE_NUMBER: 555-123-4567
```

**`DeidentifyContent`** — transform a single piece of content.

```python
response = client.deidentify_content(
    request={
        "parent": "projects/my-project/locations/us-central1",
        "content": {"value": "Contact alice@example.com or call 555-123-4567"},
        "deidentify_config": {
            "info_type_transformations": [
                {
                    "info_type": "EMAIL_ADDRESS",
                    "primitive_transformation": {
                        "replace_with_value": {"value": "[EMAIL]"}
                    },
                },
                {
                    "info_type": "PHONE_NUMBER",
                    "primitive_transformation": {
                        "character_mask": {
                            "masking_character": "*",
                            "characters_to_mask": 4,
                            "characters_to_skip": 3,
                        }
                    },
                },
            ],
            "deidentify_content_found": "CRYPTO_REPLACE",
        },
    }
)

print(response.deidentified_content)
```

Expected output:

```text
Contact [EMAIL] or call ********4567
```

**Installing the client.** The snippets above need the DLP client library and application default credentials:

```bash
pip install google-cloud-dlp
gcloud auth application-default login
```

Both calls are billed per GB of the content you pass in. Inspecting a single record is free of charge at any meaningful scale; the cost appears when you inspect whole buckets or tables.

**`CreateInspectJob` / `CreateDeidentifyJob`** — scan a whole Cloud Storage bucket. You point the job at `gs://bucket/path`, set a file predicate, and DLP walks the bucket. For a large bucket this is asynchronous, takes hours, and produces a job with a status and a findings report.

**The scan job is the right tool for a one-off audit**: "what sensitive data is in this bucket, and where?" The output is a findings report with counts by InfoType and the locations of the sensitive data.

**The right tool for ongoing enforcement** is `DeidentifyContent` called from a pipeline — a Dataflow job, a Composer task, a Dataprep flow's output step — with the template applied to every record as it lands.

### The overlap and word-boundary problem

This deserves its own treatment because it is the thing that makes a naive DLP setup unusable.

**The "Zip" false positive.** Consider a free-text support ticket:

```text
Customer asked about changing the compression Zip level on their order.
```

A `POSTAL_CODE` detector that looks for the literal token `Zip` will match the word "Zip" in "compression Zip level". If your template includes `POSTAL_CODE` with a `POSSIBLE` likelihood, this becomes a finding — and after de-identification, the word "Zip" in your dataset is replaced with `[REDACTED]`. The text now reads "compression [REDACTED] level", which is nonsense.

**The same problem in the other direction**: "Zip" is also a common US postal abbreviation. "Send it to 90210 Zip" should match.

**The fix is the `redacted` likelihood mechanism on a custom InfoType.** You define a custom InfoType for your postal code format, and you list the words that should *reduce* confidence — "compression", "level", "ratio", "file", "archive". You list the words that should *increase* it — "zip code", "postal", "postcode", "zip:".

```json
{
  "infoType": {
    "name": "US_POSTAL_CODE_CUSTOM",
    "regex": {"matches": [{"pattern": "(?i)\\b\\d{5}(-\\d{4})?\\b"}]},
    "likelihood": {
      "minimumLikelihood": "POSSIBLE",
      "redactedLikelihood": "VERY_UNLIKELY"
    }
  },
  "context": {
    "contextualRegex": {"matches": [{"pattern": "(?i)(zip|postal)\\s*code"}]},
    "boostedLikelihood": "VERY_LIKELY"
  }
}
```

**The word-boundary problem in general.** A regex like `\d{5}` matches the first five digits of a 16-digit card number. A regex like `\d{3}-\d{3}-\d{4}` matches the middle of a longer digit run. DLP's built-in detectors use anchoring and validation precisely to avoid this, but **custom InfoTypes are your responsibility** — anchor them with `\b` and validate them with a checksum where you can.

**The overlap problem, again, concretely.** In the same free-text ticket:

```text
Call 555-123-4567 ext. 89, or email alice@example.com, order 12345.
```

`PHONE_NUMBER` might match `555-123-4567 ext. 89` (14 characters) while `POSTAL_CODE` matches `12345`. `ORDER_ID` might match `12345`. Three findings, overlapping spans. DLP resolves them by priority; the higher-priority transformation wins for the overlapping region, and the lower-priority one becomes a **redact finding**.

**The operational consequence:** your de-identified output is only as predictable as your span-resolution understanding. When you validate a de-identification pipeline, **compare the input length, the output length, and the finding count** — and investigate any output where a number of digits changed unexpectedly.

### The cost model

From `project/core/cost_model.py`:

```python
SENSITIVE_DATA_PROTECTION_PER_GB = 0.10
```

**$0.10 per GB inspected**, after a monthly free allowance (historically 10 GB/month for inspect).

**The cost drivers:**

| Operation | Unit | What it means |
|---|---|---|
| **Inspect** | Per GB | $0.10/GB scanned |
| **De-identify** | Per GB | Priced per GB of *input* content processed |

**Where the cost surprises people:**

1. **Inspection is not free and not per-finding.** You are charged for every byte you inspect, whether or not anything is found. Scanning a 1 TB bucket to find 12 emails costs $102.40.
2. **Scanning the same data repeatedly.** A nightly bucket scan of a 500 GB bucket costs $50 every night, $1,500 a month. Scope the scan to what changed.
3. **The `L` mode costs slightly more per byte** because the contextual analysis is more work. For a full-bucket scan, this is measurable.
4. **The free allowance is small relative to enterprise usage.** Ten GB a month disappears instantly.
5. **Redaction does not stop the underlying data from existing.** De-identifying a copy leaves the original in place, still billed, still holding the sensitive data. If the goal is to *not have* the sensitive data, you must delete the original.

**The cost-benefit framing:** de-identification is cheap relative to the cost of a breach. $100 to inspect a terabyte that turns out to be full of card numbers is an excellent trade. DLP's cost is rarely the reason not to use it — the reason not to use it is usually that it is being asked to do a job it cannot do (it is not a validator).

---

## 🛠️ Hands-On

### Lab 1 — DLP in the service catalog

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, regions_for, REGIONS, services_by_category

service = get_service("sensitive-data-protection")
print(f"{service.id}: {service.name}")
print(f"  category     : {service.category}")
print(f"  data role    : {service.data_role}")
print(f"  summary      : {service.summary}")
print(f"  pricing      : {service.pricing_model}")
print(f"  key resources: {', '.join(service.key_resources)}")
print()

available = regions_for("sensitive-data-protection")
print(f"available in {len(available)}/{len(REGIONS)} regions")
missing = [r for r in REGIONS if r not in available]
if missing:
    print(f"  NOT available: {', '.join(missing)}")
else:
    print("  available everywhere — DLP has no regional restriction")
print()

for sibling in services_by_category("Security & Governance"):
    print(f"  {sibling.id:<28} {sibling.name}")
```

Expected output:

```text
sensitive-data-protection: Sensitive Data Protection
  category     : Security & Governance
  data role    : governance
  summary      : Discovery, de-identification and inspection of sensitive data.
  pricing      : Per inspected byte, after a free monthly allowance.
  key resources: Inspect Template, De-identify Template, InfoType, Job

available in 12/12 regions
  available everywhere — DLP has no regional restriction

  sensitive-data-protection    Sensitive Data Protection
```

### Lab 2 — The cost of scanning

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import SENSITIVE_DATA_PROTECTION_PER_GB, estimate

GB = 1024.0

print(f"DLP price: ${SENSITIVE_DATA_PROTECTION_PER_GB:.2f} per GB inspected")
print()

print(f"{'scan':<28} {'GB':>10} {'cost':>12}")
for tb in (0.05, 0.5, 1, 5, 10):
    gb = tb * GB
    cost = gb * SENSITIVE_DATA_PROTECTION_PER_GB
    print(f"{str(tb) + ' TB one-off':<28} {gb:>10,.1f} ${cost:>10,.2f}")
print()

# The recurring-scan trap.
daily_gb = 500
daily = daily_gb * SENSITIVE_DATA_PROTECTION_PER_GB
monthly = daily * 30
print(f"Scanning the same {daily_gb} GB bucket nightly:")
print(f"  per scan : ${daily:,.2f}")
print(f"  per month: ${monthly:,.2f}")
print(f"  per year : ${monthly * 12:,.2f}")
print()
print("Scope the scan to what changed, or scan once and track.")

est = estimate("sensitive-data-protection", inspected_gb=500)
print("Via cost_model.estimate:")
for line in est.lines:
    print(f"  {line.label:<20} {line.quantity:>10,.0f} {line.unit:<6} ${line.cost:>9,.2f}")
print(f"  {'TOTAL':<20} {'':>10} {'':<6} ${est.total:>9,.2f}")
```

Expected output:

```text
DLP price: $0.10 per GB inspected

scan                                 GB         cost
0.05 TB one-off                    51.2 $      5.12
0.5 TB one-off                    512.0 $     51.20
1 TB one-off                    1,024.0 $    102.40
5 TB one-off                    5,120.0 $    512.00
10 TB one-off                 10,240.0 $  1,024.00

Scanning the same 500 GB bucket nightly:
  per scan : $50.00
  per month: $1,500.00
  per year : $18,000.00

Scope the scan to what changed, or scan once and track.
Via cost_model.estimate:
  Inspection                  500 GB     $    50.00
  TOTAL                                  $    50.00
```

### Lab 3 — Why a regex is not a detector

The course's `looks_like_email` helper is a regex. Let's show exactly what it misses.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import looks_like_email, redact_pii

CANDIDATES = [
    "alice@example.com",
    "alice.smith@example.co.uk",
    "alice+events@example.com",
    "not-an-email",
    "alice@example",
    "ALICE@EXAMPLE.COM",
    "@example.com",
    "alice @example.com",
    "a@b.c",
]

print("looks_like_email — the course regex")
print(f"{'value':<32} {'match':>6}")
for candidate in CANDIDATES:
    print(f"{candidate:<32} {str(looks_like_email(candidate)):>6}")
print()

# The regex is a shape test, not a detector. It has three failure modes:
print("Failure mode 1 — shape but not a real address:")
print(f"  'a@b.c'      -> {looks_like_email('a@b.c')}  (TLD is one char)")
print(f"  'alice@example' -> {looks_like_email('alice@example')}  (no dot)")
print()
print("Failure mode 2 — real address but the shape does not match:")
print(f"  'alice@example.com' with a space -> {looks_like_email('alice @example.com')}")
print("  RFC 5321 allows quoted local parts: '\"a b\"@example.com'")
print(f"  '\"a b\"@example.com' -> {looks_like_email('\"a b\"@example.com')}")
print()
print("Failure mode 3 — the regex has no CONTEXT.")
print("  DLP knows that 'email' or 'contact' nearby raises confidence,")
print("  and that 'zip' or 'level' nearby lowers it.")
print("  The regex cannot: it sees a string, not a document.")
```

Expected output:

```text
looks_like_email — the course regex
value                             match
alice@example.com                  True
alice.smith@example.co.uk          True
alice+events@example.com           True
not-an-email                       False
alice@example                      False
ALICE@EXAMPLE.COM                  True
@example.com                       False
alice @example.com                 False
a@b.c                              True

Failure mode 1 — shape but not a real address:
  'a@b.c'      -> True  (TLD is one char)
  'alice@example' -> False  (no dot)

Failure mode 2 — real address but the shape does not match:
  'alice@example.com' with a space -> False
  RFC 5321 allows quoted local parts: '"a b"@example.com'
  '"a b"@example.com' -> False

Failure mode 3 — the regex has no CONTEXT.
  DLP knows that 'email' or 'contact' nearby raises confidence,
  and that 'zip' or 'level' nearby lowers it.
  The regex cannot: it sees a string, not a document.
```

### Lab 4 — The character-masking transformation

`redact_pii` is a character mask. Let's line it up against DLP's `characterMask` primitive.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import redact_pii, looks_like_email

print("redact_pii(value, keep_last=4) vs DLP characterMask")
print()
print(f"{'value':<28} {'redact_pii':<28} {'dlp chars_to_mask':>18} {'dlp chars_to_skip':>18}")
for value in ["alice@example.com", "555-123-4567", "4111111111111111", "e00000001"]:
    masked = redact_pii(value, keep_last=4)
    # DLP masks N characters from the start, skipping the first M.
    chars_to_mask = max(0, len(value) - 4)
    chars_to_skip = min(len(value), 4)
    print(f"{value:<28} {masked:<28} {chars_to_mask:>18} {chars_to_skip:>18}")
print()

# The difference is WHERE the mask is applied.
print("redact_pii masks the TAIL, keeping the last 4 visible.")
print("DLP characterMask masks the HEAD, keeping the last N visible by")
print("setting charactersToMask = len - N and charactersToSkip = 0.")
print("Both preserve the length. That is the property that matters for")
print("format validation downstream.")
print()

sample = "alice@example.com"
masked_head = "*" * (len(sample) - 4) + sample[-4:]
print(f"input          : {sample}")
print(f"redact_pii     : {redact_pii(sample)}")
print(f"dlp charMask   : {masked_head}")
print()
print(f"same length preserved: {len(sample) == len(redact_pii(sample)) == len(masked_head)}")
```

Expected output:

```text
redact_pii(value, keep_last=4) vs DLP characterMask

value                        redact_pii                    dlp chars_to_mask  dlp chars_to_skip
alice@example.com            *************.com                            13                  4
555-123-4567                 ********4567                                  8                  4
4111111111111111             ************1111                             12                  4
e00000001                    *****0001                                     5                  4

redact_pii masks the TAIL, keeping the last 4 visible.
DLP characterMask masks the HEAD, keeping the last N visible by
setting charactersToMask = len - N and charactersToSkip = 0.
Both preserve the length. That is the property that matters for
format validation downstream.

input          : alice@example.com
redact_pii     : *************.com
dlp charMask   : *************.com

same length preserved: True
```

### Lab 5 — Building an inspect/de-identify template

```python
import json
from typing import Any


def build_deidentify_template(
    *,
    minimum_likelihood: str = "LIKELY",
    content_found: str = "CRYPTO_REPLACE",
) -> dict[str, Any]:
    """Build a de-identify template.

    The two rules that matter:
      1. deidentifyContentFound = CRYPTO_REPLACE, never REDACT.
      2. Every InfoType in `config` has a matching transformation.
    """
    info_types = ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SOCIAL_SECURITY_NUMBER"]
    transformations = {
        "EMAIL_ADDRESS": {"replace_with_value": {"value": "[EMAIL]"}},
        "PHONE_NUMBER": {
            "character_mask": {
                "masking_character": "*",
                "characters_to_mask": 4,
                "characters_to_skip": 3,
                "reverse_order": False,
            }
        },
        "US_SOCIAL_SECURITY_NUMBER": {"replace_with_value": {"value": "[SSN]"}},
    }
    return {
        "deidentifyConfig": {
            "infoTypeTransformations": [
                {"infoType": name, "primitiveTransformation": transformations[name]}
                for name in info_types
            ],
            "deidentifyContentFound": content_found,
        },
        "config": {
            "infoTypes": [
                {"infoType": name, "minimumLikelihood": minimum_likelihood}
                for name in info_types
            ]
        },
    }


template = build_deidentify_template()
print(json.dumps(template, indent=2))
print()

# The safety check: every configured InfoType must have a rule, and
# content_found must be CRYPTO_REPLACE.
def audit_template(template: dict[str, Any]) -> list[str]:
    problems = []
    config = template.get("config", {})
    deid = template.get("deidentifyConfig", {})
    configured = {i["infoType"] for i in config.get("infoTypes", [])}
    ruled = {t["infoType"] for t in deid.get("infoTypeTransformations", [])}
    for missing in sorted(configured - ruled):
        problems.append(f"{missing}: configured but has no transformation rule")
    for extra in sorted(ruled - configured):
        problems.append(f"{extra}: has a rule but is not configured (never fires)")
    if deid.get("deidentifyContentFound") != "CRYPTO_REPLACE":
        problems.append(
            "deidentifyContentFound is not CRYPTO_REPLACE: a found value "
            "with no rule would pass through unmodified"
        )
    return problems


problems = audit_template(template)
print("template audit:")
if problems:
    for p in problems:
        print(f"  [FAIL] {p}")
else:
    print("  [PASS] every configured InfoType has a rule")
    print("  [PASS] content_found = CRYPTO_REPLACE")

print()
print("Now audit a deliberately broken template:")
broken = build_deidentify_template(content_found="REDACT")
broken["deidentifyConfig"]["infoTypeTransformations"] = broken[
    "deidentifyConfig"
]["infoTypeTransformations"][:1]   # drop the other two rules

for p in audit_template(broken):
    print(f"  [FAIL] {p}")
```

Expected output:

```text
{
  "deidentifyConfig": {
    "infoTypeTransformations": [
      {
        "infoType": "EMAIL_ADDRESS",
        "primitiveTransformation": {
          "replace_with_value": {
            "value": "[EMAIL]"
          }
        }
      },
      {
        "infoType": "PHONE_NUMBER",
        "primitiveTransformation": {
          "character_mask": {
            "masking_character": "*",
            "characters_to_mask": 4,
            "characters_to_skip": 3,
            "reverse_order": false
          }
        }
      },
      {
        "infoType": "US_SOCIAL_SECURITY_NUMBER",
        "primitiveTransformation": {
          "replace_with_value": {
            "value": "[SSN]"
          }
        }
      }
    ],
    "deidentifyContentFound": "CRYPTO_REPLACE"
  },
  "config": {
    "infoTypes": [
      { "infoType": "EMAIL_ADDRESS", "minimumLikelihood": "LIKELY" },
      { "infoType": "PHONE_NUMBER", "minimumLikelihood": "LIKELY" },
      { "infoType": "US_SOCIAL_SECURITY_NUMBER", "minimumLikelihood": "LIKELY" }
    ]
  }
}

template audit:
  [PASS] every configured InfoType has a rule
  [PASS] content_found = CRYPTO_REPLACE

Now audit a deliberately broken template:
  [FAIL] PHONE_NUMBER: configured but has no transformation rule
  [FAIL] US_SOCIAL_SECURITY_NUMBER: configured but has no transformation rule
  [FAIL] deidentifyContentFound is not CRYPTO_REPLACE: a found value with no rule would pass through unmodified
```

The broken-template audit is the point of the lab. A template with `REDACT` and missing rules would pass a naive syntax check and silently leak social security numbers.

### Lab 6 — The "Zip" false positive, concretely

```python
import re

# A naive postal code InfoType: the literal token "Zip".
NAIVE_ZIP = re.compile(r"(?i)\bzip\b")
STREET_ZIP = re.compile(r"\b\d{5}(?:-\d{4})?\b")

TICKETS = [
    "Customer asked about changing the compression Zip level on their order.",
    "Please send the invoice to 90210 Zip.",
    "The zip archive of the dataset is corrupt.",
    "Ship to 10001 Zip with signature required.",
    "Increase the Zip ratio to 9 and re-upload.",
]

print("Two detectors on five free-text records")
print(f"{'record':<62} {'naive Zip':>10} {'digits':>8}")
print("-" * 84)
for ticket in TICKETS:
    naive = bool(NAIVE_ZIP.search(ticket))
    digits = STREET_ZIP.findall(ticket)
    print(f"{ticket[:60]:<62} {str(naive):>10} {str(digits):>8}")
print()

# The context rules that fix it. In DLP these are `boostedLikelihood`
# and `redactedLikelihood` on a custom InfoType.
BOOST = re.compile(r"(?i)\b(zip|postal)\s*code\b")
REDACT = re.compile(
    r"(?i)\b(compression|level|ratio|archive|file|folder|unzip|extract)\b"
)


def contextual_zip(ticket: str) -> str:
    """The custom InfoType logic: boost near 'zip code', redact near noise."""
    if not STREET_ZIP.search(ticket) and not NAIVE_ZIP.search(ticket):
        return "no match"
    if BOOST.search(ticket):
        return "VERY_LIKELY (boosted)"
    if REDACT.search(ticket):
        return "VERY_UNLIKELY (redacted)"
    return "POSSIBLE"


print("With context rules applied:")
for ticket in TICKETS:
    print(f"  {contextual_zip(ticket):<24} {ticket[:56]}")
print()
print("Record 1 and 3 are false positives without the redacted rule.")
print("Record 5 is a bare number with no postal context — POSSIBLE at best.")
print("A threshold of LIKELY drops records 1, 3 and 5 from the findings.")
```

Expected output:

```text
Two detectors on five free-text records
record                                                          naive Zip   digits
------------------------------------------------------------------------------------
Customer asked about changing the compression Zip level on t         True       []
Please send the invoice to 90210 Zip.                                True ['90210']
The zip archive of the dataset is corrupt.                           True       []
Ship to 10001 Zip with signature required.                           True ['10001']
Increase the Zip ratio to 9 and re-upload.                           True       []

With context rules applied:
  VERY_UNLIKELY (redacted) Customer asked about changing the compression Zip level
  POSSIBLE                 Please send the invoice to 90210 Zip.
  VERY_UNLIKELY (redacted) The zip archive of the dataset is corrupt.
  POSSIBLE                 Ship to 10001 Zip with signature required.
  VERY_UNLIKELY (redacted) Increase the Zip ratio to 9 and re-upload.

Record 1 and 3 are false positives without the redacted rule.
Record 5 is a bare number with no postal context — POSSIBLE at best.
A threshold of LIKELY drops records 1, 3 and 5 from the findings.
```

### Lab 7 — Findings are values in context

```python
import sys
sys.path.insert(0, "project/core")

from dataclasses import dataclass


@dataclass
class Finding:
    """A DLP finding: a sensitive value, in a context, with a confidence."""

    info_type: str
    likelihood: str
    byte_offset: int
    byte_length: int
    unicode_substring: str
    is_redact_finding: bool = False


RECORD = "Contact alice@example.com or call 555-123-4567 ext. 89, order 12345."

# DLP reports byte offsets. In UTF-8, one character can be many bytes.
raw = RECORD.encode("utf-8")
print(f"record: {RECORD}")
print(f"length: {len(RECORD)} characters, {len(raw)} bytes")
print()


def span_of(value: str, substring: str) -> tuple[int, int]:
    """Return the (byte_offset, byte_length) of a substring, as DLP reports it."""
    index = RECORD.index(substring)
    start = len(RECORD[:index].encode("utf-8"))
    return start, len(substring.encode("utf-8"))


# Simulate three findings on the same record, using real offsets.
findings = [
    Finding("EMAIL_ADDRESS", "VERY_LIKELY", *span_of(RECORD, "alice@example.com"),
            "alice@example.com"),
    Finding("PHONE_NUMBER", "LIKELY", *span_of(RECORD, "555-123-4567"),
            "555-123-4567"),
    Finding("ORDER_ID", "POSSIBLE", *span_of(RECORD, "12345"), "12345"),
]

for finding in findings:
    # The correct extraction uses BYTE offsets.
    extracted_bytes = raw[finding.byte_offset:finding.byte_offset + finding.byte_length]
    extracted = extracted_bytes.decode("utf-8", errors="replace")
    match = extracted == finding.unicode_substring
    print(f"{finding.info_type:<16} {finding.likelihood:<12} "
          f"bytes[{finding.byte_offset}:{finding.byte_offset + finding.byte_length}] "
          f"-> {extracted!r}  {'OK' if match else 'MISMATCH'}")
print()

# Overlap detection.
print("Span overlap analysis:")
for i, a in enumerate(findings):
    a_start, a_end = a.byte_offset, a.byte_offset + a.byte_length
    for b in findings[i + 1:]:
        b_start, b_end = b.byte_offset, b.byte_offset + b.byte_length
        if a_start < b_end and b_start < a_end:
            print(f"  OVERLAP: {a.info_type} [{a_start},{a_end}) vs "
                  f"{b.info_type} [{b_start},{b_end})")
print("(no overlaps here — the three spans are disjoint)")
print()

# Now the UTF-8 bug: a character index is not a byte index.
MULTIBYTE = "Café ☕ order 12345"
raw_mb = MULTIBYTE.encode("utf-8")
index = MULTIBYTE.index("12345")
char_start = index
byte_start = len(MULTIBYTE[:index].encode("utf-8"))
print(f"record: {MULTIBYTE}")
print(f"length: {len(MULTIBYTE)} characters, {len(raw_mb)} bytes")
print()
print(f"  character index of '12345' : {char_start}")
print(f"  byte offset of '12345'      : {byte_start}")
print(f"  difference                 : {byte_start - char_start} bytes")
print()
print("The character index is NOT the byte offset. Decoding the raw bytes")
print("at the CHARACTER index gives the wrong text:")
wrong = raw_mb[char_start:char_start + 5].decode("utf-8", errors="replace")
right = raw_mb[byte_start:byte_start + 5].decode("utf-8")
print(f"  raw[char_start:char_start+5] -> {wrong!r}")
print(f"  raw[byte_start:byte_start+5] -> {right!r}")
print(f"  correct: {wrong == right}")
print()
print("This is why you must decode by byte offset, or use unicodeSubstring.")

# The contrast with the pipeline: reason codes, not a boolean.
from pipeline_logic import ingest_events, reject_counts

bad = ingest_events(open("sample_data/malformed_events.csv").read().splitlines())[1]
print("Contrast — the pipeline's per-row classification:")
for reason, count in sorted(reject_counts(bad).items()):
    print(f"  {reason:<22} {count}")
print()
print("DLP: a boolean per InfoType, per content.")
print("Pipeline: a reason code per row, with a dead-letter path.")
```

Expected output:

```text
record: Contact alice@example.com or call 555-123-4567 ext. 89, order 12345.
length: 68 characters, 68 bytes

EMAIL_ADDRESS    VERY_LIKELY  bytes[8:25] -> 'alice@example.com'  OK
PHONE_NUMBER     LIKELY       bytes[34:46] -> '555-123-4567'  OK
ORDER_ID         POSSIBLE     bytes[62:67] -> '12345'  OK

Span overlap analysis:
(no overlaps here — the three spans are disjoint)

record: Café ☕ order 12345
length: 18 characters, 21 bytes

  character index of '12345' : 13
  byte offset of '12345'      : 16
  difference                 : 3 bytes

The character index is NOT the byte offset. Decoding the raw bytes
at the CHARACTER index gives the wrong text:
  raw[char_start:char_start+5] -> 'er 12'
  raw[byte_start:byte_start+5] -> '12345'
  correct: False

This is why you must decode by byte offset, or use unicodeSubstring.
Contrast — the pipeline's per-row classification:
  bad_amount             1
  bad_timestamp          1
  missing_event_id       1
  missing_user_id        1
  negative_amount       1
  unknown_channel        1
  unknown_currency       1
  unknown_event_type     1
  unknown_region         2
  wrong_field_count      2

DLP: a boolean per InfoType, per content.
Pipeline: a reason code per row, with a dead-letter path.
```

---

## 🛠️ Common Errors and Fixes

### 1. `400 Bad Request` — the de-identify template is invalid

```text
INVALID_ARGUMENT: De-identify template is invalid: the de-identify
config must not contain both a primitiveTransformation and a
primitiveTransformation in the same infoTypeTransformation.
```

**Cause:** a malformed template. The most common causes are: a `config.infoTypes` entry with no matching `infoTypeTransformations` entry, a transformation with two primitive transformations set, or a `deidentifyContentFound` value that is not a valid enum.

**Fix:** validate the template before deploying it. The `audit_template` function from Lab 5 catches this class of error locally.

```bash
# List the templates that exist
gcloud sensitive-data-protection templates list \
  --project=my-project --location=us-central1

# Delete and recreate after fixing
gcloud sensitive-data-protection templates delete my-template \
  --project=my-project --location=us-central1 --force
```

### 2. `INVALID_ARGUMENT: Unsupported finding type`

```text
INVALID_ARGUMENT: Unsupported finding type: PHONE_NUMBER_5
```

**Cause:** the InfoType name does not exist. This happens when a template is written against a catalogue of custom InfoTypes that were deleted, or when a name is mistyped, or when an InfoType was renamed. It is also common when copying a template between projects, because custom InfoTypes are project-scoped and do not travel.

**Fix:** list the valid names and use them exactly. Custom InfoTypes must be recreated in the destination project before the template that references them.

```bash
gcloud sensitive-data-protection info-types list \
  --project=my-project --location=us-central1 \
  --filter="name:EMAIL_ADDRESS OR name:PHONE_NUMBER OR name:custom"
```

### 3. `403 Quota exceeded` — the inspect job exceeds the DLP quota

```text
RESOURCE_EXHAUSTED: Quota exceeded for quota metric 'Inspect data
bytes' and limit 'Inspect data bytes per minute' of service
'sensitivedata.googleapis.com'.
```

**Cause:** a bucket scan job submitted a large batch of parallel inspection calls. The DLP API has per-minute byte quotas, and a scan of a large bucket with many small files will hit them.

**Fix:** reduce the concurrency of the scan. For Cloud Storage scan jobs, narrow the file predicate; for API calls, throttle client-side with exponential backoff.

```bash
# Narrow the scan to one prefix rather than the whole bucket
gcloud sensitive-data-protection jobs create \
  --project=my-project --location=us-central1 \
  --output-config="gs://reports/dlp-out/" \
  --scan-config="gs://data-bucket/daily/" \
  --inspect-config=inspect-template=my-inspect-template
```

### 4. `PERMISSION_DENIED` — the service account cannot create a job

```text
PERMISSION_DENIED: Permission 'sensitivedata.googleapis.com.jobs.create'
denied on resource 'projects/my-project/locations/us-central1'.
```

**Cause:** the principal running the job lacks the DLP roles. The roles are split: `roles/dlp.user` (run jobs), `roles/dlp.deidentifier` (inspect and de-identify content), and `roles/dlp.cryptorekeyAdmin` (use CMEK for cryptonyms).

**Fix:** grant the right role for what the job does.

```bash
gcloud projects add-iam-policy-binding my-project \
  --member=serviceAccount:dlp-runner@my-project.iam.gserviceaccount.com \
  --role=roles/dlp.user

gcloud projects add-iam-policy-binding my-project \
  --member=serviceAccount:dlp-runner@my-project.iam.gserviceaccount.com \
  --role=roles/dlp.deidentifier
```

### 5. `400 Bad Request` — `cryptonym` fails with "key version does not exist"

```text
INVALID_ARGUMENT: Crypto key version projects/my-project/locations/
us-central1/keyRings/dlp/cryptoKeys/deid/cryptoKeyVersions/1 does not
exist or is not enabled.
```

**Cause:** the `cryptonym` transformation references a KMS CryptoKeyVersion that does not exist, is disabled, or is in a different project. The version id must be the **numeric version**, not the key name.

**Fix:** create and enable the key version, then reference the exact numeric version.

```bash
gcloud kms keys versions create \
  --location=us-central1 --keyring=dlp --key=deid \
  --project=my-project

gcloud kms keys versions list \
  --location=us-central1 --keyring=dlp --key=deid --project=my-project
```

### 6. The de-identified output is missing a column you did not configure

```text
# Symptom: a field is entirely "[REDACTED]" and you have no rule for it.
```

**Cause:** a **redact finding**. A larger matched span covered it — for example, a `PHONE_NUMBER` match that spanned a wider region than you expected swallowed the neighbouring field.

**Fix:** inspect first with `InspectContent` and look at the byte offsets. The fix is to narrow the detection (a custom InfoType with a tighter regex) or to lower the minimum likelihood for the offending InfoType.

```text
# Inspect, do not guess. The findings report shows where each span is.
EMAIL_ADDRESS          offset=7    len=17    likelihood=VERY_LIKELY
PHONE_NUMBER           offset=26   len=18    likelihood=LIKELY
POSTAL_CODE            offset=50   len=5     likelihood=POSSIBLE
```

The offsets tell you which span swallowed which. Compare the byte length against the length of the value you expected — a `len` much larger than your field means the match over-reached.

### 7. `L` mode finds nothing in a CSV where every row is an email address

```text
# Symptom: a CSV with a dedicated `email` column produces zero findings
# in `L` mode, but plenty in `L`-basic.
```

**Cause:** in `L` mode the detector relies on surrounding context, and a bare cell with no surrounding words gives it no evidence — so confidence stays low and the finding falls below the threshold.

**Fix:** for structured data, use `L`-basic (the default). Reserve `L` mode for free text where the context is what disambiguates the value.

```json
{
  "infoTypes": [
    { "infoType": "EMAIL_ADDRESS", "minimumLikelihood": "LIKELY" }
  ]
}
```

### 8. The scan job "succeeds" but reports no findings on data you know contains emails

**Cause:** usually the **file predicate** excluded the files. The scan config's `fileSet` can filter by file type, and a bucket of `.dat` or `.txt` files will be skipped entirely by a predicate that allows only CSV and JSON.

**Fix:** check the job's `stats` and the findings report, and widen the file predicate to `FILE_TYPE_UNSPECIFIED` while you diagnose.

```bash
gcloud sensitive-data-protection jobs describe <JOB_ID> \
  --project=my-project --location=us-central1 \
  --format="value(stats)"
```

---

## 💡 Production Notes

- **Always set `deidentifyContentFound` to `CRYPTO_REPLACE`.** It is the guarantee that nothing found passes through untouched. `REDACT` silently leaks every value you forgot to write a rule for.

- **Write a template audit into your CI.** For every configured InfoType there must be a transformation, and `content_found` must be `CRYPTO_REPLACE`. The `audit_template` function in Lab 5 is twenty lines and catches the most common catastrophic misconfiguration.

- **Inspect before you de-identify.** A de-identify run tells you what it changed. An inspect run tells you what is *there*, with offsets and likelihoods. Always inspect first — it is cheaper to iterate on detection than to re-process a warehouse of already-redacted data.

- **Tune with real findings, not with intuition.** Run the inspect job against a representative sample, look at the findings, and adjust the minimum likelihood per InfoType. Raising the threshold globally to fix one false positive hides real findings elsewhere.

- **Use `L` mode for free text and `L`-basic for structured data.** In `L` mode a bare value with no surrounding context can be down-weighted below threshold. On a CSV with a dedicated email column that means zero findings.

- **Use the boost and redact context rules aggressively.** They are the difference between a detector that is usable in production and one that flags the word "Zip" in "compression Zip level". Every custom InfoType for free text should have both lists.

- **Anchor custom InfoType regexes with `\b` and validate them with a checksum.** A raw `\d{5}` matches the first five digits of a 16-digit card number. The built-in detectors handle this; yours must too.

- **Remember the byte-offset gotcha.** Findings report `byteOffset` and `byteLength` in **bytes**. With UTF-8, a character can be 2 or 4 bytes. Use the provided `unicodeSubstring` or decode by byte offset — a character index will extract the wrong text.

- **Scope scans to what changed.** A nightly full-bucket scan of 500 GB is $150 a month for findings you already had. Use object prefixes, file modification filters, or a manifest of new files.

- **De-identifying a copy does not remove the original.** The source bucket still holds the sensitive data, still bills, and is still in scope for every audit. If the goal is not to have the data, delete the original — deliberately, and after verifying the de-identified copy is complete.

- **Prefer `cryptonym` over a plain hash for pseudonymous identifiers.** A keyed hash of a low-entropy value (a 4-digit PIN, a short account number) is brute-forceable. FPE-based cryptonyms preserve format without shrinking the search space.

- **DLP is not a validator.** It finds values that look sensitive; it does not enforce business rules. The course pipeline's ten reason codes — `unknown_currency`, `negative_amount`, `bad_timestamp` — are a validation problem, not a DLP problem. Keep the two concerns separate.

---

## 🔑 Key Takeaways

- **DLP works on findings, not on values.** A finding is a sensitive value *in a context* that matched an InfoType's pattern and passed its likelihood threshold. The same string can be a finding or not.
- **InfoTypes are the detectors.** Over 200 built-ins, plus custom regex InfoTypes and stored InfoTypes (dictionaries) for your own identifiers.
- **Likelihood scoring decides what counts.** `VERY_UNLIKELY` through `VERY_LIKELY`, with a per-InfoType `minimumLikelihood` threshold on the template. Raising it reduces false positives and increases false negatives.
- **`L` mode adds contextual analysis; `L`-basic does not.** Use `L` mode for free text. For structured data it can *lose* real findings, because a bare cell gives the detector no evidence.
- **A de-identify template has two halves**: `config` (what to detect) and `deidentifyConfig` (what to do about it). `deidentifyContentFound: CRYPTO_REPLACE` is the safety net — never use `REDACT`.
- **The methods trade reversibility against utility**: masking (no utility), character masking (format), tokenization and cryptonyms (deterministic joins), FPE (reversible), hashing (joins, brute-forceable at low entropy), date shifting (preserves intervals).
- **`cryptonym` is the modern answer to "group by an identifier without exposing it"** — deterministic, KMS-backed, and not brute-forceable.
- **Findings report byte offsets, not character offsets.** In UTF-8 they differ. Use `unicodeSubstring`.
- **A redact finding is a value removed as a side effect of an overlapping span.** It is the usual explanation for a field you did not configure going missing.
- **The overlap problem is real**: spans nest, and the resolution depends on the template. Compare input length, output length, and finding count when validating a de-identification pipeline.
- **The "Zip" false positive is solved with context rules**: `boostedLikelihood` near "zip code", `redactedLikelihood` near "compression", "level", "ratio".
- **Inspection costs $0.10/GB regardless of what is found.** A 1 TB scan is $102.40 whether it finds 12 emails or 12 million.
- **DLP finds sensitive data; it does not validate business rules.** Reason codes like `unknown_currency` are a validator's job, not DLP's.

---

## 📚 Practice Exercises

1. **Template design.** Write a complete de-identify template for the course pipeline's event records, covering `EMAIL_ADDRESS`, `PHONE_NUMBER`, and a custom `CUSTOMER_ID` InfoType. For each, choose the transformation and justify it in terms of reversibility, utility, and re-identification risk. Then write the `audit_template` check and confirm your template passes it.

2. **The "Zip" problem, solved.** Using the ticket examples from Lab 6, build a custom `US_POSTAL_CODE_CUSTOM` InfoType with both a `boostedLikelihood` and a `redactedLikelihood` context list. Show the finding count and likelihood for each ticket at `minimumLikelihood` of `POSSIBLE`, `LIKELY`, and `VERY_LIKELY`, and explain which threshold you would ship.

3. **Regex versus detector.** Using `looks_like_email` from `project/core/pipeline_logic.py`, find every input in a test corpus of 20 strings that it classifies differently from a DLP-style detector. For each disagreement, state which is correct, and explain whether DLP's answer comes from a pattern, a validation rule (Luhn, length), or context.

4. **Masking comparison.** Implement all seven DLP transformations — masking, character masking, tokenization (FPE), hashing (keyed), FPE-with-KMS, replacement (`redact` / `cryptonym` / `redact-deterministic`), and date shifting — in pure Python. For each, apply it to the same `event_id` and `user_id` values and tabulate: reversible, format-preserving, groupable, and brute-forceable. Then state which one you would use for each column of the events table, and why.

5. **Findings versus reason codes.** For the malformed dataset, construct an inspection of a synthetic record containing all ten of the `EXPECTED_REJECT_COUNTS` conditions. For each condition, state whether DLP would find it (it is a sensitive-data problem), whether a validator would find it (it is a business-rule problem), or both. Then argue why running DLP *and* a validator is not redundant.

6. **Cost model.** Use `estimate("sensitive-data-protection", inspected_gb=...)` from `project/core/cost_model.py` to model: (a) a one-off audit of a 2 TB bucket; (b) a nightly scan of a 200 GB bucket for a year; (c) a full de-identification of a 50 TB lakehouse. Then propose a scanning strategy that reduces (b) by 90% while preserving detection coverage, and compute the saving.

7. **UTF-8 offsets.** Construct a record containing multi-byte characters (accented Latin, an emoji, a CJK character) adjacent to a phone number and an email. Demonstrate the bug of extracting by character index instead of byte offset, show the correct extraction, and write the function you would use in production.

8. **Migration plan.** Design the DLP rollout for an existing analytics platform: the discovery phase (where do you inspect first?), the template design phase, the enforcement phase, and the monitoring phase. For each, name the specific artefact produced, the specific tool used, and the specific check that tells you the phase is done.

---

## 📖 Further Reading

- [Sensitive Data Protection Documentation](https://docs.cloud.google.com/sensitive-data-protection/docs)
- [DLP — InfoTypes and Likelihood](https://docs.cloud.google.com/sensitive-data-protection/docs/infotypes-reference)
- [DLP — Creating Custom InfoTypes](https://docs.cloud.google.com/sensitive-data-protection/docs/custom-infotypes)
- [DLP — De-identification Transformations](https://docs.cloud.google.com/sensitive-data-protection/docs/transformations-reference)
- [DLP — Templates Overview](https://docs.cloud.google.com/sensitive-data-protection/docs/templates-overview)
- [DLP — Inspecting and De-identifying Content](https://docs.cloud.google.com/sensitive-data-protection/docs/inspecting-and-deidentifying-text)
- [DLP — Pricing](https://cloud.google.com/sensitive-data-protection/pricing)
