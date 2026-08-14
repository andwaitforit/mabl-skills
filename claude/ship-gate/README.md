# ship-gate — Claude Code skill

The loop's decision gate: **"is this change safe to ship?"**

Everything upstream produced a quality signal. This skill turns that signal into an
auditable `SHIP` / `BLOCK` / `NEEDS_HUMAN` recommendation, with reasons and blockers
attached — grounded in mabl's own release readiness plus an explicit policy.

**It recommends only.** It never opens, merges, or marks a PR ready. The click stays with
a person.

## Where it fits

The last node of the **verification loop** (see [`docs/loop-contracts.md`](../../docs/loop-contracts.md)):

```
runResult[] ─┐
coverage ────┼──▶ ship-gate ──(shipVerdict)──▶ human decides
readiness ───┘
```

Run it at the end of `feature-dev`, or right after `mabl-pre-pr-check` reports all-green
(or only non-code reds), whenever you want a defensible go/no-go rather than a vibe.

## Prerequisites

Shared setup is in the [top-level README](../../README.md). This skill needs the **mabl MCP
server** with the workspace's **AI features** enabled — it calls `check_release_readiness`
and `analyze_mabl_results`. Without them it falls back to the raw pass/fail set and says the
readiness score is unavailable.

## Install

```bash
cp -r ship-gate ~/.claude/skills/        # or <your-repo>/.claude/skills/
```

## Usage

```
/ship-gate
/ship-gate --policy strict
/ship-gate <plan-run-id>
```

Or plain language — *"is my change safe to ship?"*, *"can I open the PR?"*

| Arg | Meaning | Default |
|-----|---------|---------|
| results | A `-jr`, a `-pr`, or the `runResult[]` from `mabl-pre-pr-check` this session | this session's results |
| `--workspace <name\|id>` | Target workspace | saved default |
| coverage | A `coverage` object from `mabl-coverage-gap` | none |
| `--policy strict\|standard` | Which policy profile to apply | `standard` |

## The policy

Explicit rules, not judgement calls:

| Decision | When |
|----------|------|
| **SHIP** | Every affected test passed — **or** the only reds are confirmed non-code (billable-AI skips, failures already red on the base branch, env/flake that healed on rerun) — **and** no new uncovered critical flow |
| **BLOCK** | A confirmed product regression, or a `critical` coverage gap with no test |
| **NEEDS_HUMAN** | Mixed readiness, triage confidence below threshold, or a proposed remedy that touches product code |

`--policy strict` additionally downgrades to `NEEDS_HUMAN` any SHIP that leaned on an
un-rerun flake, or any `normal`-severity coverage gap.

Even a clean `SHIP` lists "open PR" under `requiresHumanAction` — shipping is always a
human action.

## Good to know

- **Analyze failed runs first, or the score lies.** `check_release_readiness` reasons over
  *saved* failure analyses; a failed run with none is scored "unknown root cause" and drags
  the number down for no real reason. In one observed case an `at_risk`/75 score was driven
  entirely by two unanalyzed runs whose logs already stated the cause — billable GenAI
  skips. The skill runs `analyze_mabl_failure` on every red first, then scores.
- **The verdict is only as complete as the run set.** "Safe to ship" is grounded in the
  tests that actually ran, so the reasons always surface that scope.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
