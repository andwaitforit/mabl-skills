# mabl Pre-PR Check — Kiro skill

A pre-PR safety net for Kiro. Point it at the change you just made and it will:

1. Read the diff of your current commit (or working changes).
2. Figure out which **user-facing flows** that code affects.
3. Search your mabl workspace for the **existing tests** that cover those flows.
4. Run the best matches **locally via the mabl CLI** against your dev server.
5. Report pass/fail (and publish the run to your mabl cloud workspace), then help you triage.

The goal: catch a broken flow in minutes, on your own machine, **before** you open the PR —
without waiting on CI or a cloud plan run.

## Prerequisites

Shared setup (mabl CLI, MCP config) is in [`../README.md`](../README.md). Beyond that:

| Requirement | Why | Check |
|-------------|-----|-------|
| **`mabl` MCP server** connected | Semantic test matching (maps your diff to coverage) | mabl tools appear in the session |
| **Existing mabl tests** in the workspace | The skill matches against them; it doesn't author new ones | — |
| **Git repository** | Source of the diff | `git rev-parse --is-inside-work-tree` |
| **Local dev server running** | Tests exercise your uncommitted code | e.g. `npm run dev` |

## Install

```bash
cp -r mabl-pre-pr-check ~/.kiro/skills/        # or <your-repo>/.kiro/skills/
```

Confirm it loaded by typing `/` and looking for `mabl-pre-pr-check`.

## Usage

```
/mabl-pre-pr-check
```

It defaults to the most recent commit (`HEAD`), the top 3 most-relevant tests, your
configured workspace, and your local dev server. You can also just ask in plain language —
e.g. *"run the relevant mabl tests for my changes before I PR."*

### Optional arguments

| Arg | Meaning | Default |
|-----|---------|---------|
| commit ref | `HEAD`, a SHA, `main..HEAD`, … | `HEAD` |
| `--working` | Use uncommitted working-tree + staged changes instead of a commit | off |
| `--url <url>` | Run against this URL (your dev server / preview) | local dev server (detect/ask) |
| `--workspace <name\|id>` | Target mabl workspace | saved default |
| `--max <n>` | Max tests to run | 3 |
| `--detached` | `nohup` the run and poll the log instead of blocking the turn | off |

Examples:
```
/mabl-pre-pr-check --working --url http://localhost:3000
/mabl-pre-pr-check main..HEAD --max 5
/mabl-pre-pr-check --workspace "My Team Workspace"
```

First run will offer to save your default workspace so later runs are zero-prompt.

## Two execution modes

- **Blocking (default).** Kiro runs `mabl tests run` in the foreground and reads the result
  straight from stdout. The browser is **visible** so you can watch, and `--reporter mabl`
  publishes a shareable cloud run + history. A typical browser test is 1–5 minutes.
- **Detached (`--detached`).** For jobs that must outlive the turn, the run is `nohup`-ed to
  a log file and polled on a later turn. Use this for long suites or a live screen-share.

> This differs from the Claude Code original, which backgrounds every run and relies on the
> harness to re-invoke the agent on exit. Kiro has no such callback — see
> [`../README.md`](../README.md#what-changed-from-the-claude-code-originals).

## Good to know

- **Local execution, cloud reporting.** Runs execute on your machine (no cloud credits,
  sequential), but `--reporter mabl` posts the result to the cloud so it's shareable and
  tracked. The cloud entry is the *report*, not a cloud execution.
- **Never pass `--keep-browser-open` in a blocking run** — the command never returns and the
  turn hangs.
- **GenAI / visual assertions are billable.** Local CLI runs disable them by default, so a
  test that includes one will show that step as failed unless you opt in with
  `--allow-billable-features` (consumes mabl credits). The skill flags this so a skipped
  AI assertion isn't mistaken for a code regression.
- **No matching test?** The skill says so plainly — that's a coverage gap worth a new test.
- **Mobile tests** aren't supported for local CLI execution.

## How it decides what to run

mabl tests exercise end-user behavior, so the skill translates code changes into the flows
they affect (a changed page component → that page's navigation test; a changed API
controller → that resource's API test; changed business logic → the feature it powers),
searches your workspace semantically for those flows, ranks the matches, and runs the
strongest ones. It shows you the inferred framing before running so you can redirect it.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
