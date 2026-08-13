---
name: feature-dev
description: >-
  End-to-end feature development lifecycle for <YOUR_APP>: plan → build → test →
  ship. Captures the feature as a Kiro spec and a Jira Epic in Atlassian,
  implements and browser-verifies the code change, then establishes mabl test
  coverage (identify existing tests, author new/updated tests via local authoring,
  run locally) before deciding on a PR. Use when the user wants to "build a new
  feature", "plan, build and test a feature", "develop X against an epic", "do
  the full feature workflow", "ship a feature with mabl coverage", or otherwise
  asks to take a feature from idea to PR-ready with Jira + mabl in the loop.
metadata:
  version: "1.0.0"
  host: kiro
  status: template
compatibility: >-
  Requires the mabl CLI on PATH, plus the mabl, Atlassian, and chrome-for-mabl
  MCP servers connected in Kiro. Needs a local dev server and Chrome.
---

<!--
============================================================================
  TEMPLATE — fill this in before use.

  This is a portable, project-agnostic copy of the feature-dev skill for Kiro.
  To adopt it in your own repo:

    1. Replace every <PLACEHOLDER> below (and in the "Project constants"
       table) with your own values. The table's "How to find it" column
       tells you where each comes from.
    2. Review the build/verify commands in Phases 2–3 — swap in your repo's
       actual build, type-check, and dev-server commands.
    3. Generalize or delete any app-specific gotchas at the bottom that
       don't apply to your stack; keep the principles.
    4. Drop the folder into .kiro/skills/feature-dev/ (workspace) or
       ~/.kiro/skills/feature-dev/ (all repos).

  Prerequisites (see README.md): the mabl CLI
  (`npm install -g @mablhq/mabl-cli` + `mabl auth login`) and the `mabl`,
  `Atlassian`, and `chrome-for-mabl` MCP servers in .kiro/settings/mcp.json.
  There is no `mabl agent install kiro` target — add the entries by hand.
============================================================================
-->

# Feature Development Lifecycle (plan → build → test → ship)

A repeatable orchestration for taking a feature from request to PR-ready in this
repo, with a **Kiro spec** + **Atlassian (Jira)** documenting the work and **mabl**
proving it. This skill is a conductor — it composes the focused mabl skills
(`mabl-pre-pr-check`, `mabl-failure-rca`, local authoring) and Kiro's own
spec/build tooling rather than reimplementing them.

Run the phases in order. Each phase gates the next: don't build before the spec
is confirmed, don't author tests before the build is verified, don't open a PR
before triaging the test run.

---

## Project constants (fill these in)

Set these once so steps are zero-prompt. Verify before relying on them if the
environment may have changed. Consider parking this table in a
`.kiro/steering/mabl.md` steering doc (`inclusion: manual`) so other skills and
chats can pull it in with `#mabl`.

| Thing | Value | How to find it |
|-------|-------|----------------|
| Atlassian cloudId | `<ATLASSIAN_CLOUD_ID>` (site `<your-site>.atlassian.net`) | Atlassian MCP `getAccessibleAtlassianResources` |
| Default Jira project | `<PROJECT_NAME>` — key `<KEY>` (Epic issue type id `<EPIC_TYPE_ID>`) — confirm with the user; they may name another project/"space" | Atlassian MCP `getVisibleJiraProjects` / `getJiraProjectIssueTypesMetadata` |
| mabl workspace | `<WORKSPACE_NAME>` — `<WORKSPACE_ID>` | `mabl auth info`, or the mabl app URL `…/workspaces/<id>/…`, or mabl-MCP `list_mabl_workspaces` |
| mabl applicationId | `<APPLICATION_ID>` | mabl-MCP `list_mabl_applications`, or the mabl app |
| mabl environment (local) | `<ENV_NAME>` — `<ENVIRONMENT_ID>` | mabl-MCP `list_mabl_environments` |
| mabl credentials ids | `<CRED_NAME>` — `<CREDENTIALS_ID>` (one per persona; note which is admin) | mabl-MCP `list_mabl_credentials` |
| Local dev server | `<LOCAL_URL>` (e.g. `http://localhost:3000`; start with `<DEV_SERVER_COMMAND>`) | your app |
| Test creds | `<USERNAME>` / `<PASSWORD>` (per persona) | your app |

> Throughout the steps below, `<LOCAL_URL>` means the local dev-server URL above.
> Repo-wide conventions (stack, commands, structure, testing notes) live in
> `.kiro/steering/` — read them before planning.

---

## Phase 1 — Plan (spec + epic)

1. **Explore** the codebase to ground the change. Find the components, types,
   API/controllers, and styles involved; prefer reusing existing utilities.
2. **Create a Kiro spec** at `.kiro/specs/<feature-slug>/`. This is the Kiro-native
   home for the plan and the thing you execute against in Phase 2:
   - `requirements.md` — user stories plus **EARS-style acceptance criteria**
     (`WHEN <trigger> THE SYSTEM SHALL <response>`). These become the mabl
     assertions in Phase 3, so write them as observable browser behavior, not
     internals.
   - `design.md` — the components/routes/endpoints touched, data flow, and the
     selectors (`data-testid`) the feature will expose. **Name the test ids here** —
     Phase 3 authoring is dramatically more reliable when it's handed literal
     selectors instead of intent (see gotchas).
   - `tasks.md` — the discrete implementation steps, as a checklist.
3. **Create a Jira Epic** in the target project to document the feature, using
   `createJiraIssue` (Atlassian MCP). Include a **Context**, **Goal**, and
   **Acceptance Criteria** (lift the EARS criteria from `requirements.md`) in the
   description; `contentFormat: "markdown"` is simplest. Link the spec path in the
   description so the two stay associated. Capture the returned issue **key + URL**
   (e.g. `<KEY>-NN`) — it threads through the commit message and PR later.
   - Confirm the project first: the user's "space" usually means a Jira project.
     Resolve it with `getVisibleJiraProjects` (searchString) if unsure.
   - Epic only by default; create child stories/tasks only if the user asks.
   - (No Jira? Skip this — the spec alone documents the intent — and reference the
     feature directly in the commit/PR.)
4. **Confirm scope** with the user before writing code — present the requirements
   and ask about any real fork (item counts, naming, test-id changes, etc.).
   Don't start Phase 2 until the spec is approved.
5. **Settle the GenAI/billable question now — not at Phase 4.** Ask whether local
   runs should pass `--allow-billable-features`. This is a known property of the
   suite, knowable before a single test runs, and the wrong moment to raise it is
   after two tests have already printed `FAILED` while being green.

## Phase 2 — Build (implement + browser-verify)

1. **Implement** the change by working through `tasks.md`, checking items off as
   you go. Match surrounding code style. Reuse existing helpers (your shared
   formatting/util modules). Keep the diff tight.
2. **Build / type-check**: run your repo's build + type-check command
   (`<BUILD_COMMAND>`). Fix any errors before proceeding.
3. **Verify in the real app**, not just tests, with the `chrome-for-mabl` MCP:
   - Ensure dev servers are up (`curl -s -o /dev/null -w "%{http_code}"
     <LOCAL_URL>`). If Chrome isn't attached, launch one with a debug port into a
     scratch user-data-dir (path is OS-specific; macOS example):
     `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
     --remote-debugging-port=9222 --user-data-dir="$HOME/.kiro/tmp/chrome-debug"
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
2. **Author the coverage gap** — use mabl **local** authoring against `<LOCAL_URL>`,
   feeding it the selectors you named in `design.md`:
   - **Edit** tests that a rename/refactor broke: pass `{test_id, url_override,
     test_case}` describing the exact selector/text changes.
   - **Create** a test for net-new behavior: `{name, url_override,
     application_id, test_case}` with explicit, stable selectors.
   - Run `mabl agent authoring initiate ... --mode local --headless --auto-save
     --verbose`. ⚠️ **Kiro blocks on foreground commands and a create session can
     take 30–45 minutes** — launch it **detached** and poll on a later turn:
     ```bash
     A_DIR="$HOME/.kiro/tmp/mabl-authoring"; mkdir -p "$A_DIR"
     nohup mabl agent authoring initiate ... --mode local --headless --auto-save --verbose \
       > "$A_DIR/authoring.log" 2>&1 &
     echo "started pid $!"
     ```
     Poll with `awk 'length($0) < 300' "$A_DIR/authoring.log" | tail -n 40` and
     `pgrep -fl "mabl agent authoring"`. Logs are huge — filter by line length
     **before** grepping for `createdTestId` / `Test saved` / `Generated Steps`.
   - Fix stale **metadata** (name/description) afterward with
     `edit_mabl_test_metadata` if the authoring agent only updated steps.
3. **Resolve credentials BEFORE the first run — this is a pre-flight step, not a
   triage step.** For each test you're about to run, read its login flow / landing
   assertion and pick the matching credential, then pass `--credentials-id`. Look
   ids up with `list_mabl_credentials`.
   - Skipping this wastes a whole round: a run with `Credentials: None` resolves
     the default username to nothing and the login flow executes with a literal
     placeholder string. The test then fails *downstream* — "Element not found" on
     a nav link, or an empty landing assertion — which reads exactly like a
     regression in your diff.
4. **Run existing + new tests locally.** One test per `mabl tests run --id <id> -w
   <WORKSPACE_ID> --url <LOCAL_URL> --application-id <APPLICATION_ID>
   --environment-id <ENVIRONMENT_ID> --credentials-id <CREDENTIALS_ID>
   --reporter mabl [--allow-billable-features]`. Run sequentially (shared dev
   server), in the **foreground** — a browser test is 1–5 min, well within a normal
   command execution, and Kiro hands you the output directly. Do **not** pass
   `--keep-browser-open` (the command would never return and the turn would hang).
5. **Triage** — parse `run.log` `Passed:`/`Failed:` (exit code alone is
   unreliable) and confirm via `list_mabl_test_runs` / `get_mabl_test_run`. For
   each failure, separate a **code regression** (cross-reference the failing step
   against the diff) from a **test/harness issue** (brittle assertion, GenAI skip,
   stale selector, data).
   - **Don't conclude root cause from headless re-runs alone.** A headless
     `mabl tests run` reports terse, sometimes misleading errors (e.g.
     "Element not found" can really mean *the element was filtered out by app
     state*, or a heal timed out). Re-running headless with tweaked inputs
     only changes *which* symptom you see — it rarely isolates the cause.
   - **Triage with a live step-through — the fastest, most reliable way to assign
     blame, and the default triage tool for this workflow.** Start a live session
     against local (`mabl agent debug session start <test-id> --credentials-id
     <CREDENTIALS_ID> --environment-id <ENVIRONMENT_ID> --url <LOCAL_URL>`, or
     `--run-id <jr>` if you have a failed run), `list-steps` to get addressable
     ids, `run-to-step` to just before the failure, inspect the real page with
     `chrome-for-mabl` (`take_snapshot`/`take_screenshot`), then `run-step` on the
     failing step. Whether the step **passes or stops** tells you definitively
     whether your diff broke it — e.g. if a click step *advances past itself*, the
     selector still works and a later step (often a GenAI assert) is the real red.
     The same session reproduces and verifies the fix (`set-current-step` →
     `run-step` → `run-all`), so prefer it over re-running headless. Re-run the
     full local test after fixes to confirm.
   - For a deeper artifact-backed code-vs-test call, invoke **`mabl-failure-rca`**
     to classify the failure (product / stale-test / env-data / flake) against the
     source and point at the exact line.

## Phase 4 — Ship (PR decision)

Only after triage. **First run `analyze_mabl_failure` on every failed run** so a
saved failure analysis exists for each — otherwise `check_release_readiness` scores
those runs "unknown root cause" and drags the readiness score down for no real
reason. Then, if green — or the only reds are confirmed non-code (test-tooling /
pre-existing / unrelated) — summarize and, on the user's go, commit on the feature
branch referencing the Epic key and open the PR (body ends with any required
trailers your repo uses). Otherwise, fix and re-run. The PR decision is the
user's — recommend, don't assume.

Mark the spec's `tasks.md` complete and, if the user wants Jira kept in sync,
transition the Epic (`transitionJiraIssue`) and comment the PR link
(`addCommentToJiraIssue`).

---

## Gotchas & lessons (baked in from real runs)

- **GenAI/visual assertions auto-skip in local CLI runs.** They fail with "AI
  assertions are not available" unless you pass `--allow-billable-features`
  (consumes mabl credits — confirm with the user first). A test whose *only*
  real assertion is GenAI is meaningless locally without the flag. When every
  concrete (DOM) assertion passed and the *only* red is a GenAI/visual step, the
  test is effectively green — say so explicitly; don't report it as FAILED.
- **Dynamic / time-sensitive text is brittle to assert on.** Greetings,
  timestamps, relative dates, and randomized values change between runs. Never
  let an authored test assert the full dynamic string — confirm success on a
  **stable element** (the app shell, the user's name, a nav link), or match only
  a stable substring.
- **Local authoring saves to an "Agent edit session" branch, not `master`.** After
  `mabl agent authoring initiate --mode local` edits a test, the new version lands on
  a side branch — but `mabl tests run --id` executes the **master** tip, so a verify
  re-run still uses the OLD steps and "fails." Promote first: `list_mabl_test_versions`
  → `restore_mabl_test(version=<new>)` to make it the master latest, **then** re-run.
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
  (a debug live session or a `chrome-for-mabl` snapshot) and reset the
  precondition (undo the prior state / pick a guaranteed-available item). Tests
  that assume a clean starting state are pre-existing fragility, not your
  regression.
- **A live step-through beats guesswork for code-vs-test calls.** In real runs,
  headless has reported "Element not found" on a click that the live debug session
  then showed *passing* (the run advanced to the next step) — the actual red being
  a downstream GenAI assertion disabled locally. Headless alone would have
  mislabeled a harness limitation as a selector regression. When in doubt, step
  through it.
- **The right local-run credentials depend on what the test asserts.** Many apps
  render the same page differently per persona (e.g. an admin vs. a standard
  user see different landing titles and nav items). If a test's
  assertions/selectors were authored for one persona, run it with that persona's
  credentials id via `--credentials-id` — a local run won't pick the right one
  on its own. Look up ids with `list_mabl_credentials` (note which creds are
  cloud-only and can't run locally).
- **`--reporter mabl`** publishes a shareable cloud run + history while executing
  locally (no cloud credits for execution); resolve `--application-id` and
  `--environment-id` so the published run associates correctly.
- **Know your app's nav element type.** Tests should target the right role —
  e.g. link-based navigation (`<a>`/router links) must be targeted as links, not
  buttons. Check how your app renders nav before authoring selectors.
- **Kiro blocks on foreground commands; there is no background-completion
  notification.** Short jobs (a test run) go in the foreground and you read the
  output directly. Long jobs (authoring sessions) must be `nohup`-detached and
  polled on a later turn. Don't busy-wait inside a single turn.
- **Budget local authoring at 30–45 min, not the documented 5–20.** Measured on a
  real app: a 9-group create session took **44 min** (`--mode local --headless`),
  a one-step *edit* session took **7 min**. For a **demo** this is dead air —
  pre-author the test beforehand and demo the *run*, or state the wait up front.
- **Never `grep` an authoring/run log raw — filter by line length first.** These
  logs embed base64 screenshot payloads; a naive grep can dump hundreds of KB into
  context. Always pipe through `awk 'length($0) < 300'` before grepping.
- **One feature per branch, and verify the baseline survives the cut.** A branch
  carrying unrelated commits or another feature's uncommitted work makes the ship
  step ambiguous and makes impact analysis harder. After cutting a branch, check:
  - **Skills.** Install these at `~/.kiro/skills/` rather than relying on a
    committed `.kiro/skills/` copy, so cutting a fresh branch can't delete them
    mid-run and leave every skill resolving as unknown.
  - **Features under test.** `git log main..<other-branch> --oneline` before
    assuming a red test is your fault. A mabl test authored during earlier work
    asserts *that* feature, which may not exist on your branch. Exclude such tests
    explicitly and say why; don't debug them as regressions.
- **For visual features, a rendered screenshot is not optional.** DOM-text
  assertions pass against a visually broken build — e.g. a chart label present in
  the DOM but positioned off-canvas is invisible yet "asserted." Browser-verify
  with a screenshot in Phase 2; don't rely on the mabl test's DOM checks to catch
  positioning/layout bugs.
- **A/B a suspected regression instead of reasoning about it.** To decide whether
  your diff caused a failing step, toggle just your change (comment it out) and
  re-run the test. Identical failure at the identical step → pre-existing, not your
  regression. Cheaper and more conclusive than argument (~90s).
- **Read every conditional branch in a generated test by hand — an untaken branch
  is unvalidated code.** The authoring agent reports success and the validation run
  goes green based only on the paths it *executed*. An `IF` whose condition was
  false during authoring was never run, so a wrong step inside it ships silently.
  Two mitigations, both cheap:
  - **Demand literal selectors for conditional actions.** Agents get steps right
    where the spec gives an exact selector (`button[aria-label="Remove X"]`) and
    invent wrong ones where the spec describes *intent* ("un-track X"). Describing
    intent is where they guess. This is exactly why Phase 1 puts the `data-testid`s
    in `design.md`.
  - **After authoring, diff intent vs. generated steps for each `IF` body
    specifically** before trusting the test — then promote and re-run.
- **Give the authoring agent explicit *negative* constraints.** Naming the traps up
  front yields a test that passes first try and survives re-runs: *do NOT assert
  time-of-day greetings*; *do NOT use GenAI/visual assertions* (so it's green in
  local CLI); *do NOT assert exact values* that are randomized per request — assert
  **format and counts** instead; *use only `data-testid`/stable class selectors*,
  never generated ids or pixel coordinates. Count-based asserts (e.g.
  `bar_count == 7`) are strong regression sentinels but couple the test to seed
  data — prefer them over `> 0` only when the seed is stable, and flag the coupling.
