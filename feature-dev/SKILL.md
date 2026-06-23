---
name: feature-dev
description: >-
  End-to-end feature development lifecycle for <YOUR_APP>: plan → build → test →
  ship. Documents the feature as a Jira Epic in Atlassian, implements and
  browser-verifies the code change, then establishes mabl test coverage
  (identify existing tests, author new/updated tests via local authoring, run
  locally) before deciding on a PR. Use when the user wants to "build a new
  feature", "plan, build and test a feature", "develop X against an epic", "do
  the full feature workflow", "ship a feature with mabl coverage", or otherwise
  asks to take a feature from idea to PR-ready with Jira + mabl in the loop.
---

<!--
============================================================================
  TEMPLATE — fill this in before use.

  This is a portable, project-agnostic copy of the feature-dev skill. To
  adopt it in your own repo:

    1. Replace every <PLACEHOLDER> below (and in the "Project constants"
       table) with your own values. The table's "How to find it" column
       tells you where each comes from.
    2. Review the build/verify commands in Phases 2–3 — swap in your repo's
       actual build, type-check, and dev-server commands.
    3. Generalize or delete any app-specific gotchas at the bottom that
       don't apply to your stack; keep the principles.
    4. Rename this file to SKILL.md (replacing the project-specific one) so
       Claude Code loads it, and update README.md accordingly.

  Prerequisites (see README.md for details): the mabl CLI
  (`npm install -g @mablhq/mabl-cli` + `mabl auth login`) and the mabl
  agent tooling (`mabl agent install claude`), which installs the
  `mabl-debug` skill plus the `chrome-for-mabl` and `mabl` MCP servers.
============================================================================
-->

# Feature Development Lifecycle (plan → build → test → ship)

A repeatable orchestration for taking a feature from request to PR-ready in this
repo, with **Atlassian (Jira)** documenting the work and **mabl** proving it.
This skill is a conductor — it composes the focused mabl skills
(`mabl-pre-pr-check`, `mabl-plan-test`/local authoring, and `mabl-debug` for
triage via live step-through isolation) and the standard plan/build tools
rather than reimplementing them.

Run the phases in order. Each phase gates the next: don't build before the plan
is confirmed, don't author tests before the build is verified, don't open a PR
before triaging the test run.

---

## Project constants (fill these in)

Set these once so steps are zero-prompt. Verify before relying on them if the
environment may have changed.

| Thing | Value | How to find it |
|-------|-------|----------------|
| Atlassian cloudId | `<ATLASSIAN_CLOUD_ID>` (site `<your-site>.atlassian.net`) | Atlassian MCP `getAccessibleAtlassianResources` |
| Default Jira project | `<PROJECT_NAME>` — key `<KEY>` (Epic issue type id `<EPIC_TYPE_ID>`) — confirm with the user; they may name another project/"space" | Atlassian MCP `getVisibleJiraProjects` / `getJiraProjectIssueTypesMetadata` |
| mabl workspace | `<WORKSPACE_NAME>` — `<WORKSPACE_ID>` | `mabl auth info`, or the mabl app URL `…/workspaces/<id>/…`, or `mabl`-MCP `get_workspaces` |
| mabl applicationId | `<APPLICATION_ID>` | `mabl`-MCP `get_applications`, or the mabl app |
| mabl environment (local) | `<ENV_NAME>` — `<ENVIRONMENT_ID>` | `mabl`-MCP `get_environments` |
| mabl credentials ids | `<CRED_NAME>` — `<CREDENTIALS_ID>` (one per persona; note which is admin) | `mabl`-MCP `get_credentials` |
| Local dev server | `<LOCAL_URL>` (e.g. `http://localhost:3000`; start with `<DEV_SERVER_COMMAND>`) | your app |
| Test creds | `<USERNAME>` / `<PASSWORD>` (per persona) | your app |

> Throughout the steps below, `<LOCAL_URL>` means the local dev-server URL above.

---

## Phase 1 — Plan (document the intent)

1. **Explore** the codebase to ground the change (use the Explore/Plan agents,
   or `/plan` if the user invoked plan mode). Find the components, types,
   API/controllers, and styles involved; prefer reusing existing utilities.
2. **Create a Jira Epic** in the target project to document the feature, using
   `createJiraIssue` (Atlassian MCP). Include a **Context**, **Goal**, and
   **Acceptance Criteria** (bullet list) in the description; `contentFormat:
   "markdown"` is simplest. Capture the returned issue **key + URL** (e.g.
   `<KEY>-NN`) — it threads through the commit message and PR later.
   - Confirm the project first: the user's "space" usually means a Jira project.
     Resolve it with `getVisibleJiraProjects` (searchString) if unsure.
   - Epic only by default; create child stories/tasks only if the user asks.
   - (No Jira? Skip this and reference the feature directly in the commit/PR.)
3. **Confirm scope** with the user via `AskUserQuestion` for any real fork
   (item counts, naming, test-id changes, etc.). Write the plan to the plan file
   if in plan mode and exit via `ExitPlanMode`.

## Phase 2 — Build (implement + browser-verify)

1. **Implement** the change per the plan. Match surrounding code style. Reuse
   existing helpers (your shared formatting/util modules). Keep the diff tight.
2. **Build / type-check**: run your repo's build + type-check command
   (`<BUILD_COMMAND>`). Fix any errors before proceeding.
3. **Verify in the real app**, not just tests, with the `chrome-for-mabl` MCP:
   - Ensure dev servers are up (`curl -s -o /dev/null -w "%{http_code}"
     <LOCAL_URL>`). If Chrome isn't attached, launch one with a debug port into a
     scratch user-data-dir (path is OS-specific; macOS example):
     `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
     --remote-debugging-port=9222 --user-data-dir=<scratchpad>/chrome-debug
     --no-first-run --no-default-browser-check about:blank &`
   - `new_page` → `<LOCAL_URL>`, log in (`fill_form` + `click`), navigate to
     the changed view, `take_snapshot` to assert content, `take_screenshot` to
     show the user. Clean up the debug Chrome (`pkill -f chrome-debug`) when done.

## Phase 3 — Test (mabl coverage)

1. **Identify existing coverage** — invoke **`mabl-pre-pr-check`** (or directly
   `search_mabl_tests` in the workspace) to map the diff to existing tests.
   Classify each: direct hit (likely needs updating for renames), partial
   (regression smoke), or tangential/prod-bound (exclude from local run).
   Tests bound to a deployed URL still run locally via `--url`.
2. **Author the coverage gap** — invoke **`mabl-plan-test`** with **local**
   authoring against `<LOCAL_URL>`:
   - **Edit** tests that a rename/refactor broke: pass `{test_id, url_override,
     test_case}` describing the exact selector/text changes.
   - **Create** a test for net-new behavior: `{name, url_override,
     application_id, test_case}` with explicit, stable selectors.
   - Run with `mabl agent authoring initiate ... --mode local --headless
     --auto-save --verbose` as a **background** process; the harness notifies you
     on completion. Logs are huge — `grep` for `createdTestId` / `Test saved` /
     `Generated Steps`.
   - Fix stale **metadata** (name/description) afterward with `edit_mabl_test`
     if the authoring agent only updated steps.
3. **Run existing + new tests locally** (background, publishes to cloud). One
   test per `mabl tests run --id <id> -w <WORKSPACE_ID> --url <LOCAL_URL>
   --application-id <APPLICATION_ID> --environment-id <ENVIRONMENT_ID>
   --reporter mabl [--allow-billable-features]`. Run sequentially (shared dev
   server). Do **not** pass `--keep-browser-open` in background (it blocks exit).
4. **Triage** — parse `run.log` `Passed:`/`Failed:` (exit code alone is
   unreliable) and confirm via `get_latest_test_runs`. For each failure,
   separate a **code regression** (cross-reference the failing step against the
   diff) from a **test/harness issue** (brittle assertion, GenAI skip, stale
   selector, data).
   - **Don't conclude root cause from headless re-runs alone.** A headless
     `mabl tests run` reports terse, sometimes misleading errors (e.g.
     "Element not found" can really mean *the element was filtered out by app
     state*, or a heal timed out). Re-running headless with tweaked inputs
     only changes *which* symptom you see — it rarely isolates the cause.
   - **Triage with `mabl-debug` — a live step-through is the fastest, most
     reliable way to assign blame, and is the default triage tool for this
     workflow.** Start a live session against local
     (`mabl agent debug session start <test-id> --credentials-id <CREDENTIALS_ID>
     --environment-id <ENVIRONMENT_ID> --url <LOCAL_URL>`, or `--run-id <jr>` if
     you have a failed run), `list-steps` to get addressable ids, `run-to-step`
     to just before the failure, inspect the real page with `chrome-for-mabl`
     (`take_snapshot`/`take_screenshot`), then `run-step` on the failing step.
     Whether the step **passes or stops** tells you definitively whether your
     diff broke it — e.g. if a click step *advances past itself*, the selector
     still works and a later step (often a GenAI assert) is the real red.
     `mabl-debug` also reproduces and verifies the fix in the same session
     (`set-current-step` → `run-step` → `run-all`), so prefer it over re-running
     headless. Re-run the full local test after fixes to confirm.

## Phase 4 — Ship (PR decision)

Only after triage. If green — or the only reds are confirmed non-code
(test-tooling / pre-existing / unrelated) — summarize and, on the user's go,
commit on the feature branch referencing the Epic key and open the PR (body ends
with any required Co-Authored-By / Generated-with trailers your repo uses).
Otherwise, fix and re-run. The PR decision is the user's — recommend, don't
assume.

---

## Gotchas & lessons (baked in from real runs)

- **GenAI/visual assertions auto-skip in local CLI runs.** They fail with "AI
  assertions are not available" unless you pass `--allow-billable-features`
  (consumes mabl credits — confirm with the user first). A test whose *only*
  real assertion is GenAI is meaningless locally without the flag.
- **Dynamic / time-sensitive text is brittle to assert on.** Greetings,
  timestamps, relative dates, and randomized values change between runs. Never
  let an authored test assert the full dynamic string — confirm success on a
  **stable element** (the app shell, the user's name, a nav link), or match only
  a stable substring.
- **Local authoring may not persist edits to existing "Count elements" steps.**
  Observed repeatedly: the CLI reports new steps + "validated 100%", but
  `mabl tests run` still executes the old step/selectors. If a re-run shows the
  pre-edit selectors, edit the step **in the mabl app UI** (those edits persist
  reliably) and re-run, rather than re-looping the CLI.
- **Renames break selector-based tests.** A `data-testid` / class / heading
  rename will fail any test asserting the old value — update those tests as part
  of the change (that's coverage maintenance, not a regression).
- **"Element not found" is often test *state*, not a missing element.** Views
  that filter by state hide their own controls — e.g. a list that drops items
  already in some other list won't render the control to add them again. So an
  "add X" step can fail with "Element not found" simply because X is already in
  the target state for that user. Before blaming the diff, check the live page
  (`mabl-debug` live session or a `chrome-for-mabl` snapshot) and reset the
  precondition (undo the prior state / pick a guaranteed-available item). Tests
  that assume a clean starting state are pre-existing fragility, not your
  regression.
- **A live step-through beats guesswork for code-vs-test calls.** In real runs,
  headless has reported "Element not found" on a click that the `mabl-debug`
  live session then showed *passing* (the run advanced to the next step) — the
  actual red being a downstream GenAI assertion disabled locally. Headless alone
  would have mislabeled a harness limitation as a selector regression. When in
  doubt, step through it.
- **The right local-run credentials depend on what the test asserts.** Many apps
  render the same page differently per persona (e.g. an admin vs. a standard
  user see different landing titles and nav items). If a test's
  assertions/selectors were authored for one persona, run it with that persona's
  credentials id via `--credentials-id` — a local run won't pick the right one
  on its own. Look up ids with `get_credentials` (note which creds are
  cloud-only and can't run locally).
- **`--reporter mabl`** publishes a shareable cloud run + history while executing
  locally (no cloud credits for execution); resolve `--application-id` and
  `--environment-id` so the published run associates correctly.
- **Know your app's nav element type.** Tests should target the right role —
  e.g. link-based navigation (`<a>`/router links) must be targeted as links, not
  buttons. Check how your app renders nav before authoring selectors.
- **Background everything long-running** (authoring sessions, test runs) and let
  the harness re-invoke you on completion; don't foreground-block or poll.
