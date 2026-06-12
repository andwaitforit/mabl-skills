# mabl-failure-rca — Claude Code skill

Turns a **failed mabl test run** into a **root-cause report against your source code**. It pulls
mabl's AI failure analysis, downloads the supporting artifacts (DOM snapshots, HAR/network,
console logs, screenshots), correlates them with the app's code, and tells you *why* it failed and
*what to change* — classifying the failure as a product regression, a stale test, an env/data
issue, or a flake.

## Prerequisites

- **mabl CLI** installed & authenticated (`mabl --version && mabl auth info`).
- **mabl MCP server** connected — the skill uses `analyze_failure`, `get_test_run_artifact`,
  result-analysis chat, and recovery-session tools.
- The **source repo** of the app under test, checked out locally (ideally at the revision the run
  executed against).
- **Workspace AI features** enabled for full AI failure analysis — without them, the skill falls
  back to raw artifacts + step data and says so.

## Usage

```
/mabl-failure-rca <test-run-id|mabl-run-url|test-name>
/mabl-failure-rca abc123-jr --repo . --fix
/mabl-failure-rca "Portfolio: Recent Deposits card" --workspace "Demo Bank"
```

| Input / Arg | Meaning |
|---|---|
| run reference | Test-run id (`-jr`), mabl run URL, test id (`-j`), test name, or plan-run id (`-pr`) |
| `--workspace <name\|id>` | Target workspace (else saved default / ask) |
| `--repo <path>` | Source repo to correlate against (default: cwd) |
| `--rev <ref>` | Git revision the app-under-test was built from, if known |
| `--artifacts <list>` | Artifacts to export (default: `doms hars console_logs screenshots`; `all` for everything) |
| `--fix` | Propose/apply a fix after diagnosing (default: diagnose, then offer) |

## What it produces

A root-cause report with: a **verdict** (regression / stale test / env-data / flake) and confidence,
the **failing step & assertion** (expected vs actual), an **evidence trail** tying each conclusion to
an artifact, the **pinpointed `file:line`** and likely culprit commit(s), and a **recommended fix** —
plus links to the mabl run and analysis session.

## How it works

1. **Resolve** the input to a concrete failed `testRunId`.
2. **Pull AI analysis** — `analyze_failure` (synopsis, root cause, evidence URIs); recovery session if
   auto-heal engaged; "since last green" via result-analysis chat to scope suspect commits.
3. **Pull artifacts** — surgically inline via `get_test_run_artifact`, and/or in bulk via
   `mabl test-runs export <id> --types doms hars console_logs screenshots`.
4. **Correlate with source** — map the failing selector → component, failed network request → API
   handler, console stack → file; `git log`/`blame` the change window.
5. **Classify & report**, then optionally `--fix` and verify with `mabl-pre-pr-check`.

## Good to know

- Diagnose-only by default; it won't change code unless you pass `--fix`.
- RCA is evidence-based reasoning, not proof — it reports confidence and the trail. Verify a proposed
  fix (e.g. re-run the test) before closing the loop.
- Video/email artifacts and internal logs aren't accessible to agents.

## Related skills

- [`mabl-pre-pr-check`](../mabl-pre-pr-check) — run the relevant tests locally to verify a fix.
- `mabl-test-from-requirement` — if RCA reveals missing coverage, author a new test.
