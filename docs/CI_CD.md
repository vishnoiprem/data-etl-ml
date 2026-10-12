# CI/CD — leads-pipeline

This doc covers the three GitHub Actions workflows and the GHCR
publish that wrap the `leads-pipeline/draft-cron` Python package.

## Workflows at a glance

| Workflow      | File                                | Triggers                                   | Purpose |
|---------------|-------------------------------------|--------------------------------------------|---------|
| `leads-ci`    | `.github/workflows/leads-ci.yml`    | push to `main` + 2 active feature branches, PRs to `main` | Run 6 test modules + lint + Dockerfile build |
| `leads-cd`    | `.github/workflows/leads-cd.yml`    | push to `main`, manual dispatch            | Build + push container image to `ghcr.io` + verify |
| `pip-audit`   | `.github/workflows/pip-audit.yml`   | changes to `requirements*.txt`, weekly Mon 06:00 UTC, manual dispatch | Security scan, upload SARIF |

## `leads-ci`

Two jobs:

1. **`test`** — spins up a Postgres 15 service container, runs the
   6 in-repo test modules in order, runs flake8 on the modified
   source files (advisory only — pre-existing warnings surface in
   the UI as a warning, not a hard failure).
2. **`dockerfile-build`** — builds the Dockerfile in
   `leads-pipeline/draft-cron` (without pushing) and smoke-tests
   the resulting image. This guards the CD workflow: a broken
   Dockerfile can't reach `main` because the PR will fail.

### Trigger branches

`main` plus the two active feature branches
(`feature/agent-coding-11oct`, `feature/auto-pilot-ai-leads-loop`).
To add a branch, edit the `branches:` list in the `on:` block.

### Concurrency

`cancel-in-progress: true` — a force-push cancels the previous
run. Saves runner minutes on rapid iteration.

## `leads-cd`

Two jobs, sequential:

1. **`build-and-push`** — uses `docker/build-push-action@v6` with
   the `metadata-action` to compute the tags. Pushes to
   `ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline`.
2. **`verify`** — re-pulls the just-published image and runs a
   Python smoke test inside it (imports every critical module +
   prints the runtime UID). If the manifest is broken, the
   workflow fails before the bad tag is left in GHCR.

### Image tags

| Push event                | Tags applied                              |
|---------------------------|-------------------------------------------|
| push to `main`            | `latest`, `main-<short_sha>`, `<short_sha>` |
| manual `workflow_dispatch` with `tag_suffix=rc1` | `latest-rc1`, `<short_sha>` |
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

## `pip-audit`

Weekly Monday 06:00 UTC scan of every `requirements*.txt` in the
repo, plus on every change to those files. Uploads a SARIF to
the Code Scanning tab so the security advisories show up inline
on PRs.

## Dependabot

`.github/dependabot.yml` covers three ecosystems:

- `pip` (root, plus `/leads-pipeline/draft-cron` for the CD
  manifest)
- `npm` (TypeScript starters under `agentic-ai/` and `aws/`)
- `github-actions` (all workflows)
- `docker` (the new leads-pipeline Dockerfile)

Dependabot opens a PR per major-version bump. The `CODEOWNERS`
file auto-assigns `@vishnoiprem` for review on CI/CD paths so a
fresh commit to the workflow files won't slip in unreviewed.

## Local reproduction

To reproduce the CI build locally:

```bash
# CI test step
cd leads-pipeline/draft-cron
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt flake8
# (in another terminal: docker compose up -d postgres)
PYTHONPATH=. python -m tests.test_dedup_key   # etc.

# CD build step
docker build -t leads-pipeline:local leads-pipeline/draft-cron
docker run --rm --entrypoint python leads-pipeline:local \
  -c "import db.lead_store, find_more_leads; print('OK')"
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
- **Tag-driven releases** — extend `metadata-action` with
  `type=semver,pattern={{version}}` to publish a versioned tag
  (e.g. `1.2.3`) on `v*` git tags.
- **Renovate instead of Dependabot** — Renovate groups PRs more
  aggressively and handles docker images better. Migration is a
  1-file change (`renovate.json5`).
