# Lesson 03 — Sandbox Hardening (gVisor)

> **A subprocess sandbox is sufficient when the threat is "the LLM emits bad code." A gVisor sandbox is necessary when the threat is "an untrusted user uploads code."**

## 🎯 Outcome

By the end of this lesson you can:

1. Explain why subprocess + rlimit handles 99% of CVEs, and which 1% it doesn't.
2. Run a code execution inside a gVisor sandbox using `docker --runtime=runsc`.
3. Decide when gVisor is overkill (subprocess is fine) vs. necessary (multi-tenant with untrusted users).

## 🧠 Mindset

The Phase 4 sandbox (`subprocess.py`) is a subprocess with `resource.setrlimit` for memory + CPU + a 5s wall-clock timeout. **At 50 questions/day from 1 tenant, this is sufficient.** The threat model is "the LLM emits code that the customer doesn't realize is dangerous." The LLM is bounded by its training distribution; it can't emit a novel kernel exploit.

Phase 5 changes two things:

1. **Volume** (50 → 500 questions/day × 12 tenants = 6,000 executions/day). A 1-in-10,000 CVE becomes a 60% probability of one event per day.
2. **Threat model**: now **multi-tenant** with **untrusted users** (the e-commerce platform's CS team uploads customer CSVs as part of the analysis). Subprocess + rlimit doesn't isolate one tenant's data from another tenant's exploit.

The fix: **gVisor** (`runsc`). Google's userspace kernel implementation. Every code execution is a Docker container running under gVisor:

- No host filesystem (only tmpfs at `/workspace`).
- No network (`--network=none`).
- No capabilities (`--cap-drop=ALL`).
- No `/proc`, no `/sys`, no `/dev`.
- Runs as `nobody` (no root).

**Even a kernel CVE in `matplotlib` or `pandas` can't escape.** The cost: ~50ms per execution (vs ~5ms for subprocess). At 6,000 executions/day this is 5 minutes of overhead across all tenants — fine.

## 🛠️ Practice

Open `projects/03-gvisor-sandbox/service/gvisor_runner.py`. The key bits:

1. **`_have_gvisor()`** checks for `runsc` or `docker` on PATH. Falls back to subprocess if neither is installed.
2. **`run_code_gvisor()`** runs `docker run --runtime=runsc ... python user_code.py`.
3. **`_run_subprocess_fallback()`** is the Phase 4 path; keeps working when gVisor isn't installed.

Run the demo (it works either way):

```bash
cd projects/03-gvisor-sandbox
python3 service/gvisor_runner.py
```

Expected: output prints `backend=gvisor` if Docker + gVisor are installed, else `backend=subprocess`.

Then the 2 tests:

```bash
python3 -m pytest phase-5-advanced/projects/03-gvisor-sandbox/tests/test_gvisor.py -v
```

Expected: **2 passed.**

## 🏛️ FDE Lens — the production reality underneath

| Threat model | Sandbox | Cost |
|---|---|---|
| LLM emits code, 1 tenant | Phase 4 subprocess | 5ms/exec |
| LLM emits code, 12 tenants | Phase 5 subprocess | 5ms/exec (still safe — LLM can't bypass rlimit) |
| Untrusted user uploads code, 1 tenant | Phase 5 subprocess **with rlimit + chroot** | 10ms/exec |
| Untrusted user uploads code, 12 tenants | **Phase 5 gVisor** | 50ms/exec |

**The escalation:** when the threat model changes, the sandbox changes. Phase 4 was sufficient because the threat was bounded. Phase 5 changes the threat because the deployment is multi-tenant. **The eval set stays the same; the sandbox changes.**

## What's NOT in Phase 5

- **gVisor in Kubernetes (gVisor + kata-containers + firecracker).** These are Phase 6 topics. For 6,000 executions/day on 1 VM, plain Docker + gVisor is sufficient.
- **Verifiable builds (reproducible sandbox).** Out of scope for this lesson.
- **GPU sandboxing for LLM agents.** Different problem; out of scope.

## 🌙 Reflect

1. The Phase 4 sandbox was sufficient for 1 year. **What changed in Phase 5 to make it insufficient?**
2. gVisor is ~50ms per execution. At 6,000 executions/day, that's 5 minutes/day. **When does that overhead become a problem?**
3. A real CVE in `matplotlib` would be patched in 24h. **What's the window of exposure for a multi-tenant sandbox without gVisor?**
