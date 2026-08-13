# mabl-failure-rca — Kiro skill

Root-cause a **failed mabl test run** against your application source. Hand it a run id (or
a link, or just a test name) and it will:

1. Resolve the reference to a concrete failed test run.
2. Pull mabl's **AI failure analysis** — synopsis, root cause, next steps, evidence.
3. Pull the **artifacts** — DOM snapshot, HAR, console logs, screenshots at the failing step.
4. **Correlate** all of it with the repo: grep for the targeted selector, map the failing
   request to its route handler, `git blame` the suspect window.
5. **Classify** the failure — product regression / stale test / env-data / flake — with a
   pinpointed `file:line`, the likely culprit commits, and a concrete fix.

The point is a verdict you can act on, not "it failed at step 7."

## Prerequisites

Shared setup (mabl CLI, MCP config) is in [`../README.md`](../README.md). Beyond that:

| Requirement | Why |
|-------------|-----|
| **`mabl` MCP server** connected | `analyze_mabl_failure`, `get_mabl_test_run_artifact`, run lookup |
| **Workspace AI features enabled** | mabl's AI failure analysis; without it the skill falls back to raw artifacts and says so |
| **The app's source repo** checked out | Correlation is the whole point — RCA against the wrong repo is worse than none |

## Install

```bash
cp -r mabl-failure-rca ~/.kiro/skills/        # or <your-repo>/.kiro/skills/
```

## Usage

```
/mabl-failure-rca <run-id | run-url | test-id | test-name | plan-run-id>
```

Or in plain language — *"why did this mabl test fail?"*, *"root cause this run"*, or just
paste a mabl run link.

### Optional arguments

| Arg | Meaning | Default |
|-----|---------|---------|
| `--workspace <name\|id>` | Target workspace | saved default |
| `--repo <path>` | Source repo to correlate against | current working directory |
| `--rev <ref>` | Revision the app-under-test was built from | current checkout (stated as an assumption) |
| `--artifacts <list>` | Which artifacts to export | `doms hars console_logs screenshots` |
| `--fix` | Apply the proposed fix, don't just describe it | off (diagnose, then offer) |

## Good to know

- **Pair it with `mabl-dom-sanitizer`.** Exported DOM snapshots run their own JS when opened,
  which re-hydrates the SPA and bounces you to login. Sanitize before inspecting.
- **Filter logs before grepping.** Artifact bundles embed base64 payloads; the skill pipes
  through `awk 'length($0) < 300'` first so a naive grep can't dump hundreds of KB into
  context.
- **Verdicts are evidence-based reasoning, not proof.** The skill reports confidence and the
  full evidence trail, and recommends verifying a proposed fix (e.g. via `mabl-pre-pr-check`)
  before calling it closed.
- **Video, email artifacts, and internal support logs** aren't exposed to agents.
- **Plan runs** are drilled into one failing test at a time.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
