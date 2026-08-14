---
name: mabl-coverage-gap
description: >-
  Answer "is there a gap in mabl coverage for this change?" Takes the changed
  flows (or the impact object from mabl-pre-pr-check) and uses mabl's coverage
  analysis to find user-facing paths the change touches that no test exercises —
  then recommends authoring, and can hand the gap to mabl-test-from-requirement to
  create the missing test. Use when the user asks "do we have coverage for this",
  "is there a test gap", "what's untested in my change", when mabl-pre-pr-check
  returns zero matching tests, or as the Q5 step of the verification loop.
---

# mabl-coverage-gap (Q5 — Is there a gap in coverage?)

Coverage is the question the pass/fail signal can't answer: a change can be all-green
simply because **nothing tests it**. This skill finds the user-facing flows a change
touches that have no mabl test, rates them, and (on request) closes the gap by
authoring a test.

The flow: **take changed flows → identify uncovered paths → rate + recommend →
optionally author → emit `coverage`.**

Emits a `coverage` object — defined in [`docs/loop-contracts.md`](../../docs/loop-contracts.md),
and inlined below so this skill works standalone.

---

## When to use

- Right after `mabl-pre-pr-check` — especially when its `impact` has
  `coverageZeroMatch: true` (the change matched no existing test).
- Before `ship-gate`, so a critical uncovered flow can BLOCK the ship.
- As a standalone "what's untested here?" check on a diff or a feature area.

Not for: running tests (`mabl-pre-pr-check`) or classifying a red run
(`mabl-failure-rca`). Authoring is delegated, not reimplemented.

---

## Inputs

| Input | Meaning | Default |
|-------|---------|---------|
| flows / diff | The `impact` object from `mabl-pre-pr-check`, or a changed-file/flow list | this session's `impact`; else current diff (`git diff HEAD`) |
| `--workspace <name\|id>` | Target workspace | saved default |
| `--app <id>` | mabl applicationId to scope coverage to | resolve via `list_mabl_applications`; ask if ambiguous |
| `--author` | If a gap is found, hand off to authoring to create the test | off (recommend only) |

---

## Step 0 — Preflight
1. **mabl MCP required** — uses `identify_coverage_gaps` (and `search_mabl_tests` to
   confirm no near-match). If the mabl MCP tools aren't present, stop and ask the user to
   connect the mabl MCP server (`mabl agent install <target>`, or add it to your MCP
   client config).
2. **Workspace + application** — resolve once and reuse.

## Step 1 — Establish the change's user-facing flows
Reuse the `impact` object if `mabl-pre-pr-check` ran this session (its `inferredFlows`
+ `affectedTests`). Otherwise derive flows from the diff using the same mapping
heuristics as `mabl-pre-pr-check` Step 2 (page/route → flow, component → flows that
render it, endpoint → API tests for that resource).

## Step 2 — Identify uncovered paths
Call `identify_coverage_gaps` (scoped to the workspace/application, biased to the
flows from Step 1). Cross-check against `mabl-pre-pr-check`'s `affectedTests`:
- A flow in Step 1 with **no** affected test and **no** gap-tool coverage → a gap.
- A flow with only a `tangential` match → weak coverage; treat per severity.

Confirm a suspected gap with a broadened `search_mabl_tests` query before declaring it —
avoid false gaps from an over-narrow earlier search.

## Step 3 — Rate & recommend
For each gap set `severity`:
- `critical` — core money/auth/data-integrity flow, or the primary behavior the
  change introduces (e.g. a brand-new card the feature exists to add).
- `normal` — secondary/edge behavior of a covered feature.
- `low` — cosmetic/rarely-hit path.

Set `recommendation`: `author` (critical/normal on a shipped flow), `defer`
(low, or covered indirectly elsewhere), or `none` (no real gap).

## Step 4 — Optionally author the missing test (`--author`)
When `--author` (or the user says to close the gap), hand the flow spec to
**`mabl-test-from-requirement`** (if the gap traces to a documented AC) or to mabl's
authoring tools directly — `mabl_authoring_plan` → `mabl_authoring_initiate` for cloud,
or `mabl agent authoring initiate --mode local` against a dev server.

Give the authoring agent a **stable selector plan**, not intent: name the exact
`data-testid` / `aria-label` to target. Agents get steps right from a literal selector
and guess wrong from a description. Also state the negative constraints — no
time-of-day or other dynamic-text assertions, no GenAI/visual assertions if the test must
be green in local CLI runs, no assertions on values randomized per request.

⚠️ **Local authoring is slow** — budget 30–45 minutes for a multi-group create session,
not the documented 5–20. Background it and don't poll in a tight loop.

Capture the new test id(s) into `authoredTestIds`, then loop them back through
`mabl-pre-pr-check` so the new coverage actually runs. Without `--author`, stop at the
recommendation and let the human/loop decide.

## Step 5 — Report + emit verdict
Summarize the gaps (flow, severity, recommendation) and any tests authored. Then emit
the verdict — prose first, JSON last:

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

`gapFound: true` at `critical` severity is a ship-blocker input for `ship-gate`.

Skip the JSON for a purely interactive one-off check; always emit it inside
`feature-dev` or an automated loop.

---

## Decision defaults (don't ask unless it matters)
- Flows: reuse this session's `impact`; else derive from `git diff HEAD`.
- Mode: **recommend only**; author only with `--author` or on explicit request
  (authoring may consume mabl credits / dev-server time — confirm first).
- Output: prose summary + one `coverage` JSON block.

## Limitations
- `identify_coverage_gaps` needs the workspace's AI/coverage features enabled; if
  unavailable, fall back to the set-difference of Step 1 flows vs. `affectedTests`
  and say the analysis is heuristic (no mabl coverage model behind it).
- "No gap" means no gap **among the flows this change touches** — it is not a
  statement about whole-app coverage. For that, run coverage analysis across the
  application rather than scoping it to a diff.
