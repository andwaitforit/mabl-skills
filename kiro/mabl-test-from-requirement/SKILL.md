---
name: mabl-test-from-requirement
description: Turn a documented requirement (Jira ticket, Confluence page, or pasted acceptance criteria) into a new mabl browser or API test. Use when the user wants to "create a mabl test from JIRA-123", "automate this AC in mabl", "build mabl coverage from this ticket / spec / Confluence page", or hands over a Given/When/Then story and asks for a mabl test. The skill handles requirement extraction, mabl workspace discovery, duplicate-coverage check, structured test planning, cloud test generation, and (optionally) writing the mabl test link back to the source ticket for traceability.
metadata:
  version: "1.0.0"
  host: kiro
compatibility: >-
  Requires the mabl MCP server connected in Kiro, plus an Atlassian MCP server
  when the requirement lives in Jira or Confluence. Network access required.
---

# Create a mabl test from a documented requirement

Use this skill any time the user wants to convert a written requirement into an automated mabl test. It works with Jira issues, Confluence pages, or free-form acceptance criteria the user pastes in. It deliberately does **not** invent requirements — if the source is ambiguous, ask.

## Required MCP tools

This skill assumes the **mabl** MCP server is connected, plus an **Atlassian** MCP server if the source is Jira/Confluence. If a tool isn't authenticated, tell the user which server to add to `.kiro/settings/mcp.json` (and connect from Kiro's **MCP Servers** panel) and stop.

mabl tools used:
- `list_mabl_workspaces`, `list_mabl_applications`, `list_mabl_credentials` — discover context
- `search_mabl_tests` — check for existing coverage of the same requirement
- `mabl_authoring_plan` — turn the AC into a reviewable step plan
- `mabl_authoring_initiate` — generate the test in the cloud
- `mabl_authoring_status` — poll until generation finishes
- `mabl_authoring_merge` — promote the generated test off its authoring branch

Atlassian tools used (when applicable):
- `getAccessibleAtlassianResources` — resolve `cloudId`
- `getJiraIssue` — fetch the ticket
- `getConfluencePage` — fetch a Confluence spec
- `addCommentToJiraIssue` — write a traceability comment back (only with explicit user OK)

## Workflow

Run these phases in order. Don't skip the planning step — generating a test from an unclear plan wastes a cloud-generation cycle.

### 1. Get the requirement

Ask the user (or infer from their message) where the requirement lives:

| Source | Action |
|---|---|
| Jira issue key (e.g. `PROJ-123`) | `getAccessibleAtlassianResources` → use the returned `cloudId` with `getJiraIssue`, `responseContentFormat: "markdown"` |
| Jira URL | Parse the issue key from the URL, then same as above |
| Confluence page URL | Parse `pageId`, call `getConfluencePage` with `responseContentFormat: "markdown"` |
| Pasted text / file | Use as-is — don't guess at hidden context |

Extract specifically:
- **The acceptance criterion** being automated (often labeled AC1/AC2/AC3, or a Given/When/Then block). If the ticket has multiple ACs, ask which one — one mabl test per AC is the cleanest mapping.
- **Concrete data** in the AC — exact amounts, exact strings to assert on, exact field labels. The AC's literal language should drive test assertions, not paraphrased.
- **Any pre-existing automation pointers** in comments (linked mabl test IDs, prior failure notes). Use these to decide whether you're creating new vs. augmenting existing — see step 3.

### 2. Discover the mabl context

In parallel:
1. `list_mabl_workspaces` — pick the workspace. If the user has one obvious workspace (named after their company or product), use it; otherwise list options and ask.
2. `list_mabl_applications` for that workspace — pick the application matching the requirement, and pick the **environment** the user wants to target. Print the env name + URL back so the user can correct you (Dev vs Staging vs Prod matters).
3. `list_mabl_credentials` — pick the credential matching the persona in the AC ("as an admin" → an Admin credential; "as a customer" → a customer credential). Prefer ones that aren't cloud-only if the test may also run locally.

If anything is ambiguous, ask before continuing. Do NOT guess credentials.

### 3. Check for duplicate coverage

Call `search_mabl_tests` with a natural-language query derived from the AC (e.g. "promo code applied at checkout"). If a test already exists that covers the same AC:

- If it's clearly the same scope → tell the user, link the existing test, ask whether to:
  - (a) skip creation,
  - (b) create a new variant with a clarified name (e.g. "AC3 — deterministic $50 case"),
  - (c) replace by deleting the old one (only with explicit confirmation).
- If it's adjacent but different scope (e.g. happy path exists, this AC is the negative case) → proceed and call out the relationship in the test name.

This step prevents the workspace from accumulating near-duplicate tests, which is a very common customer pain point.

### 4. Plan the test (BEFORE creating it)

Use `mabl_authoring_plan` to draft the steps, then present a concise plan to the user containing:

- **Name** — `<TICKET-KEY>: <short AC summary>`. Example: `PROJ-142: Promo code — 10% off a $50 order`.
- **Target** — workspace name, application name, environment name + URL, credential name.
- **Test type** — browser vs API. Default to browser unless the AC describes an API contract (status codes, JSON shape, headers).
- **Intent** (1–3 sentences) — exact paraphrase of what passing means. This shapes the generated steps.
- **Steps** — numbered, terse, each one verifiable. Include:
  - Setup (viewport, visit URL)
  - Login via a reusable flow if one exists in the workspace (check `search_mabl_tests` results for `Login - <persona>` flows)
  - Each user action from the AC, with **exact** field labels and values
  - Assertions on **exact** strings/values from the AC — substring matches for messages, arithmetic for amounts
- **Deterministic data** — prefer fixed values from the AC over `randomInt(...)`. Random values make assertions hard and break traceability. Only use random data if the AC explicitly requires it.
- **Negative constraints** — tell the generator what *not* to do: no assertions on time-of-day greetings or other dynamic text, no GenAI/visual assertions if the test must be green in local CLI runs, no generated ids or pixel coordinates as selectors.

Stop and get user sign-off on the plan before generating. Generation costs time and a cloud-runner slot; planning errors caught here are free.

### 5. Create the test

Call `mabl_authoring_initiate` with the workspace, application, environment, and target URL from step 2 (the application URL for browser tests, the API base URL for API tests), plus the name, intent, and steps from step 4. Flag it as an API test and supply the relevant spec excerpt if the AC describes an API contract.

Capture the returned session identifiers so you can poll.

### 6. Poll until generation completes

Call `mabl_authoring_status` every ~30s. Don't busy-loop — generation typically takes 1–3 minutes for browser tests. Stop when the status is terminal (complete or failed).

On success, the response includes the new test ID (ends in `-j`) and a link to view it. Show the user both.

⚠️ **Generated tests land on an authoring branch, not `master`.** `mabl tests run --id` executes the master tip, so a verification run before promoting will execute the *old* steps (or nothing). Promote with `mabl_authoring_merge` — or `list_mabl_test_versions` → `restore_mabl_test(version=<new>)` — **then** run it.

On failure, surface the model message verbatim — don't retry blindly. Common causes: wrong env URL (app not reachable from the cloud runner), missing reusable flow referenced in the steps, ambiguous step text. Fix the plan and retry once.

### 7. Read the generated steps before trusting the test

Generation reporting success is not the same as the test being correct. **Hand-read every conditional branch.** An `IF` whose condition was false during authoring never executed, so validation passed without ever running the steps inside it — a wrong step there ships silently. Diff intent vs. generated steps for each `IF` body specifically.

### 8. Traceability (optional, only with consent)

Offer to write the result back to the source. For Jira, `addCommentToJiraIssue` with a body summarizing:
- Test name + link
- Test ID
- Environment + credential used
- Result of the first run (if you ran it)

**Do not post to Jira/Confluence/Slack without an explicit "yes" from the user** — this is a write operation visible to the whole project.

## Defaults and conventions

- **One AC = one test.** Don't bundle multiple ACs into a single test even if they're in the same ticket; bundling makes failure attribution painful.
- **Browser tests target the front-end URL** (e.g. `http://localhost:3000`), **API tests target the API base URL** (e.g. `http://localhost:3001/api`). Both come back from `list_mabl_applications`; pick the right one.
- **Reuse existing flows.** When `search_mabl_tests` reveals reusable flows like `Login - Admin` or `Select Account`, reference them by name in the steps — the generator will wire them up.
- **Quote AC strings exactly.** If the AC says "Promo code SAVE10 applied — you saved $5.00", the assertion text must contain that substring verbatim. Paraphrasing breaks the trace.
- **Skip generation for unclear ACs.** If the requirement is more aspirational than testable ("the page should feel fast", "users should love the new UI"), tell the user it's not test-ready and suggest concrete acceptance criteria first.

## Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Cloud runner can't reach the app | Used `localhost` for a cloud env | Switch to a cloud-reachable env (e.g. mabl Link, or a deployed URL) |
| Generated test logs in but stops at "Click on X" | Used a label that doesn't match the live DOM | Update the step to match the actual button text/aria-label |
| Test is created but assertions are vague | Intent was paraphrased instead of quoted | Re-create with the AC string verbatim in the intent |
| A verification run executes the old steps | Test still on its authoring branch | `mabl_authoring_merge` (or `restore_mabl_test`) before running |
| Multiple near-duplicate tests pile up | Skipped step 3 | Run `search_mabl_tests` first; consolidate before creating |

## Example: Jira → mabl in one pass

User: *"Create a mabl test for PROJ-142 in my dev env using admin creds."*

1. `getAccessibleAtlassianResources` → cloudId.
2. `getJiraIssue(PROJ-142)` → extract AC3 (Given/When/Then: a $50 order, code `SAVE10`, expect $45 total and a confirmation message).
3. `list_mabl_workspaces` → pick the user's product workspace.
4. `list_mabl_applications` → pick the storefront app, environment "Dev".
5. `list_mabl_credentials` → pick "Admin".
6. `search_mabl_tests("promo code checkout")` → find one near-duplicate, propose a deterministic variant.
7. `mabl_authoring_plan` → present the plan, get OK.
8. `mabl_authoring_initiate(...)` with the deterministic $50 / $45 / exact-substring plan.
9. Poll `mabl_authoring_status` until complete; `mabl_authoring_merge` to promote; share the test URL.
10. Offer to post an `addCommentToJiraIssue` traceability comment with the new test link.
