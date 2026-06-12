# mabl Pre-PR Check — Claude Code skill

A pre-PR safety net for Claude Code. Point it at the change you just made and it will:

1. Read the diff of your current commit (or working changes).
2. Figure out which **user-facing flows** that code affects.
3. Search your mabl workspace for the **existing tests** that cover those flows.
4. Run the best matches **locally via the mabl CLI** against your dev server.
5. Report pass/fail (and publish the run to your mabl cloud workspace), then help you triage.

The goal: catch a broken flow in minutes, on your own machine, **before** you open the PR —
without waiting on CI or a cloud plan run.

---

## Prerequisites

| Requirement | Why | Check |
|-------------|-----|-------|
| **mabl CLI** installed & authenticated | Runs the tests locally | `mabl --version && mabl auth info` |
| **mabl MCP server** connected to your AI client | Semantic test matching (maps your diff to coverage) | `mabl` tools appear in the session |
| **Existing mabl tests** in the workspace | The skill matches against them; it doesn't author new ones | — |
| **Git repository** | Source of the diff | `git rev-parse --is-inside-work-tree` |
| **Local dev server running** | Tests exercise your uncommitted code | e.g. `npm run dev` |

Setup help:
- Install the CLI: `npm install -g @mabl/cli` (or `brew install mabl`), then `mabl auth login`.
- Connect the mabl MCP server: `mabl agent install <target>` (installs the mabl MCP entry +
  debug skill into supported AI tools), or add it to your MCP client config manually.

---

## Install

Drop the `mabl-pre-pr-check/` folder into either:

- **Project scope:** `<your-repo>/.claude/skills/mabl-pre-pr-check/`
- **User scope (all repos):** `~/.claude/skills/mabl-pre-pr-check/`

That's it — Claude Code discovers it automatically. Confirm it's loaded by typing `/` and
looking for `mabl-pre-pr-check`.

---

## Usage

Invoke it after making a change:

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
| `--terminal` | Run in a visible Terminal window instead of auto-detect | off |

Examples:
```
/mabl-pre-pr-check --working --url http://localhost:3000
/mabl-pre-pr-check main..HEAD --max 5
/mabl-pre-pr-check --workspace "My Team Workspace"
```

First run will offer to save your default workspace so later runs are zero-prompt.

---

## Two execution modes

- **Auto-detect (default).** Runs as a background process and publishes the result to your
  mabl cloud workspace (`--reporter mabl`). The browser is still **visible** so you can
  watch, but Claude reads the result itself and reports the verdict — no copy-pasting
  terminal output. Each run gets a shareable mabl app link + history.
- **Visible terminal (`--terminal`).** Launches the run in its own Terminal window for live
  demos / screen-shares. Claude can't observe the result in this mode — you narrate it.

---

## Good to know

- **Local execution, cloud reporting.** Runs execute on your machine (no cloud credits,
  sequential), but `--reporter mabl` posts the result to the cloud so it's shareable and
  tracked. The cloud entry is the *report*, not a cloud execution.
- **GenAI / visual assertions are billable.** Local CLI runs disable them by default, so a
  test that includes one will show that step as failed unless you opt in with
  `--allow-billable-features` (consumes mabl credits). The skill flags this so a skipped
  AI assertion isn't mistaken for a code regression.
- **No matching test?** The skill says so plainly — that's a coverage gap worth a new test
  (see the `mabl-test-from-requirement` skill).
- **Mobile tests** aren't supported for local CLI execution.

---

## How it decides what to run

mabl tests exercise end-user behavior, so the skill translates code changes into the flows
they affect (a changed page component → that page's navigation test; a changed API
controller → that resource's API test; changed business logic → the feature it powers),
searches your workspace semantically for those flows, ranks the matches, and runs the
strongest ones. It shows you the inferred framing before running so you can redirect it.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
