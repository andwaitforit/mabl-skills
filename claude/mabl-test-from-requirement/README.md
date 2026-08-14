# mabl-test-from-requirement — Claude Code skill

Turn a **documented requirement** into a real mabl test. Point it at a Jira ticket, a
Confluence page, or pasted acceptance criteria and it will:

1. Extract the specific AC being automated — with its exact strings and amounts.
2. Discover your mabl workspace, application, environment, and the right credential.
3. **Check for duplicate coverage** before creating anything.
4. Draft a step plan and get your sign-off.
5. Generate the test in the cloud, poll to completion, and promote it off its authoring branch.
6. Optionally comment the test link back on the ticket for traceability.

It deliberately does **not** invent requirements. If the source is ambiguous, it asks.

## Prerequisites

Shared setup is in the [top-level README](../../README.md). Beyond that:

| Requirement | Why |
|-------------|-----|
| **mabl MCP server** connected | Workspace discovery, duplicate check, cloud test generation |
| **Atlassian MCP server** connected | Only if the requirement lives in Jira or Confluence |
| **A cloud-reachable environment** | The cloud runner has to be able to load your app — `localhost` won't work unless you're using mabl Link |

## Install

```bash
cp -r mabl-test-from-requirement ~/.claude/skills/        # or <your-repo>/.claude/skills/
```

## Usage

```
/mabl-test-from-requirement PROJ-142
/mabl-test-from-requirement https://your-site.atlassian.net/browse/PROJ-142
```

Or paste the criteria directly — *"automate this AC in mabl: Given a $50 order…"*

## Conventions it enforces

- **One AC = one test.** Bundling multiple criteria into one test makes failure attribution
  painful, so it refuses to.
- **Quote the AC verbatim.** If the AC says "Promo code SAVE10 applied — you saved $5.00",
  the assertion contains that substring exactly. Paraphrasing breaks the trace back to the
  requirement.
- **Deterministic data over random.** Fixed values from the AC beat `randomInt(...)` —
  random values make assertions hard and destroy traceability.
- **Reuse existing flows.** When the workspace already has `Login - Admin` or similar, the
  plan references it by name rather than re-authoring the steps.
- **Plan before generating.** Generation costs a cloud-runner slot; a planning error caught
  at review is free.
- **Nothing is posted without consent.** The Jira traceability comment is visible to the
  whole project, so it requires an explicit yes.

## Good to know

- **Promote before you run.** Generated tests land on an authoring branch, not `master` —
  and `mabl tests run --id` executes the master tip. A verification run before promoting
  silently executes the old steps. The skill promotes with `mabl_authoring_merge` first.
- **Read the generated conditionals by hand.** Generation reporting success only means the
  paths it *executed* worked. An `IF` whose condition was false during authoring was never
  run, so a wrong step inside it ships silently and validation still passes.
- **Not every requirement is testable.** "The page should feel fast" gets pushed back with a
  request for concrete criteria rather than a bad test.

## Pairs with

- [`mabl-coverage-gap`](../mabl-coverage-gap) — finds the gap; this skill fills it when the
  gap traces to a documented AC.
- [`mabl-app-context`](../mabl-app-context) — generate an app-context briefing first and the
  generated steps get markedly better selectors.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
