---
name: mabl-triage-router
description: >-
  The decision brain that makes a mabl verification loop self-driving. Takes a
  classified failure (a failureVerdict from mabl-failure-rca) and decides the next
  action — fix code, update the test, reset the environment, retry a flake, or
  escalate to a human — enforcing loop bounds (max repair cycles) and human gates
  (product-code fixes and shipping never auto-apply). Use after a mabl test fails
  and has been root-caused, to decide what the loop does next, or when driving the
  verification loop headlessly and you need a routed next-step per failure.
metadata:
  version: "1.0.0"
  host: kiro
compatibility: >-
  Requires the mabl MCP server connected in Kiro. Pure decision logic — no
  browser or CLI execution of its own.
---

# mabl-triage-router (loop glue)

What turns a pile of skills into a **loop**. `mabl-failure-rca` says *why* a run is
red; this skill decides *what happens next* and keeps the loop safe and bounded so it
converges on green (or escalates) instead of spinning.

The flow: **read the verdict → pick the action → apply loop bound → gate or
auto-apply → emit `routerDecision`.**

Consumes a `failureVerdict` and emits a `routerDecision` — both defined in
[`docs/loop-contracts.md`](../../docs/loop-contracts.md), and inlined below so this
skill works standalone.

---

## When to use

- Immediately after `mabl-failure-rca` produces a `failureVerdict`, to route it.
- As the branch node when driving the loop headlessly (your orchestrator calls this to
  decide whether to auto-repair, gate for a human, or stop).

Not for: classifying the failure (that's `mabl-failure-rca`) or deciding shippability
(that's `ship-gate`). This skill only routes an already-classified failure.

---

## Inputs

| Input | Meaning | Default |
|-------|---------|---------|
| verdict | A `failureVerdict` object (or several) from `mabl-failure-rca` | this session's most recent verdict |
| `--max-iterations <n>` | Repair cycles allowed before escalating | 3 |
| `--iteration <n>` | Current cycle count (the loop increments this) | 1 |
| `--confidence-floor <0–1>` | Below this, route to a human instead of auto-repair | 0.6 |

---

## Step 1 — Guard the loop bound first
If `iteration > maxIterations`, **stop**: emit a `routerDecision` with
`action: "escalate"`, `escalated: true`, and a summary of what was tried. A bad diff
must never spin forever. Do this before anything else.

## Step 2 — Confidence check
If `failureVerdict.confidence < confidence-floor`, route to a human:
`action: "escalate"`, `requiresHumanGate: true` — a low-confidence auto-repair is
worse than asking. (Escalation here is "ask a human," not "loop exhausted.")

## Step 3 — Route by class
Map `failureVerdict.class` → action. Auto-apply is allowed **only** for test/env/flake
classes; anything touching product code or shipping is human-gated.

| `class` | `action` | `autoApply` | `requiresHumanGate` | Next step |
|---------|----------|-------------|---------------------|-----------|
| `product` | `propose-code-fix` | **false** | **true** | Present the diff from `suggestedFix`; on approval apply → re-run `mabl-pre-pr-check` |
| `stale-test` | `edit-test` | true | false | Edit the selector/assertion (Q4) → **promote to master** → re-run. Note `autoHealCandidate` if only a selector moved |
| `env-data` | `reset-env` | true | false | Reset the seed data / credential / precondition the test assumed (see below); re-run |
| `mabl-flake` | `retry` | true | false | `rerun_mabl_test` once; if it heals, flag drift as auto-heal candidate; if it re-fails, send back to `mabl-failure-rca` for reclassification |

Rules that override the table:

- **Never** auto-apply a product-code change — always `autoApply:false` +
  `requiresHumanGate:true`, even at high confidence. Product logic is the user's to approve.
- **`edit-test` must promote the fix to the runnable branch before re-verifying.**
  Local authoring (`mabl agent authoring initiate --mode local`) saves the edit to an
  "Agent edit session" branch, **not `master`** — but `mabl tests run --id` executes the
  master tip, so a re-run before promoting still uses the old steps and "fails." After the
  edit, `list_mabl_test_versions`, then `restore_mabl_test(version=<new>)` to make it the
  master latest (or merge the branch), **then** re-run. (Verified live: a selector fix
  persisted on a branch and only took effect after `restore_mabl_test`.)
- **`reset-env` means restoring the precondition the test assumed**, not editing the test.
  The common case is a test that isn't self-resetting: it adds an item that's already
  added, or runs as the wrong persona so the page renders differently. Undo the prior
  state, or pick a guaranteed-clean fixture, then re-run.
- **Verify re-run: a lone GenAI/visual (billable) failure is a pass.** Local CLI runs skip
  AI assertions ("AI assertions are not available in CLI runs") unless
  `--allow-billable-features` (consumes credits). If every concrete assertion passes and
  only the GenAI step is red, treat the repair as green; only spend credits to prove the
  AI step with explicit user go-ahead.
- A `retry` that re-fails does **not** consume a fresh repair iteration as a flake —
  reclassify it; a "flake" that reproduces is a real failure.
- Anything that would **spend mabl credits** (billable AI reruns, cloud plan) is
  gated regardless of class.

## Step 4 — Emit the decision

In prose, state the action, whether it auto-applies or waits for a human, and the next
step. When `autoApply:true` and no gate, the loop proceeds directly; when
`requiresHumanGate`, stop and surface the approval ask (an approval step in your
orchestrator, or a prompt to the user here).

Then emit one `routerDecision` block per input verdict — prose first, JSON last:

```json
{
  "schema": "routerDecision",
  "schemaVersion": "1.0",
  "inputVerdict": "product",
  "action": "propose-code-fix",
  "autoApply": false,
  "requiresHumanGate": true,
  "nextStep": "re-run mabl-pre-pr-check after fix",
  "iteration": 1,
  "maxIterations": 3,
  "escalated": false
}
```

- `action`: `propose-code-fix | edit-test | reset-env | retry | escalate | none`
- `autoApply`: `true` only for `edit-test` / `reset-env` / `retry`.
- `escalated`: `true` when `iteration > maxIterations` → stop looping, hand to a human.

Skip the JSON for a purely interactive one-off routing; always emit it inside
`feature-dev` or an automated loop.

---

## Decision defaults (don't ask unless it matters)
- Verdict: this session's latest `failureVerdict`; else ask for a run to route.
- Max iterations: 3; confidence floor: 0.6.
- Product fixes and ship actions: always human-gated, never auto-applied.
- Output: prose + one `routerDecision` JSON block per verdict.

## Limitations
- Only as good as the incoming `failureVerdict` — garbage class in, wrong route out.
  Keep the confidence floor meaningful; when RCA is unsure, this skill defers to a human.
- The loop bound counts **repair attempts**, not test reruns — a single flake retry
  that heals shouldn't burn the budget (Step 3 rule). The caller owns incrementing
  `iteration` on each genuine repair cycle.
