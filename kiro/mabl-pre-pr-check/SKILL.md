---
name: mabl-pre-pr-check
description: >-
  Pre-PR safety net — analyze the current commit (or working changes), find the
  mabl tests most relevant to what changed, and run them locally via the mabl
  CLI for fast feedback before opening a pull request. Use when the user wants
  to "check my changes against mabl tests", "run relevant mabl tests before I
  push/PR", "what mabl tests cover this commit", "smoke-test my diff in mabl", or
  any pre-PR / pre-push validation against an existing mabl test suite.
metadata:
  version: "1.0.0"
  host: kiro
compatibility: >-
  Requires the mabl CLI (Node 18+) on PATH, the mabl MCP server connected in
  Kiro, a git repo, and a local Chrome. Network access required.
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
| `--workspace <name\|id>` | Target mabl workspace | configured default (see Step 0) |
| `--max <n>` | Max tests to run | 3 |
| `--detached` | Run via `nohup` + poll instead of blocking the chat turn | off (blocking) |

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

2. **mabl MCP required.** This skill needs the mabl MCP server for semantic test matching (`search_mabl_tests` returns descriptions + step summaries — the CLI's `tests list` returns names only, which isn't enough to map a diff to coverage reliably).
   - Check whether the mabl MCP tools are available in this session.
   - **Not connected** → stop and tell the user to add the mabl server to
     `.kiro/settings/mcp.json` (workspace) or `~/.kiro/settings/mcp.json` (global), then
     connect it from Kiro's **MCP Servers** panel. There is **no `mabl agent install kiro`**
     target — the entry is written by hand; see this tree's `README.md`. Do not attempt a
     degraded CLI-only match.

3. **Workspace:** resolve the target workspace once and reuse it.
   - If the user named one, match it against `mabl workspaces list` (or MCP `list_mabl_workspaces`).
   - Else read a saved default: `mabl config get workspace-id` — or a `MABL_WORKSPACE_ID`
     recorded in the project's `.kiro/steering/`.
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

⚠️ **Watch for committed-vs-working drift.** A local dev server serves the **working
tree**, so if the tree is dirty, that — not the last commit — is what mabl will
actually exercise. When `git status --short` shows changes, say so and consider
`--working`; never map coverage from a committed ref alone when uncommitted changes
touch the same files.

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

Run MCP `search_mabl_tests` once per query (pass `workspaceId`), then merge and
de-duplicate by test id. Use the returned `description` + step chunks to judge fit.

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

First resolve the test's `applicationId` (and environment) so the published cloud run
associates correctly — `--reporter mabl` works best with `--application-id` (and
`--environment-id`):
- `applicationId` → from `get_mabl_test` for the test.
- `environmentId` → from `list_mabl_environments` for the workspace (the test's default
  env, or the one matching the target). If genuinely ambiguous, omit it and let the test
  default apply.

### Mode A — Blocking run (default)

> **Kiro execution model.** Kiro runs a shell command and **waits** for it to finish,
> handing you stdout/stderr directly — there is no background-process harness that
> re-invokes the agent on exit. Run the test in the foreground and read the result from
> the returned output. A typical browser test is 1–5 minutes, well within a normal
> command execution.

Publish results to the mabl cloud via `--reporter mabl` (Unified Reporting) so each run
gets a shareable app link + history. The browser still launches **headed** so the user
can watch live.

```bash
RUN_DIR="$(mktemp -d)/mabl-pre-pr"; mkdir -p "$RUN_DIR"
mabl tests run \
  --id <testId> \
  -w <workspaceId> \
  --url <resolvedUrl> \              # e.g. http://localhost:3000
  --application-id <applicationId> \ # associate the published cloud run
  --reporter mabl \                  # publish results to the mabl app (shareable + history)
  [--environment-id <environmentId>] \
  [--credentials-id <credentialsId>] \
  2>&1 | tee "$RUN_DIR/run.log"
# NOTE: do NOT pass --keep-browser-open. It keeps the process alive, so the command
# never returns and the turn hangs. Browser closing is fine — the result and
# screenshots are in the cloud.
```

Run tests **sequentially**, one command per test — they share a single dev server/port.

### Mode B — Detached + poll (`--detached`, or a run you expect to exceed the command timeout)

For long jobs or live screen-shares where the run must outlive the turn, detach it and
poll the log:

```bash
RUN_DIR="$HOME/.kiro/tmp/mabl-pre-pr"; mkdir -p "$RUN_DIR"
nohup mabl tests run --id <id> -w <ws> --url <url> --reporter mabl \
  > "$RUN_DIR/run.log" 2>&1 &
echo "started pid $!"
```

Then poll on a later turn — **never** in a busy-wait loop inside one turn:

```bash
tail -n 40 "$RUN_DIR/run.log"; pgrep -fl "mabl tests run" || echo "run finished"
```

Tell the user you've detached it and check back when they prompt you again, or after a
single bounded `sleep`. Do not spin.

### Observing the result

1. ⚠️ **Do not trust the exit code alone.** `mabl tests run` can exit `0` even when a test
   failed. Determine pass/fail from the `run.log` summary block — parse the
   `Passed:` / `Failed:` counts (and the per-test `Test Failed` / `Test Passed` line).
2. **Confirm via the published cloud run** (authoritative): call MCP
   `list_mabl_test_runs` / `get_mabl_test_run` — returns the latest run's `status`,
   `testRunId`, environment, and (on failure) an AI-generated error message. For deeper
   analysis use `analyze_mabl_failure(testRunId)`.
3. **Read which step failed** from `run.log` and judge whether it's a *code* failure vs a
   *harness* limitation — e.g. a GenAI/visual assertion that was skipped (see billable note
   below) is NOT a regression in the user's change. Report that distinction explicitly.
4. `run.log` also prints a **link to the run in the mabl app** — surface it so the user can
   open the full result with screenshots.

**Billable / AI assertions.** Local CLI runs **disable GenAI and visual assertions by
default** — any such step auto-fails with "AI assertions are not available in CLI runs."
Before running, check the test's steps (from `get_mabl_test_steps`) for GenAI/visual
assertions. If present, either:
- add `--allow-billable-features` to run them for real (consumes mabl credits — confirm with the user first), or
- run without the flag but **treat a failure on only those steps as a harness skip, not a
  code regression**, and say so in the verdict.

⚠️ **Never `grep` a run log raw — filter by line length first.** These logs embed base64
screenshot payloads; a naive grep can dump hundreds of KB into context. Always pipe
through a length filter, e.g. `awk 'length($0) < 300'` before grepping.

---

## Step 6 — Triage & next step

You have the `run.log` summary + the published cloud run, so state the verdict directly.

- **All pass** → report green, clear to open the PR.
- **Failure** → read the failing step from `run.log` / the cloud run.
  First separate a real *code* failure from a *harness* skip (e.g. a billable AI assertion).
  Common pre-PR causes: a moved/renamed element (your change shifted a selector — often
  an auto-heal candidate), changed copy breaking an assertion, or a genuine behavior
  regression. Cross-reference the failing step against the diff from Step 1 to localize
  the cause, and propose a fix. For a full artifact-backed diagnosis, hand off to
  `mabl-failure-rca`.
- Optionally suggest `mabl agent debug` for deeper local failure analysis.
- If Step 3 found **no coverage**, flag it as a gap and offer to draft a new mabl test
  for the changed flow.

---

## Step 7 — Emit machine-readable output (loop mode)

So this skill can drive an automated verification loop (and be parsed by a headless
runner), end your response with two contract objects. Prose for the human comes first;
the JSON blocks come last. Full reference: [`docs/loop-contracts.md`](../../docs/loop-contracts.md).

**One `impact` block** — answers Q1 "which tests are affected" + Q2 "which will run":

```json
{
  "schema": "impact",
  "schemaVersion": "1.0",
  "changeRef": "HEAD",
  "changedAreas": ["src/pages/ReportsDashboard.tsx"],
  "inferredFlows": ["Reports dashboard — recent activity card"],
  "affectedTests": [
    {
      "testId": "AbC123-j",
      "name": "Reports Dashboard — Recent Activity",
      "type": "browser",
      "matchStrength": "strong",
      "willRun": true,
      "reason": "direct flow match"
    }
  ],
  "runSet": ["AbC123-j"],
  "coverageZeroMatch": false,
  "workspaceId": "<workspace-id>-w"
}
```

**One `runResult` block per executed test**:

```json
{
  "schema": "runResult",
  "schemaVersion": "1.0",
  "testId": "AbC123-j",
  "testRunId": "XyZ789-jr",
  "status": "passed",
  "failingStep": null,
  "runUrl": "https://app.mabl.com/workspaces/.../runs/XyZ789-jr",
  "billableSkipped": false,
  "target": "http://localhost:3000"
}
```

- `matchStrength`: `strong | partial | tangential`; `status`: `passed | failed | error`.
- Set `impact.coverageZeroMatch: true` when Step 3 found no match — the loop routes
  that to `mabl-coverage-gap`.
- Mark `runResult.billableSkipped: true` for any test whose only red steps were
  GenAI/visual assertions skipped locally — downstream skills must not treat that as
  a code regression.
- Any `runResult` with `status: failed|error` is the handoff to `mabl-failure-rca`.

This section is additive: skip it for a purely interactive, one-off check; always emit
it when invoked as part of `feature-dev` or an automated loop.

---

## Decision defaults (don't ask unless it matters)

- Commit to analyze: `HEAD` (or `--working` when the tree is dirty and the dev server is serving it).
- Tests to run: top **3** by relevance, sequentially.
- Execution: **blocking** (Mode A). Use Mode B (detached + poll) only for `--detached`
  or a job expected to exceed the command timeout.
- Browser: Chrome, headed. Browser closes at run end — never pass `--keep-browser-open`
  in a blocking run, it will hang the turn.
- Run target URL: the **local dev server** — `--url` if given, else detect, else ask.
  Test the deployed mabl environment only if the user explicitly asks.
- Workspace: saved default; prompt + offer to save only on first use.

## Limitations

- Requires the mabl MCP server connected (used for relevance matching). Without it, stop and prompt the user to connect it.
- Mode A publishes results to the mabl cloud via `--reporter mabl`, so each run gets a
  shareable app link + history. Execution is still local (no cloud credits, sequential),
  per the mabl Unified Reporter — the cloud entry is the report, not a cloud execution.
- In Mode B (detached) you can't see the result until you poll the log on a later turn.
- Mobile tests aren't supported for local CLI execution.
