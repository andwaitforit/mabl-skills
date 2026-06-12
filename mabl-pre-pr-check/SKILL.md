---
name: mabl-pre-pr-check
description: >-
  Pre-PR safety net — analyze the current commit (or working changes), find the
  mabl tests most relevant to what changed, and run them locally via the mabl
  CLI for fast feedback before opening a pull request. Use when the user wants
  to "check my changes against mabl tests", "run relevant mabl tests before I
  push/PR", "what mabl tests cover this commit", "smoke-test my diff in mabl", or
  any pre-PR / pre-push validation against an existing mabl test suite.
---

# mabl Pre-PR Check

Catch regressions **before** the PR. This skill maps the code you just changed to
the mabl tests that exercise those user-facing flows, then runs the best matches
locally through the mabl CLI so the developer sees pass/fail in their own browser
within minutes — no waiting on CI or a cloud plan run.

The flow: **diff → derive intent → match tests → run locally → triage.**

---

## When to use

- Right before opening a PR or pushing a branch.
- After finishing a feature/fix and wanting a quick "did I break a known flow?" check.
- When the user references a commit, a range, or just "my changes" and mabl coverage in the same breath.

Do **not** use this to author new tests (that's the mabl authoring tools) or to run
a full cloud plan (that's `run_mabl_test_cloud` / `mabl plans run`).

---

## Inputs (all optional)

| Arg | Meaning | Default |
|-----|---------|---------|
| commit ref | `HEAD`, a SHA, `main..HEAD`, etc. | `HEAD` (the most recent commit) |
| `--working` | Analyze uncommitted working-tree + staged changes instead of a commit | off |
| `--url <url>` | Run tests against this URL (e.g. a local dev server / preview) | local dev server (prompt/detect if not given) |
| `--workspace <name|id>` | Target mabl workspace | configured default (see Step 0) |
| `--max <n>` | Max tests to run | 3 |
| `--terminal` | Run in a visible detached Terminal window (agent can't observe result) instead of auto-detect | off (auto-detect) |

Parse these from the user's invocation; otherwise use defaults. Never block on an arg you can infer.

---

## Step 0 — Preflight

Run these checks first and fix/surface any gap before proceeding:

1. **CLI present & authed:**
   ```bash
   mabl --version && mabl auth info
   ```
   - Missing CLI → tell the user to `npm install -g @mablhq/mabl-cli` and stop.
   - Not logged in / expired → instruct `mabl auth login` (or `mabl auth activate-key <key>`) and stop.

2. **mabl MCP required.** This skill needs the mabl MCP server for semantic test matching (`get_mabl_tests` returns descriptions + step summaries — the CLI's `tests list` returns names only, which isn't enough to map a diff to coverage reliably).
   - Check whether the `mcp__mabl__*` tools are present in this session.
   - **Not connected** → stop and tell the user to add the mabl MCP server, then re-run. Point them at `mabl agent install <target>` (installs the mabl MCP entry + debug skill into supported editors) or their MCP client config. Do not attempt a degraded CLI-only match.

3. **Workspace:** resolve the target workspace once and reuse it.
   - If the user named one, match it against `mabl workspaces list` (or MCP `get_workspaces`).
   - Else read a saved default: `mabl config get workspace-id` — or a `MABL_WORKSPACE_ID` you've stored in the project's `.claude/` config.
   - Else list workspaces and ask which one (then offer to save it via `mabl config set workspace-id <id>` so future runs are zero-prompt).

4. **Git repo:** confirm `git rev-parse --is-inside-work-tree` succeeds.

---

## Step 1 — Resolve the change set

Get the diff that defines "what changed":

```bash
# default: the most recent commit
git show --stat --format= HEAD          # changed files
git show HEAD                           # full diff (read selectively)

# a range / specific ref if the user gave one
git diff --stat <ref>
git diff <ref>

# --working mode
git status --short && git diff HEAD      # staged + unstaged
```

Produce a concise list of changed files grouped by area (frontend pages, components,
routes, API/controllers, backend logic, styles, config). Skip lockfiles, generated
files, and pure-formatting churn — they don't map to behavior.

---

## Step 2 — Derive user-facing intent → search queries

mabl tests exercise **end-user behavior**, not code internals. Translate the diff
into the user-facing flows it affects, then write **1–5 short natural-language search
queries**. Mapping heuristics:

- A page/route component (`IronsPLP.tsx`, `routes/checkout.ts`) → the page/flow by name ("Irons product listing page", "checkout flow").
- A shared UI component → the flow(s) that render it ("login form", "account transfer card").
- An API endpoint/controller → API tests for that resource ("transfers API", "create user endpoint").
- Backend business logic → the user-facing feature it powers (a donation calc change → "donation on withdrawal").

Show the developer the inferred change summary + the queries you'll search, so they
can sanity-check the framing before you search.

---

## Step 3 — Discover relevant tests

Run MCP `get_mabl_tests` once per query (pass `workspaceId`), then merge and
de-duplicate by test id. Use the returned `description` + `stepsChunks` to judge fit.

Rank candidates by relevance (exact flow match > same feature area > tangential). Drop
anything clearly unrelated. If queries are too narrow and return nothing, broaden once
(e.g. feature area instead of specific page) before concluding there's no coverage.

---

## Step 4 — Confirm the run set

Present the ranked candidates compactly:

```
Changed: client/src/pages/IronsPLP.tsx, client/src/components/ProductGrid.tsx
Inferred flow: Irons product listing page — navigation + product display

Relevant mabl tests:
  1. Irons Product Listing Page (PLP) Navigation   [browser]  ← strong match
  2. Homepage → Category Nav                         [browser]  ← partial
```

Default to running the top `--max` matches (default 3). Ask for confirmation only if
the picks are ambiguous, there are zero matches, or the user requested review. With
zero matches, say so plainly (this change may have no existing coverage — a gap worth a new test).

---

## Step 5 — Run locally via the mabl CLI

**Resolve the run URL first.** The point of a pre-PR check is to exercise the
developer's *uncommitted local code*, so tests run against the **local dev server**, not
the deployed mabl environment:
- If the user passed `--url`, use it.
- Else detect a running dev server (probe common ports — `3000`, `3001`, `5173`, `8080`
  — or read it from the repo's dev config). If found, confirm it with the user.
- Else **ask** for the local URL (and remind them the dev server must be running).
- Only fall back to the mabl environment default if the user explicitly says to test the deployed app.

For each selected test, run with the mabl CLI. Carry over the test's attached
credentials/environment automatically (running by `--id` pulls the test config).

There are two execution modes. **Default to auto-detect** — it lets the agent report
pass/fail and triage without the user copy-pasting terminal output.

### Mode A — Auto-detect (default)

Run as a **harness-tracked background process** that **publishes results to the mabl cloud**
via `--reporter mabl` (Unified Reporting). The browser still launches **headed** so the user
can watch live. The harness re-invokes the agent when the process exits; the agent then reads
both the local exit code and the published cloud run.

First resolve the test's `applicationId` (and environment) so the cloud run associates
correctly — `--reporter mabl` works best with `--application-id` (and `--environment-id`):
- `applicationId` → from `get_mabl_test_details` for the test.
- `environmentId` → from `get_environments` for the workspace (the test's default env, or
  the one matching the target). If genuinely ambiguous, omit it and let the test default apply.

```bash
RUN_DIR="$(mktemp -d)/mabl-pre-pr"; mkdir -p "$RUN_DIR"
mabl tests run \
  --id <testId> \
  -w <workspaceId> \
  --url <resolvedUrl> \              # e.g. http://localhost:3000
  --application-id <applicationId> \ # associate the published cloud run
  --reporter mabl \                  # publish results to the mabl app (shareable + history)
  [--environment-id <environmentId>] \
  [--creds <credentialsId>] \
  > "$RUN_DIR/run.log" 2>&1
# NOTE: do NOT pass --keep-browser-open here. It keeps the process alive, so a
# background run never exits and the harness never notifies you. Browser closing
# is fine in Mode A — the result and screenshots are in the cloud.
```

**Billable / AI assertions.** Local CLI runs **disable GenAI and visual assertions by
default** — any such step auto-fails with "AI assertions are not available in CLI runs."
Before running, check the test's steps (from `get_mabl_test_details`) for GenAI/visual
assertions. If present, either:
- add `--allow-billable-features` to run them for real (consumes mabl credits — confirm with the user first), or
- run without the flag but **treat a failure on only those steps as a harness skip, not a
  code regression**, and say so in the verdict.

Launch this via the Bash tool with `run_in_background: true` (NOT a detached `osascript`
window — that's invisible to the agent).

**Observe the result** (when the harness notifies you the process exited):
1. ⚠️ **Do not trust the exit code alone.** `mabl tests run` can exit `0` even when a test
   failed. Determine pass/fail from the `run.log` summary block — parse the
   `Passed:` / `Failed:` counts (and the per-test `Test Failed` / `Test Passed` line).
2. **Confirm via the published cloud run** (authoritative): call MCP
   `get_latest_test_runs(testId, workspaceId)` — returns the latest run's `status`,
   `testRunId`, environment, and (on failure) an AI-generated `errorMessage`. For deeper
   analysis use `mabl_result_analysis_chat` / `analyze_failure(testRunId)`.
3. **Read which step failed** from `run.log` and judge whether it's a *code* failure vs a
   *harness* limitation — e.g. a GenAI/visual assertion that was skipped (see billable note
   below) is NOT a regression in the user's change. Report that distinction explicitly.
4. `run.log` also prints a **link to the run in the mabl app** — surface it so the user can
   open the full result with screenshots.

Then go straight to Step 6 with a concrete verdict — no need to ask the user what happened.

### Mode B — Visible terminal (live demos / `--terminal`)

For screen-shares where the point is to *show* the run in its own window, launch detached
and let the user narrate. The agent cannot observe the result in this mode.

```bash
osascript -e 'tell application "Terminal" to do script "mabl tests run --id <id> -w <ws> --url <url> --keep-browser-open"' \
          -e 'tell application "Terminal" to activate'
# verify it started:
pgrep -fl "mabl tests run"
```

Notes:
- `--keep-browser-open` leaves Chrome open for inspection after asserts run.
- Add `--reporter mabl` here too if you want the demo run published to the cloud; otherwise
  Mode B prints results only in its own window and the agent cannot see them.
- Run multiple tests concurrently only if they won't fight over a single dev server / port;
  otherwise run them sequentially (each background run completing before the next starts).

---

## Step 6 — Triage & next step

In Mode A you already have the `run.log` summary + the published cloud run, so state the
verdict directly. In Mode B, ask the user for the terminal output first.

- **All pass** → report green, clear to open the PR.
- **Failure** → read the failing step from `run.log` / the cloud run (or ask, in Mode B).
  First separate a real *code* failure from a *harness* skip (e.g. a billable AI assertion).
  Common pre-PR causes: a moved/renamed element (your change shifted a selector — often
  an auto-heal candidate), changed copy breaking an assertion, or a genuine behavior
  regression. Cross-reference the failing step against the diff from Step 1 to localize
  the cause, and propose a fix.
- Optionally suggest `mabl agent debug` for deeper local failure analysis.
- If Step 3 found **no coverage**, flag it as a gap and offer to draft a new mabl test
  for the changed flow.

---

## Decision defaults (don't ask unless it matters)

- Commit to analyze: `HEAD`.
- Tests to run: top **3** by relevance.
- Execution: **auto-detect** (Mode A — background run with `--reporter mabl`; agent reads
  exit code + the published cloud run). Use Mode B (visible terminal) only for `--terminal`
  / live screen-shares.
- Browser: Chrome, headed (visible even in auto-detect). Browser closes at run end in
  Mode A (do not keep it open — it would block the background process from exiting);
  kept open only in Mode B.
- Run target URL: the **local dev server** — `--url` if given, else detect, else ask.
  Test the deployed mabl environment only if the user explicitly asks.
- Workspace: saved default; prompt + offer to save only on first use.

## Limitations

- Requires the mabl MCP server connected (used for relevance matching). Without it, stop and prompt the user to connect it.
- Mode A publishes results to the mabl cloud via `--reporter mabl`, so each run gets a
  shareable app link + history. Execution is still local (no cloud credits, sequential),
  per the mabl Unified Reporter — the cloud entry is the report, not a cloud execution.
- In Mode B (visible terminal) the agent cannot observe the result — use Mode A (default) for auto-detection.
- Mobile tests aren't supported for local CLI execution.
