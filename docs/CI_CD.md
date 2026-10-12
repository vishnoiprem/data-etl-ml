# CI/CD — leads-pipeline

This doc covers the four GitHub Actions workflows and the GHCR
publish that wrap the `leads-pipeline/draft-cron` Python package.

## Workflows at a glance

| Workflow         | File                                    | Triggers                                   | Purpose |
|------------------|-----------------------------------------|--------------------------------------------|---------|
| `leads-ci`       | `.github/workflows/leads-ci.yml`        | push to `main` + 2 active feature branches, PRs to `main` | Run 6 test modules + lint + Dockerfile build (size budget) + advisory grype scan |
| `leads-cd`       | `.github/workflows/leads-cd.yml`        | push to `main`, manual dispatch, dispatch from release-please | Build + push image to `ghcr.io` + verify + SBOM + cosign keyless sign |
| `release-please` | `.github/workflows/release-please.yml`  | push to `main`                             | Open release PR from conventional commits, re-dispatch leads-cd with semver tag |
| `pip-audit`      | `.github/workflows/pip-audit.yml`       | changes to `requirements*.txt`, weekly Mon 06:00 UTC, manual dispatch | Security scan, upload SARIF |
| `codeql`         | `.github/workflows/codeql.yml`          | changes to `leads-pipeline/**`, weekly Mon 06:30 UTC, manual dispatch | CodeQL static analysis on leads-pipeline Python, upload SARIF |

## `leads-ci`

Two jobs:

1. **`test`** — spins up a Postgres 15 service container, runs the
   6 in-repo test modules in order, runs flake8 on the modified
   source files (advisory only — pre-existing warnings surface in
   the UI as a warning, not a hard failure).
2. **`dockerfile-build`** — reads the in-tree
   `leads-pipeline/draft-cron/VERSION` (falling back to
   `0.0.0+<sha>`), builds the Dockerfile in
   `leads-pipeline/draft-cron` (without pushing), smoke-tests the
   resulting image, and enforces a 300 MB size budget. This guards
   the CD workflow: a broken Dockerfile or a 2 GB regression
   can't reach `main` because the PR will fail.

### Trigger branches

`main` plus the two active feature branches
(`feature/agent-coding-11oct`, `feature/auto-pilot-ai-leads-loop`).
To add a branch, edit the `branches:` list in the `on:` block.

### Concurrency

`cancel-in-progress: true` — a force-push cancels the previous
run. Saves runner minutes on rapid iteration.

## `leads-cd`

Three jobs, mostly parallel after `build-and-push`:

1. **`build-and-push`** — uses `docker/build-push-action@v7` with
   the `metadata-action` to compute the tags. Pushes to
   `ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline`. Reads
   `VERSION` and passes it as `--build-arg VERSION=…` so the
   image carries `org.opencontainers.image.version`.
2. **`verify`** (sequential, after `build-and-push`) — re-pulls
   the just-published image and runs three checks: the 300 MB
   size budget, a Python import smoke test (every critical
   module), and a manifest sanity check (entrypoint must be
   `python`). Any failure exits the job before the bad tag is
   left in GHCR.
3. **`sbom`** (parallel with `verify`) — uses
   `anchore/sbom-action@v0` to generate an SPDX 2.3 SBOM from
   the pulled image and uploads it as a workflow artifact
   (`leads-pipeline-sbom`, 30-day retention). The image itself
   is not shipped with an embedded SBOM (faster push, smaller
   layers) — the SBOM is generated downstream per release.

### Image tags

| Push event                | Tags applied                              |
|---------------------------|-------------------------------------------|
| push to `main`            | `latest`, `main-<short_sha>`, `<short_sha>` |
| manual `workflow_dispatch` with `tag_suffix=rc1` | `latest-rc1`, `<short_sha>` |
| dispatched from release-please with `tag_suffix=v1.2.3` | `latest`, `latest-v1.2.3`, `main-<short_sha>`, `<short_sha>` |
| other branch              | `<branch>`, `<short_sha>`                  |

### Concurrency

`cancel-in-progress: false` — an in-flight push runs to completion
because a half-pushed image is worse than a slow one.

### Permissions

- `contents: read` — checkout
- `packages: write` — push to `ghcr.io` (uses the
  `GITHUB_TOKEN` automatically; no extra secrets needed)

### No remote deploy

The image is just published. Pull + run on the target host:

```bash
docker pull ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:latest
docker run --rm \
  -e AVILX_DB_HOST=db.example.com \
  -e AVILX_DB_PORT=5432 \
  -e AVILX_DB_NAME=avilx \
  -e AVILX_DB_USER=avilx \
  -e AVILX_DB_PASSWORD=... \
  -e GMAIL_USER=... \
  -e GMAIL_APP_PASSWORD=... \
  ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:latest
```

To run a different entrypoint (e.g. the dashboard):

```bash
docker run --rm \
  -e AVILX_DB_HOST=... \
  -p 8501:8501 \
  ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:latest \
  dashboard.py
```

Or, using the repo's `docker-compose.yml` (one-shot, behind the
`agent` profile so it doesn't auto-start on a plain `up`):

```bash
docker compose --profile agent run --rm leads-pipeline
# override the image tag:
LEADS_IMAGE=ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:main-abc1234 \
  docker compose --profile agent run --rm leads-pipeline
```

## `release-please`

Runs on every push to `main`. Scans conventional commits since
the last release, computes the next semver, and opens a PR
`chore(release): release X.Y.Z` that:

- Bumps `leads-pipeline/draft-cron/VERSION` to the new semver.
- Updates `.release-please-manifest.json` so the next run picks
  up from the right baseline.
- Regenerates `CHANGELOG.md` from the conventional-commit history.

When the release PR is merged, release-please creates a GitHub
release + git tag, then dispatches `leads-cd` with
`tag_suffix=vX.Y.Z` so the image is republished with a
`latest-vX.Y.Z` tag (in addition to `latest`).

**Bump policy** (see `release-please-config.json`):

- `fix:` → patch bump
- `feat:` → minor bump
- `feat!:` / `BREAKING CHANGE:` footer → major bump
- `chore:`, `docs:`, `refactor:`, `test:`, `ci:`, `build:`, `style:` → no bump

## `pip-audit`

Weekly Monday 06:00 UTC scan of every `requirements*.txt` in the
repo, plus on every change to those files. Uploads a SARIF to
the Code Scanning tab so the security advisories show up inline
on PRs.

## `codeql`

Weekly Monday 06:30 UTC GitHub CodeQL pass over
`leads-pipeline/draft-cron/` (the only project in the repo with
"production-shaped" Python — the rest of the monorepo is
tutorials + reference impls where false positives would just be
distractors). Complements `grype` (which only scans the runtime
deps) by looking at the source itself — SQL injection, unsafe
deserialisation, weak crypto, etc. Triggers on every change to
`leads-pipeline/**` and on a separate weekly schedule. Findings
are uploaded to the Security tab; the build only fails on
warnings or higher.

## Dependabot + Renovate

The repo runs **both** by design:

- **Dependabot** (`.github/dependabot.yml`) — pip + npm +
  github-actions + docker ecosystems, weekly Monday 09:00 IST.
  Has the canonical per-ecosystem config and is what opened the
  original security PRs.
- **Renovate** (`renovate.json5`) — opt-in via the Renovate
  GitHub App. Adds:
  - Automerge for low-risk patch/minor updates in
    `leads-pipeline/draft-cron/requirements.txt`.
  - Automerge for github-actions patch updates.
  - A custom regex manager for inline `pip install foo==X.Y.Z`
    in any `*.py` or `*.sh` (Dependabot can't see these).
  - A "Renovate Dashboard" issue listing all open PRs.

The `CODEOWNERS` file auto-assigns `@vishnoiprem` for review on
CI/CD paths so a fresh commit to the workflow files won't slip
in unreviewed.

## Local reproduction

To reproduce the CI build locally:

```bash
# CI test step
cd leads-pipeline/draft-cron
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt flake8
# (in another terminal: docker compose up -d postgres)
PYTHONPATH=. python -m tests.test_dedup_key   # etc.
make ci          # install + test + lint + docker-build + smoke

# CD build step (the Makefile passes --build-arg VERSION=...)
make docker-build
make docker-run

# Or, on the published image (after a release):
docker pull ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:latest
```

## Adding a new workflow or changing an existing one

1. Edit the YAML under `.github/workflows/`.
2. Validate with `python3 -c "import yaml; yaml.safe_load(open('…'))"`.
3. Open a PR. The README badges update automatically once the
   workflow file exists on `main`.

## Future enhancements (not yet built)

- **Multi-arch build** — add `platforms: linux/amd64,linux/arm64`
  to `docker/build-push-action` when an arm64 target host appears.
- **Remote deploy** — when there's a server to deploy to, add an
  `appleboy/ssh-action` step after the verify job. Needs
  `SSH_HOST` + `SSH_KEY` secrets.
- **Cosign signature** — sign the published image with
  `sigstore/cosign-installer` + `cosign sign --yes
  ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline@<digest>`. Needs
  a sigstore keypair (or OIDC) configured.
- **SBOM-driven vuln scan on PRs** — add a `grype` job to
  leads-ci that reads the generated SBOM and fails the PR on
  any `Severity >= High` finding. Catches vulns before they
  reach `main`.
- **Image diff job** — `container-diff` between the new image
  and the previous `latest` to surface added/removed packages
  in the PR description.

