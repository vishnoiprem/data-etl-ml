# Permissions — Week 2 (Claude Code's most-leaked control)

Claude Code's permission model is the difference between a useful session and a
disastrous one. The interesting part is not the `allow` list — it's the **shape**
of how you express it, and how it interacts with YOLO mode.

---

## The three-tier model

| Tier | Syntax | Default | What it controls |
|---|---|---|---|
| **allow** | `"Bash(git commit -m*)"` | prompt | First run of the glob pre-authorises the command; subsequent runs are silent. |
| **deny** | `"Bash(git push --force*)"` | deny | Hard refusal. Even in YOLO mode, this wins. |
| **ask** | `"Bash(brew install*)"` | prompt | Always prompts, regardless of mode. |

The `allow` list is a *denylist complement*. Anything not listed is rejected by
default. Anything listed is auto-approved unless `deny` overrides it. **Order
matters**: `deny` beats `allow` beats `ask` beats "unlisted" (`prompt`).

---

## Project vs user level

Two settings files exist, and they merge:

| File | Scope | Wins when… |
|---|---|---|
| `~/.claude/settings.json` | every project on this machine | A `deny` rule is **never** overridden by a project file. |
| `.claude/settings.json` (in repo) | just this repo | A project `allow` rule *narrows* the user-level rules — the project is more restrictive, not less. |

So a `deny` for `git push --force` in your user settings will block it from any
project, including a project that doesn't list it. A `deny` in a project file
only blocks it inside that project.

This is the answer to "why can't my teammate run `terraform apply` even though
their `.claude/` allows it?" — because the global `deny` won the merge.

---

## YOLO mode is not "allow everything"

`yoloMode: true` removes the prompt step. **It does not bypass the `deny` list.**
That is the entire safety model in one sentence.

The course's rule (in `.claude/settings.json` as `yoloMode: false`):

> YOLO mode is a deliberate elevated-trust setting. Flip to true only on
> throwaway branches.

The failure mode this is preventing: enabling YOLO to "skip the prompts" and
then discovering three commands later that you have also given Claude Code
permission to run `git push --force origin master` to your production repo.

---

## The `Bash(git commit -m*)` glob — a real footgun

The project's `allow` lists:

```
Bash(git commit -m*)
```

That matches `git commit -m "..."` but **also** matches `git commit -m "*"`,
because the shell does not expand the glob against the rule — the rule is just
a substring match. The `*` in `-m*` is fine because we never issue
`git commit -m*anything` as a single argv in practice. But if you tried to write
`Bash(git commit -m*)` and someone pasted `git commit -m "` into the chat,
Claude Code would happily glob-mismatch into a `git commit -m "..."` with
whatever body came next.

Lesson: prefer narrow rules. `Bash(git commit -m "feat: *")` is safer than
`Bash(git commit -m*)`. You cannot escape shell semantics from the settings
file, but you can refuse to use broad globs.

---

## What you DO NOT put in `settings.json`

- **Real secrets.** API keys go in your shell environment, not in JSON checked
  into a repo. The MCP server config in `.claude/settings.json` references
  `${env:JIRA_API_TOKEN}` — that is a reference, not a value.
- **Long path allow-lists.** If you need more than ~15 distinct globs, you are
  working in a project whose permissions model is wrong. Restructure so the
  agent runs fewer distinct commands.
- **Things Claude Code already rejects for you.** `Bash(rm -rf /)` is rejected
  by the Claude Code binary itself, not by your settings file. Adding it to
  `deny` is harmless and slightly self-documenting, but don't confuse the two.

---

## The hard rules

1. **Never force-push to a protected branch.** Belt and suspenders — both the
   `deny` entry and the operator's good sense.
2. **Never add a credential-shaped string to `allow`.** Permissions are about
   commands, not payloads. You cannot meaningfully allow-list "Bash(env | grep
   API_KEY)" without giving the agent the ability to leak the key.
3. **Always preserve `deny` on commits.** The `deny` entries in this file are
   the load-bearing part of the safety story. They survive YOLO mode turning
   on. If a teammate asks to "clean up" the deny list, the answer is no.

---

**Last updated:** 2026-10-21