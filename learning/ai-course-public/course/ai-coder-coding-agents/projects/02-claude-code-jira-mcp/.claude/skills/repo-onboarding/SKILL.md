---
name: repo-onboarding
description: Bootstraps the agent's understanding of a fresh repository. Use this skill the first time you start work in any new repo.
---

# Repo onboarding skill

This skill is the structured version of `/onboard`. It exists as a skill rather
than a slash command so that other skills (e.g. `add-feature`, `fix-bug`) can
*invoke* it without the human having to type `/onboard` separately.

## When to invoke

You must run this skill **before writing any code** in a repository you have not
worked on in this session. A fresh `/onboard` does not replace it; this skill
loads context the rest of the work will rely on.

## Inputs

- `repo_root` — absolute path to the repo. Defaults to the current working
  directory.

## Procedure

1. **Top-level scan.** Glob the repo for the top-level files: `README*`,
   `pyproject.toml`, `package.json`, `Gemfile`, `Cargo.toml`, `go.mod`,
   `requirements*.txt`, `Makefile`, `Dockerfile`, `.claude/`. Read the ones that
   exist. Do not read `node_modules/` etc.

2. **Stack determination.** From those files, record: language, web framework,
   ORM / DB driver, datastore, auth, test runner, formatter. Each finding must
   cite the file and the line.

3. **Layout.** Glob for `src/`, `app/`, `lib/`, `cmd/`, `internal/`. For each
   top-level directory, read its `__init__.py` or a single representative file
   to determine the responsibility.

4. **Convention scan.** Look for `.editorconfig`, `ruff.toml`, `.eslintrc*`,
   `.prettierrc*`, `biome.json`, `commitlint.config*`. Read them. Identify the
   formatter, the import order, and the line length. If two formatters are
   configured, flag it as a conflict.

5. **Convention enforcement sweep.** Pick one route file and one model file.
   Confirm they conform to whatever the formatter claims. If they don't, the
   project is mid-migration; record that as a gotcha.

6. **Gotcha hunt.** Grep for: `TODO`, `FIXME`, `HACK`, `XXX`, `temporary`,
   `permanent`, `monkeypatch`. Read every match. Quote any one that looks like
   a real instruction in a comment.

7. **Generate the brief.** Use the format from `/onboard` (which is the same
   output format — the command and the skill should produce identical briefs).

## Outputs

A markdown brief structured exactly as in `/onboard`. **No edits to the
repository.** This skill is read-only.

## What this skill is NOT

- Not an architecture review. If you want opinions about whether the layering
  is good, run an `architecture-review` skill (not written here).
- Not a permissions audit. `repo-permissions-audit` (also not written here)
  would do that.