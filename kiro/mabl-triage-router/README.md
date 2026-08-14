# mabl-triage-router — Kiro skill

The piece that turns a pile of skills into a **loop**.

`mabl-failure-rca` tells you *why* a run is red. This skill decides *what happens next* —
fix the code, update the test, reset the environment, retry a flake, or escalate — and
keeps the loop bounded and safe so it converges on green instead of spinning.

## Where it fits

Part of the **verification loop** (see [`docs/loop-contracts.md`](../../docs/loop-contracts.md)):

```
mabl-failure-rca ──(failureVerdict)──▶ mabl-triage-router ──(routerDecision)──▶ auto-repair
                                                           └──────────────────▶ human gate
```

Run it immediately after `mabl-failure-rca` produces a verdict, or call it from an
orchestrator as the branch node that decides whether to auto-repair, gate for a human, or
stop.

## Prerequisites

Shared setup (mabl CLI, `.kiro/settings/mcp.json`) is in [`../README.md`](../README.md). This skill is mostly **pure
decision logic** — it reads a verdict and emits a decision. It touches the mabl MCP server
only for the repair actions it recommends (`rerun_mabl_test`, `list_mabl_test_versions`,
`restore_mabl_test`).

It expects a `failureVerdict` as input, so it's most useful alongside `mabl-failure-rca`.

## Install

```bash
cp -r mabl-triage-router ~/.kiro/skills/        # or <your-repo>/.kiro/skills/
```

## Usage

```
/mabl-triage-router
/mabl-triage-router --max-iterations 5 --confidence-floor 0.75
```

| Arg | Meaning | Default |
|-----|---------|---------|
| verdict | A `failureVerdict` from `mabl-failure-rca` | this session's most recent |
| `--max-iterations <n>` | Repair cycles allowed before escalating | 3 |
| `--iteration <n>` | Current cycle count (the loop increments this) | 1 |
| `--confidence-floor <0–1>` | Below this, ask a human instead of auto-repairing | 0.6 |

## The two safety rules

These are the whole point of the skill, and they are not configurable:

1. **Product-code fixes are never auto-applied.** A `class: product` verdict always routes
   to `autoApply: false` + `requiresHumanGate: true`, regardless of confidence. Product
   logic is the user's to approve. Only test / env / flake classes may self-repair.
2. **The loop is bounded.** When `iteration > maxIterations` the skill emits
   `escalated: true` and stops — checked *before* anything else, so a bad diff can never
   spin forever.

Anything that would spend mabl credits (billable AI reruns, a cloud plan) is gated too,
regardless of class.

## Good to know

- **A promoted fix, or the re-run lies.** Local authoring saves edits to an "Agent edit
  session" branch, but `mabl tests run --id` executes the master tip — so a verification
  run before promoting silently re-runs the *old* steps and "fails." The skill's
  `edit-test` route requires `restore_mabl_test` (or a merge) first.
- **A flake that reproduces isn't a flake.** A `retry` that fails again doesn't burn a
  repair iteration as a flake; it gets reclassified.
- **A lone GenAI/visual red is a pass.** Local CLI runs skip billable AI assertions. If
  every concrete assertion passed and only the AI step is red, the repair counts as green.
- **Garbage in, wrong route out.** The skill is only as good as the incoming verdict —
  which is why the confidence floor exists. When RCA is unsure, this defers to a human.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
