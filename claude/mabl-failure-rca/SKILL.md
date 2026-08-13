---
name: mabl-failure-rca
description: >-
  Root-cause a failed mabl test run against the source code. Pulls mabl's AI
  failure analysis, downloads supporting artifacts (DOM snapshots, HAR/network,
  console logs, screenshots) via the mabl CLI + MCP, correlates them with the
  app's source, and produces a root-cause report that classifies the failure
  (product regression vs stale test vs env/data vs flake) and points to the exact
  code. Use when the user says "why did this mabl test fail", "root cause this
  failed run", "debug this mabl failure in the code", "triage this mabl test run",
  or pastes a mabl test-run link/ID and wants the underlying cause.
---

# mabl Failure RCA

Close the loop from a red mabl run to the line of code behind it. This skill gathers
mabl's own failure evidence, pulls the heavy artifacts (DOM, HAR, console, screenshots),
and reasons about them **against the application source** to deliver a verdict and a fix —
not just "it failed at step 7."

The flow: **resolve run → pull AI analysis → pull artifacts → correlate with source → classify + report.**

---

## When to use

- A mabl test (or a test inside a plan run) failed and someone needs to know *why* and *what to change*.
- Triaging a CI/deployment failure that surfaced in mabl, before assigning a bug.
- Deciding whether a red run is a real regression, a test that needs updating, or environmental noise.

Not for: authoring tests (`mabl-test-from-requirement`), or running tests (`mabl-pre-pr-check`).

---

## Inputs

| Input | Meaning |
|-------|---------|
| run reference | A test-run id (`-jr`), a mabl run URL, a test id (`-j`), a test name, or a plan-run id (`-pr`). If omitted, offer to use the latest failed run for a named test. |
| `--workspace <name\|id>` | Target workspace (else saved default / ask). |
| `--repo <path>` | Source repo to correlate against (default: current working directory). |
| `--rev <ref>` | Git revision the app-under-test was built from, if known — analyze against it. Default: current checkout, noted as an assumption. |
| `--artifacts <list>` | Which artifacts to export (default: `doms hars console_logs screenshots`). |
| `--fix` | After diagnosing, propose/apply a concrete fix. Default: diagnose only, then offer. |

---

## Step 0 — Preflight

1. **CLI + auth:** `mabl --version && mabl auth info`. Missing → `npm install -g @mablhq/mabl-cli`; expired → `mabl auth login`. Stop on failure.
2. **mabl MCP required** — this skill uses `analyze_failure`, `get_test_run_artifact`, etc. If the `mcp__mabl__*` tools aren't present, stop and ask the user to connect the mabl MCP server (`mabl agent install <target>`).
3. **Workspace:** resolve once (named arg → `get_workspaces`; else `mabl config get workspace-id`; else ask).
4. **Source repo:** confirm `--repo` (or cwd) is the app under test (`git rev-parse --is-inside-work-tree`). Sanity-check it's the right app (package name / known routes) before correlating — RCA against the wrong repo is worse than none.
5. **AI entitlement caveat:** `analyze_failure` / result-analysis chat require the workspace's AI features to be on. You can't know until you call; if it returns `analysis_unavailable`, fall back to artifacts + step data and say AI analysis was unavailable.

---

## Step 1 — Resolve to a concrete failed test run

End state: a single failed **testRunId (`-jr`)** in a known workspace.

- Given a `-jr` → use it directly.
- Given a mabl URL → extract the run id from it.
- Given a test id (`-j`) or test name → `get_latest_test_runs(testId, workspaceId)`; pick the most recent `failed` run (confirm with the user if several).
- Given a plan run (`-pr`) → `get_plan_run_result(planRunId, workspaceId)`, list the failed test runs, and pick (or ask which) to drill into. RCA one failing test run at a time.

Record the `testRunId`, test name, environment, and completion time.

---

## Step 2 — Pull mabl's AI failure analysis

1. **Failure record:** `analyze_failure(runId=<testRunId>, testOrPlan='test', workspaceId, includeEvidence: true)`.
   Capture the **synopsis**, **Root cause** + **Next steps** markdown, and the **evidenceDetails**
   (it contains the `gs://` artifact URIs and any historical trend / cross-run data). This is your spine.
2. **Auto-heal?** If the synopsis/evidence mentions the Runtime Recovery Agent, healing, or a resumed
   step, call `get_runtime_recovery_session(testRunId, workspaceId)` to see what it changed — a run
   that "passed via healing" often signals selector drift worth fixing at the source.
3. **History / "since green" (optional but valuable):** `mabl_result_analysis_chat(entity='test_run',
   targetId=<testRunId>, workspaceId, initialUserMessage='What changed since this test last passed?')`
   to learn when it started failing — that window scopes the suspect commits in Step 4.

Note the **failing step**, the **assertion** (expected vs actual), and the **target** (selector /
URL / network request) — these drive everything downstream.

---

## Step 3 — Pull the supporting artifacts

Two complementary paths — use both as needed:

**A. Inline, surgical (MCP).** For the specific artifacts named in `evidenceDetails`, call
`get_test_run_artifact(artifactUri, workspaceId)`:
- **Screenshot** at the failing step → returns inline PNG; look at the rendered state.
- **DOM snapshot** at the failing step → confirm whether the expected element is present/changed.
- **Console logs** → JS exceptions around the failure.
- **HAR** → the network request(s) at the failure (status, payload, response).
Never surface raw `gs://` URLs to the user.

**B. Bulk, local (CLI).** To grep/diff artifacts at scale, export to disk:
```bash
RCA_DIR="$(mktemp -d)/mabl-rca"; mkdir -p "$RCA_DIR"
mabl test-runs export <testRunId> --types doms hars console_logs screenshots --file "$RCA_DIR/run"
# (use --types all for everything; traces/variables/xray_json also available)
```
Then inspect locally: open the DOM snapshot for the failing step, scan the HAR for non-2xx
responses or wrong payloads, read console logs for stack traces. Record `$RCA_DIR`.

Build a tight **evidence set**: for the failing step, what the screenshot shows, whether the DOM
contains the target, the relevant network exchange, and any console error.

---

## Step 4 — Correlate with the source code

This is the core. Map each piece of evidence to the application source in `--repo`.

- **Selector / element target** (failing find or assertion): grep the front-end for the
  `data-testid`, label text, `aria-label`, role, or `id` the test targeted.
  - Present but changed (renamed/moved/text changed) → likely a **stale test** / intentional UI change.
  - Absent / conditionally rendered → trace the component: is it gated, error-state, or removed?
- **Network failure** (from HAR — 4xx/5xx, wrong shape): map the request path to the API route /
  controller in the source; read the handler. A 500 or changed contract points at a **product bug**.
- **Console exception:** map the stack/file to source; a thrown error mid-render explains a missing element.
- **DOM vs expectation:** if the DOM shows an empty/error state where data was expected, follow the
  data path (component → fetch → endpoint) to find where it broke.
- **Blame the window:** using the "since green" window from Step 2, `git log --oneline <lastGreen>..<rev>`
  on the implicated files and `git blame` the suspect lines to surface the likely culprit commit(s).
  If `--rev` was given, analyze at that revision; otherwise note you're analyzing the current checkout.

---

## Step 5 — Classify & report

Deliver a **root-cause report**:

1. **Verdict** (one, with confidence): 
   - **Product regression** — app code broke a real behavior → fix the app.
   - **Stale test / intentional change** — UI/contract changed on purpose → update the test (flag as auto-heal candidate if a selector moved).
   - **Environment / data** — seed data, creds, config, or a down dependency (e.g. empty state, 503).
   - **Flaky / timing** — race or missing wait; corroborate with recovery session + historical pass rate.
2. **Failing step & assertion** — expected vs actual, in plain terms.
3. **Evidence trail** — each conclusion tied to its artifact ("DOM at step 7 has no `[data-testid=recent-deposits]`; HAR shows `GET /users/3/transactions → 500`; console: `TypeError …`").
4. **Pinpointed cause** — `file:line` in the repo, and the likely culprit commit(s).
5. **Recommended fix** — a concrete code change (sketch the diff) for a product bug, or the test update
   for a stale selector. With `--fix`, apply it (code edit) and offer to verify via `mabl-pre-pr-check`.
6. **Links** — the mabl run and (if used) the result-analysis session, so the user can open the full evidence.

Then clean up the export dir if you created one and the user doesn't want it kept.

---

## Decision defaults (don't ask unless it matters)

- Run: the one referenced; if only a test was named, the latest `failed` run (confirm if ambiguous).
- Artifacts: `doms hars console_logs screenshots` (add `traces`/`variables` when the failure is timing/state-related).
- Repo: current working directory; revision: current checkout (state the assumption).
- Mode: **diagnose only**, then offer a fix. Apply automatically only with `--fix`.
- Workspace: saved default; prompt + offer to save on first use.

## Limitations

- AI failure analysis (`analyze_failure`, result-analysis chat) requires the workspace's AI features
  to be enabled; otherwise rely on artifacts + step data and say so.
- Video and email artifacts, and internal support logs, are not exposed to agents (`access_restricted`).
- RCA quality depends on the repo matching the app under test — ideally at the revision the run
  executed against. If you can't confirm the revision, say the analysis is against the current checkout.
- Correlation is evidence-based reasoning, not proof — present confidence and the trail, and verify a
  proposed fix (e.g. re-run the test locally with `mabl-pre-pr-check`) before calling it closed.
