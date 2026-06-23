# feature-dev — End-to-end feature lifecycle with Jira + mabl

A Claude Code [skill](https://docs.claude.com/en/docs/claude-code/skills) that
drives a feature from **request → PR-ready** in four gated phases, with
**Atlassian (Jira)** documenting the intent and **mabl** proving the result:

| Phase | What happens |
|-------|--------------|
| **1 · Plan** | Explore the codebase, create a Jira **Epic** (Context / Goal / Acceptance Criteria), confirm scope with the user. |
| **2 · Build** | Implement the change, build / type-check, and **verify in the real running app** with a real browser (not just tests). |
| **3 · Test** | Map the diff to existing **mabl** tests, author the coverage gap via local authoring, run locally, and **triage failures with the `mabl-debug` live step-through** to isolate root cause (code regression vs. test/state/harness issue). |
| **4 · Ship** | Only after clean triage, commit on the feature branch referencing the Epic key and open the PR. The PR decision stays with the user. |

Each phase gates the next: don't build before the plan is confirmed, don't
author tests before the build is verified, don't open a PR before triaging the
test run.

> This skill is a **conductor** — it composes mabl's focused skills
> (`mabl-pre-pr-check`, `mabl-plan-test`, `mabl-debug`) and standard
> plan/build tools rather than reimplementing them.

---

## Prerequisites

### 1. Claude Code (or a compatible AI coding tool)

The skill is written for [Claude Code](https://docs.claude.com/en/docs/claude-code).
The mabl tooling below also supports Cursor, VS Code, GitHub Copilot, and
`AGENTS.md`-based agents.

### 2. The mabl CLI

The skill drives mabl through its command-line interface. Install it globally
with npm (requires Node.js 18+):

```bash
npm install -g @mablhq/mabl-cli

# verify
mabl --version
```

Then authenticate (one-time browser OAuth; the token lasts ~24h):

```bash
mabl auth login
mabl auth info        # confirm you're logged in
```

You'll need a mabl account with access to the workspace whose tests you want to
run/author. (Don't have one? Talk to your mabl account team about a trial.)

### 3. The mabl debugger + MCP integration (`mabl agent install`)

The triage phase relies on the **`mabl-debug`** skill plus the
**`chrome-for-mabl`** and **`mabl`** MCP servers. Install all of them into your
AI tool in one command:

```bash
# For Claude Code:
mabl agent install claude

# Supported targets: claude · cursor · vscode · copilot · agents-md
mabl agent install <target>
```

This installs the `mabl-debug` skill **and** wires up the `chrome-for-mabl`
(browser automation over CDP) and `mabl` (test data / runs) MCP entries on
supported targets. Useful flags:

- `--scope user` (default) installs into your home directory; `--scope project`
  installs into the current repo.
- `--skip-mcp` installs the skill only, leaving your MCP config untouched.
- `--force` overwrites an existing install.
- After upgrading the CLI, refresh installed skills with `mabl agent update`.

Confirm the debug tooling is available:

```bash
mabl agent debug command-list      # lists every debug subcommand
```

### 4. (Optional) Atlassian MCP — for the Jira Epic in Phase 1

Phase 1 documents the feature as a Jira Epic via the Atlassian MCP server. If
you don't use Jira, you can skip that step and reference the feature directly in
the commit/PR instead. See
[Atlassian's Remote MCP server](https://www.atlassian.com/platform/remote-mcp-server)
for setup.

### 5. A running app to test against

Phases 2–3 verify and test against a **locally running instance** of the app
(this repo defaults to `http://localhost:3000`). Start your dev server before
invoking the skill.

---

## Configuration — adapt the project constants

`SKILL.md` contains a **Project constants** table that hard-codes the values for
*this* demo repo (Jira project key, mabl workspace / application / environment
ids, local URL, test credentials).

**Reusing this skill in another repo? Start from
[`SKILL.template.md`](./SKILL.template.md)** — a portable, project-agnostic copy
where every project-specific value is a `<PLACEHOLDER>` and the constants table
includes a "How to find it" column. Fill it in, generalize/trim the gotchas for
your stack, then rename it to `SKILL.md` so Claude Code loads it.

The values you'll need to supply:

| Constant | How to find it |
|----------|----------------|
| mabl workspace id | `mabl auth info`, or the mabl app URL `…/workspaces/<id>/…` |
| mabl application / environment ids | mabl app, or the `mabl`-MCP `get_environments` / app settings |
| mabl credentials ids | the `mabl`-MCP `get_credentials` tool (note which is admin vs. client) |
| Jira cloudId / project key | Atlassian MCP `getAccessibleAtlassianResources` / `getVisibleJiraProjects` |
| Local dev URL + test creds | your app |

---

## Usage

With the prerequisites in place and your dev server running, invoke the skill in
Claude Code:

```
/feature-dev Add the ability to see price change alongside the percent change on the stock tracker page
```

Claude will then walk Phases 1→4, pausing to confirm scope and the final PR
decision with you.

---

## What you get

- A **Jira Epic** documenting the feature (Context / Goal / Acceptance Criteria).
- A **tight, browser-verified code change** matching the repo's conventions.
- **mabl coverage**: existing tests mapped to the diff, plus a new/updated test
  for the new behavior, run locally and published to the mabl cloud for history.
- **Root-caused triage**: when a test goes red, a live `mabl-debug` step-through
  tells you definitively whether your change broke something or the test/harness
  did — instead of guessing from terse headless errors.
- A **PR** (on your go) referencing the Epic, ready for review.

---

## Why `mabl-debug` for triage?

Headless test re-runs report terse, sometimes-misleading errors — "Element not
found" can actually mean *the element was filtered out by app state*, or that a
heal timed out. Re-running headless with tweaked inputs just changes which
symptom you see; it rarely isolates the cause. A **live step-through** launches a
real Chrome attached to the agent, runs up to the failing step, lets you inspect
the actual page, and replays the failing step — so whether it **passes or
stops** tells you immediately who owns the fix (your code, or the test). It then
reproduces and verifies the fix in the same session.

See [`SKILL.md`](./SKILL.md) for the full phase-by-phase instructions and the
baked-in gotchas from real runs.
