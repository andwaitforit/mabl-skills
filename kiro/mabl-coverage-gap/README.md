# mabl-coverage-gap — Kiro skill

Answers the question a green test run **cannot**: *is this change covered at all?*

A diff can pass every test simply because nothing exercises it. This skill takes the flows
your change touches, finds the ones no mabl test covers, rates them by severity, and — on
request — closes the gap by authoring the missing test.

## Where it fits

Part of the **verification loop** (see [`docs/loop-contracts.md`](../../docs/loop-contracts.md)):

```
mabl-pre-pr-check ──(coverageZeroMatch)──▶ mabl-coverage-gap ──(coverage)──▶ ship-gate
```

- Run it right after `mabl-pre-pr-check`, especially when that skill reports zero matching
  tests.
- Run it before `ship-gate`, so a `critical` uncovered flow can block the ship.
- Or standalone: *"what's untested in my change?"*

## Prerequisites

Shared setup (mabl CLI, `.kiro/settings/mcp.json`) is in [`../README.md`](../README.md).
This skill needs the **mabl MCP server** with the workspace's **AI / coverage features**
enabled — it calls `identify_coverage_gaps`. Without them it degrades to a heuristic
set-difference and says so.

## Install

```bash
cp -r mabl-coverage-gap ~/.kiro/skills/        # or <your-repo>/.kiro/skills/
```

## Usage

```
/mabl-coverage-gap
/mabl-coverage-gap --author
```

Or plain language — *"do we have mabl coverage for this change?"*

| Arg | Meaning | Default |
|-----|---------|---------|
| flows / diff | The `impact` from `mabl-pre-pr-check`, or a changed-file list | this session's `impact`; else `git diff HEAD` |
| `--workspace <name\|id>` | Target workspace | saved default |
| `--app <id>` | mabl applicationId to scope coverage to | resolved; asks if ambiguous |
| `--author` | Close the gap by authoring the test, not just reporting it | off — recommend only |

## Good to know

- **Recommend-only by default.** Authoring consumes time and possibly mabl credits, so it
  never happens without `--author` or an explicit ask.
- **Severity drives the ship decision.** `critical` means a core money/auth/data-integrity
  flow, or the headline behavior the change exists to add — that's a `ship-gate` blocker.
  `normal` and `low` are advisory.
- **It double-checks itself.** A suspected gap is re-confirmed with a broadened
  `search_mabl_tests` query before being declared, so an over-narrow earlier search doesn't
  manufacture a false gap.
- **Scope is the diff, not the app.** "No gap" means no gap *among the flows this change
  touches*. It is not a statement about whole-app coverage.
- **If it authors, it hands you stable selectors.** The skill instructs the authoring agent
  with literal `data-testid`s and explicit negative constraints (no dynamic-text assertions,
  no GenAI assertions if the test must pass in local CLI runs) — that's the difference
  between a test that passes once and one that survives re-runs.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
