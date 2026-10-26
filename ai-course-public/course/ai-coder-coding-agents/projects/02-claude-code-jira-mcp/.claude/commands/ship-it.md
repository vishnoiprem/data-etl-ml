---
description: Ship the current branch — test, lint, stage, commit, push, open a PR
argument-hint: "[optional one-line summary of what changed]"
allowed-tools: Bash(make:*), Bash(pytest:*), Bash(ruff:*), Bash(git:*), Read, Edit, Write
---

Ship the current branch. Follow these steps in order. Do not skip a step. Do not
reorder them.

**1. Preflight — refuse to continue if any of these is true.**
- `git status` shows unmerged conflicts (`UU`, `AA` markers) → STOP, report them.
- Working tree has modifications in files you did not touch in this session →
  report them and ask before staging.
- Current branch is `master` or `main` → STOP. This command is for feature
  branches only. Tell the user to create a branch first.

**2. Verify. Paste the real output — never predict it.**
```
make test
make lint
```
If either fails: STOP. Report the actual failure text. Do not commit code that
does not pass its own test suite, and do not "fix and retry" silently — fix,
show the diff, then re-run.

**3. Review your own diff before staging.**
```
git diff
```
Look for: debug statements (`print`, `console.log`, `console.error`, `breakpoint`,
`pdb`), commented-out blocks, `.env` or credential-shaped strings, and any file
you cannot explain. Remove the debug statements. If you find a credential, STOP
and tell the user — do not commit it.

**4. Stage deliberately.**
Stage by explicit path. Never `git add -A` or `git add .` — that is how
`.env`, build artifacts, and someone else's in-progress work get committed.
```
git add <paths you actually changed>
```

**5. Commit.**
Use the message supplied in `$ARGUMENTS` if present. Otherwise compose:
```
<type>(<scope>): <imperative summary under 72 chars>
```
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
Then the body: *why*, not *what*. The diff already says what.

**6. Push.**
```
git push -u origin <current-branch>
```
NEVER force-push to a shared branch. If the push is rejected as non-fast-forward,
STOP and report it. Do not resolve a rejected push by adding `--force`.

**7. Open the PR.**
```
gh pr create --title "<type>(<scope>): <summary>" --body "$(cat <<'EOF'
## Summary
<1-3 bullets>

## Test plan
- [ ] `make test` passes (<paste count>)
- [ ] `make lint` passes
- [ ] <manual verification you actually performed>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**8. Report back.** The PR URL, what you actually ran, and anything you skipped
and why. If you skipped a step, say so explicitly — never report a step you did
not perform as if you had.