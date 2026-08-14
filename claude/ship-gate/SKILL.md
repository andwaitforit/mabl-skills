---
name: ship-gate
description: >-
  Final "is this change safe to ship?" gate for a mabl verification loop.
  Takes the results of the mabl tests that ran for a change (a test run, a plan
  run, or the runResult set from mabl-pre-pr-check), checks mabl's release
  readiness, applies an explicit ship policy, and returns SHIP / BLOCK /
  NEEDS_HUMAN with reasons. Recommends only — it never opens or merges a PR. Use
  when the user asks "is my change safe to ship", "can I open the PR", "release
  readiness for this run/plan", "gate this change", or at the end of the
  feature-dev / pre-PR loop before the ship decision.
---

# ship-gate (Q6 — Is the change safe to ship?)

The loop's decision gate. Everything upstream produced a quality signal; this skill
turns that signal into a **recommendation** the human acts on. It does **not** open,
merge, or mark a PR ready — it answers "should we?" and hands the click to a person.

The flow: **collect run signal → check release readiness → apply ship policy →
emit `shipVerdict`.**

Emits a `shipVerdict` — defined in [`docs/loop-contracts.md`](../../docs/loop-contracts.md),
and inlined below so this skill works standalone.

---

## When to use

- The last step of `feature-dev`, or right after `mabl-pre-pr-check` reports
  all-green (or only non-code reds), to get a policy-based go/no-go.
- Any time the user wants a defensible "safe to ship?" answer tied to mabl evidence.

Not for: running tests (`mabl-pre-pr-check`), classifying a failure
(`mabl-failure-rca`), or actually opening the PR (that's the human).

---

## Inputs

| Input | Meaning | Default |
|-------|---------|---------|
| results | The signal to gate: a `-jr`, a `-pr`, or the `impact` + `runResult[]` from `mabl-pre-pr-check` this session | reuse this session's run results |
| `--workspace <name\|id>` | Target workspace | saved default (see `mabl-pre-pr-check` Step 0) |
| coverage | A `coverage` object from `mabl-coverage-gap`, if one was produced | none |
| `--policy strict\|standard` | Which policy profile to apply | `standard` |

If results weren't produced this session and none is given, ask for a run/plan ref
rather than guessing.

---

## Step 0 — Preflight
1. **mabl MCP required** — this skill uses `check_release_readiness` and
   `analyze_mabl_results`. If the mabl MCP tools aren't present, stop and ask the user to
   connect the mabl MCP server (`mabl agent install <target>`, or add it to your MCP
   client config).
2. **Workspace** — resolve once (named arg → else saved default → else ask).

## Step 1 — Collect the run signal
Assemble what actually ran for this change:
- If given `runResult[]` (from `mabl-pre-pr-check`), use them directly.
- If given a `-pr` → `analyze_mabl_results` / `get_mabl_plan_run` for per-test status.
- If given a `-jr` → `get_mabl_test_run` for status + failing step.

Note for each: pass/fail, failing step, and whether a failure was a **billable skip**
(GenAI/visual assertion disabled in local CLI — not a code regression) or a
**confirmed non-code** red already triaged by `mabl-failure-rca`.

## Step 1.5 — Analyze failed runs *before* scoring readiness
For **each failed run** in the signal, call `analyze_mabl_failure(runId)` first, so a
saved failure analysis exists. `check_release_readiness` reasons over saved analyses;
a failed run with **no** analysis is scored "unknown root cause" and **drags the score
down for no real reason** (observed: an `at_risk`/75 readiness score driven entirely by
two unanalyzed runs whose logs already stated the cause — billable GenAI skips). Skip
this only for runs already analyzed by `mabl-failure-rca` this session. Billable-skip
reds don't need deep analysis, but a saved record still keeps them from scoring as
"unknown."

## Step 2 — Check release readiness
Call `check_release_readiness` for the workspace/plan (and `analyze_mabl_results` for
a plan-level summary). Capture the readiness signal/score and any blockers it names —
this is mabl's own view; the policy in Step 3 is *yours* layered on top. If the score
looks worse than the triaged reality, check whether it's driven by unanalyzed runs
(Step 1.5) rather than real risk, and say so in the verdict reasons.

## Step 3 — Apply the ship policy
Decide `SHIP | BLOCK | NEEDS_HUMAN` from explicit rules (auditable, not vibes):

- **SHIP** — every affected test passed, **or** the only reds are confirmed non-code:
  - billable-AI skips in local CLI runs, **or**
  - pre-existing failures already red on the base branch (not introduced by this change), **or**
  - env/flake that healed on rerun (per `mabl-triage-router`),

  AND no **new uncovered critical flow** (from the `coverage` object, if present).
- **BLOCK** — any confirmed **product regression** (`failureVerdict.class == product`),
  or a **critical-flow coverage gap** with `hasTest == false`.
- **NEEDS_HUMAN** — readiness is mixed, confidence on any triage is below threshold,
  or a proposed remedy **touches product code**. Ship/merge itself is always a human
  action, so a clean SHIP still surfaces "open PR" under `requiresHumanAction`.

Under `--policy strict`, downgrade any SHIP that relied on an un-rerun flake, or any
`coverage.gapFound == true` at `normal` severity, to NEEDS_HUMAN.

## Step 4 — Report + emit verdict
Give the human a tight summary: decision, the one-line why, blockers, and the mabl
run link(s). Never call any PR/merge/deploy tool — list those under
`requiresHumanAction` for the person or your orchestrator's approval step.

Then emit the verdict — prose first, JSON last:

```json
{
  "schema": "shipVerdict",
  "schemaVersion": "1.0",
  "decision": "NEEDS_HUMAN",
  "readinessScore": 0.9,
  "reasons": [
    "1 affected test passed",
    "coverage gap (critical) with no test"
  ],
  "blockers": ["critical-flow coverage gap: Recent Activity empty state"],
  "runRefs": ["XyZ789-jr"],
  "requiresHumanAction": ["open PR", "author test for empty-state gap"]
}
```

- `decision`: `SHIP | BLOCK | NEEDS_HUMAN`.
- `readinessScore`: 0–1, from `check_release_readiness`; `null` if AI features are off.

Skip the JSON for a purely interactive one-off gate; always emit it inside
`feature-dev` or an automated loop.

---

## Decision defaults (don't ask unless it matters)
- Signal: this session's `mabl-pre-pr-check` results; else the ref given; else ask.
- Policy: `standard`.
- Output: prose summary + one `shipVerdict` JSON block.
- Never merges/opens/promotes — recommendation only.

## Limitations
- `check_release_readiness` / `analyze_mabl_results` need the workspace's AI features
  on; if unavailable, fall back to the raw pass/fail set and say the readiness score
  is unavailable (the decision then rests on the pass/fail + coverage rules alone).
- "Safe to ship" is a recommendation grounded in the tests that *ran* — it's only as
  complete as the run set (Q2) and coverage (Q5). Surface that scope in the reasons.
