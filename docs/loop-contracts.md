# Loop Contracts — machine-readable verdicts

The seam between the **reasoning layer** (the skills) and the **orchestration layer**
(whatever drives them headlessly — n8n, GitHub Actions, a shell script, a cron job).

Every skill in the verification loop emits one of these JSON objects **in a fenced
` ```json ` block at the end of its response**, so a runner can parse it deterministically
and branch on it. Prose for the human comes first; the JSON block is the machine output.

Each skill also inlines the object it emits in its own `SKILL.md`, so it stays
self-contained when you copy a single folder into `~/.claude/skills/` or `~/.kiro/skills/`.
This file is the canonical reference for the whole set.

**See the loop at a glance.** A one-page diagram of how the skills identify, author,
execute, analyze, and act as the ship verdict — and where each contract below is emitted:
[light](mabl-verification-loop-light.pdf) · [dark](mabl-verification-loop-dark.pdf).

**Contracts are optional.** For a one-off interactive check, skip them — the prose answer
is the point. Emit them when a skill runs inside `feature-dev` or an automated loop.

Conventions:
- All objects carry `schema` (name) and `schemaVersion` (`"1.0"`).
- IDs use mabl's suffix convention: test `-j`, test run `-jr`, plan run `-pr`.
- Timestamps are ISO-8601 UTC. Enums are closed sets — add values here first.
- Unknown/uninferable fields are `null`, never omitted, so parsers can rely on keys.

---

## The loop

```
                 ┌──────────────────────┐
   your diff ───▶│  mabl-pre-pr-check   │──▶ impact + runResult[]
                 └──────────────────────┘
                    │                │
    coverageZeroMatch│                │status: failed
                    ▼                ▼
        ┌────────────────────┐  ┌──────────────────┐
        │ mabl-coverage-gap  │  │ mabl-failure-rca │──▶ failureVerdict
        └────────────────────┘  └──────────────────┘
                    │                │
                coverage             ▼
                    │      ┌─────────────────────┐
                    │      │ mabl-triage-router  │──▶ routerDecision
                    │      └─────────────────────┘
                    │                │ auto-repair → re-run pre-pr-check
                    ▼                ▼
                  ┌───────────────────┐
                  │     ship-gate     │──▶ shipVerdict
                  └───────────────────┘
```

The loop answers six questions: **Q1** which tests are affected, **Q2** which ran,
**Q3** why a run is red, **Q4** does the test need updating, **Q5** is there a coverage
gap, **Q6** is it safe to ship.

---

## 1. `impact` — emitted by `mabl-pre-pr-check` (Q1 + Q2)

What changed, which tests it touches, and which will run.

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
  "workspaceId": "<your-workspace-id>-w"
}
```

- `matchStrength`: `strong | partial | tangential`
- `willRun`: whether it's in the local run set (bounded by `--max`).
- `coverageZeroMatch`: `true` when no test matched → hand to `mabl-coverage-gap`.

## 2. `runResult` — one per executed test (`mabl-pre-pr-check` Step 5)

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

- `status`: `passed | failed | error`
- `billableSkipped`: `true` when GenAI/visual asserts were skipped locally — a
  failure on *only* those steps is a harness skip, **not** a code regression.

## 3. `failureVerdict` — emitted by `mabl-failure-rca` (Q3 + Q4)

The classification the router branches on.

```json
{
  "schema": "failureVerdict",
  "schemaVersion": "1.0",
  "testRunId": "XyZ789-jr",
  "class": "product",
  "confidence": 0.82,
  "needsTestUpdate": false,
  "failingStep": "Assert Recent Activity card shows 3 rows",
  "expected": "3 activity rows",
  "actual": "empty state",
  "evidence": [
    "DOM at step 7 missing [data-testid=recent-activity]",
    "HAR: GET /api/users/3/activity -> 500"
  ],
  "sourceRef": { "file": "src/controllers/activity.ts", "line": 42 },
  "suspectCommits": ["<sha>"],
  "suggestedFix": "Guard null account in activity controller",
  "autoHealCandidate": false,
  "runUrl": "https://app.mabl.com/workspaces/.../runs/XyZ789-jr"
}
```

- `class`: `product | stale-test | env-data | mabl-flake`
  - `product` → app code broke a real behavior (fix app).
  - `stale-test` → intentional UI/contract change (update the test; set
    `needsTestUpdate: true`, and `autoHealCandidate: true` if only a selector moved).
  - `env-data` → seed/creds/config/dependency (empty state, 503, wrong persona).
  - `mabl-flake` → race/timing/framework; corroborate with recovery session + history.
- `confidence`: 0–1. Below the router's threshold → route to a human.
- `needsTestUpdate` answers **Q4** explicitly.

## 4. `coverage` — emitted by `mabl-coverage-gap` (Q5)

```json
{
  "schema": "coverage",
  "schemaVersion": "1.0",
  "gapFound": true,
  "uncoveredFlows": [
    { "flow": "Recent Activity card empty state", "severity": "critical", "hasTest": false }
  ],
  "recommendation": "author",
  "authoredTestIds": []
}
```

- `severity`: `critical | normal | low`
- `recommendation`: `author | none | defer`
- `authoredTestIds`: populated after authoring creates coverage.

## 5. `shipVerdict` — emitted by `ship-gate` (Q6)

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

- `decision`: `SHIP | BLOCK | NEEDS_HUMAN` (policy in `ship-gate` SKILL.md Step 3).
- `ship-gate` never merges — `decision` is a recommendation; the merge/PR click is human.

## 6. `routerDecision` — emitted by `mabl-triage-router`

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
- `autoApply`: `true` only for `edit-test` / `reset-env` / `retry` (test/env/flake
  classes). `propose-code-fix` is always `autoApply:false` + `requiresHumanGate:true`.
- `escalated`: `true` when `iteration > maxIterations` → stop looping, hand to human.

---

## Orchestrator branching cheat-sheet

Wire these into whatever drives the loop — an n8n Code node, a GitHub Actions `if:`, a
`jq` filter in a shell script.

| Object | Field to branch on | Then |
|--------|--------------------|------|
| `impact` | `coverageZeroMatch` | true → `mabl-coverage-gap` |
| `runResult` | `status` | `failed`/`error` → `mabl-failure-rca` |
| `failureVerdict` | `class` | route via `mabl-triage-router` |
| `routerDecision` | `requiresHumanGate` | true → approval step (Slack, PR review, …) |
| `routerDecision` | `escalated` | true → stop loop, notify owner |
| `shipVerdict` | `decision` | `SHIP` → PR gate; `BLOCK` → open bug; `NEEDS_HUMAN` → approval step |

### Two safety rules the loop depends on

1. **Product-code fixes and ship actions are never auto-applied.** `mabl-triage-router`
   forces `autoApply:false` + `requiresHumanGate:true` for `class: product`, regardless of
   confidence, and `ship-gate` never opens or merges a PR.
2. **The loop is bounded.** `routerDecision.iteration > maxIterations` → `escalated:true`
   and the loop stops. A bad diff must never spin forever.
