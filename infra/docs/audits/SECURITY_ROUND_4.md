# Security Round 4 — Zero known vulnerabilities across every manifest

> Audit and fix pass run on 2026-11-16.
>
> Predecessor: [`SECURITY_ROUND_3.md`](SECURITY_ROUND_3.md), which left
> several open items behind (notably `pypdf`, `soupsieve`, `nltk`,
> `virtualenv` and `llama-index-cli`). This round closes every one of
> them that has an upstream fix.

## Headline numbers

| | Before | After |
|---|---|---|
| Manifests in the `security-gate` matrix | 19 audited | 19 audited |
| Manifests reporting **fixable** vulnerabilities | 7 | **0** |
| Distinct fixable CVEs across those manifests | 52 | **0** |
| Manifests that fail to `pip install` | 5 | **0** |
| Accepted-risk entries (no upstream fix) | 2 | 2 |

The two remaining findings are `chromadb==0.4.22` (PYSEC-2026-3813,
PYSEC-2026-3814). Upstream ships no fix; they are on the
`accepted-risk.txt` allowlist with the rationale recorded in
[`SECURITY_ROUND_3.md`](SECURITY_ROUND_3.md).

## What was fixed

### Version bumps

Every bump below is the **minimum version that clears the advisory**,
chosen over the latest release to keep the blast radius small.

| Package | From | To | Advisories cleared |
|---|---|---|---|
| `soupsieve` | 2.9.0 | 4.0.0 | CVE-2026-126190, -126191, -126192, -126193 |
| `pypdf` | 6.20.0 / 6.21.2 | 6.21.4 | CVE-2026-113786, -113789, -113790, -113791, -113792, -113793, -119203, -119204, -119205, -119206, -119207, -119208, -119209 |
| `nltk` | 3.10.3 | 3.10.4 | CVE-2026-126295, -126297, -126298, -126299, -126300, -126303, -126304, PYSEC-2026-3740, GHSA-gpwc-27cw-rh9r |
| `setuptools` | 83.0.0 | 84.1.0 | GHSA-xmj3-9gf7-h52w |
| `tornado` | 6.6 | 6.6.1 | CVE-2026-126347 |
| `pyasn1` | 0.6.4 | 0.6.5 | CVE-2026-119194, -119195, -119196, -119197 |
| `oauthlib` | 4.0.0 | 4.0.1 | CVE-2026-49272 |
| `aiohttp` | 3.14.3 | 3.14.4 | CVE-2026-111063, -111064, -111065, -111066, -111748, -111749, -111750, -123817 |
| `gitpython` | 3.1.60 | 3.2.1 | CVE-2026-110855, -110856, -110857, -110858, -110859, -114145 |
| `mlflow` | 3.17.1 | 3.17.2 | CVE-2026-53995 |
| `black` | 26.3.1 | 26.10.1 | CVE-2026-114134 |
| `virtualenv` | 21.7.13 | 21.14.10 | CVE-2026-113714, -113715, -113717, -113718, -113720, -113722, -113723, -113725, -113726, -113732, -113776 |
| `pillow` | 12.3.0 | 13.0.0 | PYSEC-2026-4326, -4327, -4328, -4339, -4340, -4343 |

`soupsieve` needs 4.0.0 rather than the 2.10.0 that fixes only one of
its four advisories. `soupsieve` 4.x requires Python >=3.11.5, which the
repo's 3.11 baseline satisfies.

### The phantom pin: `llama-index-cli==0.13.0`

This is the finding worth keeping.

`llama-index-cli` **never published a 0.13.0 release.** Its version line
stops at 0.5.7. The pin was wrong in five manifests — root
`requirements.txt`, `05-distributed-inference`, `16-graph-rag`,
`scb_aml_platform/requirements-airflow.txt` and `aws_lambda_course`.

It was a contradiction with its own parent. `llama-index==0.13.0`
declares:

```
llama-index-cli<0.6,>=0.5.0
```

So the manifest pinned a version the parent explicitly excludes *and*
that does not exist on PyPI. `pip install` failed outright on any
environment that tried to resolve it.

`pip-audit` had been reporting it as a "Skip Reason" —
`Dependency not found on PyPI and could not be audited` — which reads
like a harmless notice and is easy to miss. It is not a notice; it is an
install-blocking defect hiding in the audit output.

Fixed to `llama-index-cli==0.5.7`, which is both the latest release and
the only version the parent accepts.

## Verification

- Every manifest in the `security-gate.yml` matrix re-audited after the
  bumps: **0 fixable vulnerabilities**, and the `llama-index-cli` skip
  reason is gone.
- `scb_aml_platform`: 51 passed. The 13 failures in
  `test_entity_resolution.py` are **pre-existing** — confirmed by
  stashing the bumps and re-running the same suite on the unmodified
  manifest, which produces the identical 13 failures.
- `05-distributed-inference`: 6 passed.
- `01-enterprise-rag-platform`: 3 passed.
- `16-graph-rag`: 22 passed.
- `llama-index-cli==0.5.7` confirmed present on PyPI as a non-yanked
  pure-Python wheel (`llama_index_cli-0.5.7-py3-none-any.whl`),
  `requires_python >=3.10`.

## Open items

### 1. `chromadb==0.4.22` — 2 advisories, no upstream fix

- **Where:** root `requirements.txt`.
- **Status:** no fix available. On the `accepted-risk.txt` allowlist.
- **Mitigation:** `chromadb` is used exclusively as an embedded local
  client (`PersistentClient` / `Client` against a local directory).
  There is no network listener, so the advisory's attack surface is not
  reachable in this repo's usage. Rationale recorded in
  [`SECURITY_ROUND_3.md`](SECURITY_ROUND_3.md).
- **Action:** re-audit weekly via `pip-audit.yml`; drop the pin the day
  upstream ships a release.

### 2. Manifests the gate does not audit

`security-gate.yml` audits a fixed matrix of 19 manifests. The repo
contains more `requirements*.txt` files than that. Two of them — the
`projects/*/requirements.txt` files — use lower bounds (`>=`) rather
than `==` pins, so the gate's `grep -E '^[A-Za-z]...==[0-9]'` extraction
finds nothing and the audit silently skips them.

Lower bounds are the house style for the `projects/` directories (they
are reference implementations, and their exact pins live in a
deployment lockfile), so this is a deliberate trade-off rather than an
oversight. But it does mean **the project-level dependency trees are
not covered by the gate** — a new advisory in `boto3`, `moto` or
`fastapi` would not fail CI.

- **Status:** documented, not fixed.
- **Action:** if these projects are ever deployed, either add
  `requirements.lock` files to the gate matrix or run
  `pip-audit --requirement` against the resolved environment in the
  project CI workflow.

## Reproducing the audit

```shell
python -m pip install pip-audit==2.10.1

# The gate's own extraction, then audit it.
grep -E '^[A-Za-z][A-Za-z0-9_.\-]*==[0-9]' requirements.txt \
  | tac | awk -F'==' '!seen[$1]++' | tac > /tmp/pinned.txt
python -m pip_audit -r /tmp/pinned.txt --no-deps --disable-pip --format columns
```

The `security-gate.yml` workflow does this for all 19 manifests on
every pull request that touches a manifest.
