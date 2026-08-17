---
name: mabl-app-crawl
description: Author a saved, read-only breadth-first "app map" test in mabl — an exploration test that crawls the app's navigation to enumerate as many pages, views, and UI states as possible, then serves as reusable NAVIGATIONAL CONTEXT for generating more specific tests later. Use when the user wants to "crawl my app in mabl", "map the app's pages/flows", "build a navigation map for the mabl agent", "create an exploration test", "discover the app's user flows", or "bootstrap breadth coverage before writing specific tests". Distinct from `mabl-app-context`/`mabl-app-context-crawl` (which write a markdown doc): this creates a saved mabl TEST via the authoring agent. Read-only by design — it never commits a change.
metadata:
  version: "1.0.0"
  host: kiro
compatibility: >-
  Requires the mabl MCP server connected in Kiro. Targets a non-production mabl
  application environment. Network access required.
---

# Author a read-only app-map (breadth crawl) test in mabl

Use this skill to have mabl's authoring agent create a **broad, read-only exploration test**
that maps the app's breadth — as many distinct pages, views, and UI states as it can reach
without changing data. The saved test doubles as **navigational context**: when you later ask
mabl to author specific tests, its agent can lean on this map to know the app's routes,
waypoints, and stable landmarks instead of rediscovering them each time.

**Coverage beats depth. Read-only, always.** The crawl never commits a change — it opens
forms to read them and closes them, and it retraces navigation, but it never submits.

The exact brief handed to the authoring agent lives in [`crawl-prompt.md`](crawl-prompt.md)
next to this file. This skill resolves the app/persona/budgets, fills that brief in, drives
authoring, and saves + reports the map.

## Relationship to the other context skills

| Skill | Produces | Best when |
|---|---|---|
| `mabl-app-context` | a **markdown doc** from front-end **source** | you have the repo |
| `mabl-app-context-crawl` | the same **markdown doc** from a **browser crawl** | you only have a URL |
| **`mabl-app-crawl`** (this) | a **saved mabl test** that maps navigation, via the **authoring agent** | you want the map to live *inside mabl* as reusable authoring context |

The doc skills and this skill are complementary — if an app-context doc already exists
(e.g. `docs/mabl/app-context.md`), read it first to seed known routes and personas, then let
the crawl confirm and extend it live.

## Required MCP tools

Assumes the **mabl** MCP server is connected in Kiro. If a tool isn't authenticated, tell the
user to add it to `.kiro/settings/mcp.json` (and connect it from Kiro's **MCP Servers** panel)
and stop.

- `list_mabl_workspaces`, `list_mabl_applications`, `list_mabl_credentials` — resolve context
- `search_mabl_tests` — check for an existing app-map test (avoid duplicates); find a reusable `Login - <persona>` flow
- `mabl_authoring_plan` — sanity-check the crawl brief as a step plan before spending a cloud cycle
- `mabl_authoring_initiate` — generate the exploration test in the cloud
- `mabl_authoring_status` — poll until generation finishes
- `mabl_authoring_merge` — promote the generated test off its authoring branch

## Arguments

| Arg | Default | Meaning |
|---|---|---|
| `--persona <label>` | ask the user | Credential/persona to crawl as; the map is bounded by what it can reach |
| `--env <name>` | ask the user | Which environment (Dev/Staging/…) — **never production** |
| `--max-views <n>` | `40` | Stop after this many distinct views |
| `--max-depth <n>` | `3` | Link-crawl depth from the post-login landing page |
| `--name <name>` | `App Map — <app> (<persona>)` | Test name (see naming convention) |
| `--personas <l1,l2,…>` | one | If several, author one app-map test per persona (access differs by role) |

If persona or env is missing, ask. **Refuse to target production** — an exploration crawl
pokes at far more of the UI than a focused test, so the blast radius of a mistaken click is
larger; require a Dev/Staging/disposable environment.

## Workflow

Track phases with the [spec workflow](https://kiro.dev/docs/specs/) when the crawl is part of
a larger task; otherwise run them inline.

### 1. Resolve the mabl context
- `list_mabl_workspaces` → pick the workspace (use the obvious one; else ask).
- `list_mabl_applications` → pick the application and the **environment** (print name + URL
  back so the user can correct you). Confirm it is **not** production.
- `list_mabl_credentials` → pick the credential matching `--persona`. Do **not** guess
  credentials; if the persona is ambiguous, ask.

### 2. Check for an existing map & a login flow
- `search_mabl_tests("app map exploration navigation crawl")` — if an app-map test already
  exists for this app+persona, offer to (a) skip, (b) re-author a fresh version, or (c) keep
  both. Don't silently pile up near-duplicate maps.
- In the same results, look for a reusable `Login - <persona>` flow. If one exists, the brief
  should log in via that flow rather than re-deriving login steps.

### 3. Seed from an app-context doc if present (optional)
If `docs/mabl/app-context.md` (or a user-named doc) exists, read it and pass its known routes
and personas into the brief as *hints* — the crawl still confirms them live and fills gaps.

### 4. Fill in the brief and plan
- Take [`crawl-prompt.md`](crawl-prompt.md) and substitute `{{BASE_URL}}` (the env URL),
  `{{PERSONA}}`, `{{MAX_VIEWS}}`, `{{MAX_DEPTH}}`, `{{MAX_STEPS}}` (default 200), and any
  seeded route hints.
- Call `mabl_authoring_plan` with the filled brief. Skim the returned plan for two things:
  it **logs in and then navigates read-only**, and it contains **no** Save/Submit/Create/
  Delete/Transfer-style steps. If any write step appears, tighten the brief and re-plan —
  do **not** proceed with a plan that commits a change.
- Show the user a short summary (target app/env/URL, persona, budgets, name) and get sign-off.

### 5. Author the test
Call `mabl_authoring_initiate` with the workspace, application, environment, base URL, the
`--name`, and the filled brief as the intent. Capture the session identifiers to poll.

### 6. Poll until complete
`mabl_authoring_status` every ~30s — don't busy-loop. A breadth crawl authors slower than a
focused test (it visits many views); allow several minutes. Stop at a terminal status.

On success you get the new test ID (`…-j`) and a link — show both. On failure, surface the
model message verbatim (common causes: env URL not reachable from the cloud runner; a
referenced `Login` flow missing) and fix the brief before one retry.

### 7. Read the generated steps before trusting the map
Generation reporting success ≠ a clean read-only crawl. **Hand-read the steps** and confirm:
- login → navigation only, and **zero** write/commit actions;
- any create/edit form is opened and then **cancelled/closed**, not submitted;
- no `Logout` click before the end; no navigation off the app origin.

If a write step slipped in, remove it (or re-author) — this test may be re-run often as
context, so it must stay safe on every run.

> ⚠️ **Generated tests land on an authoring branch, not `master`.** `mabl tests run --id`
> executes the master tip. Promote with `mabl_authoring_merge` (or `list_mabl_test_versions`
> → `restore_mabl_test`) **before** running it.

### 8. Save, label, and report
- Promote with `mabl_authoring_merge`.
- Report back to the user:
  - the test name + link + ID;
  - the **route map** the crawl produced (routes, landmarks, nav paths);
  - **Coverage & gaps** — what wasn't reached and why (`role-gated`, `destructive-only`,
    `external`, `budget-reached`), so the next test-generation pass knows the blind spots.
- If the user gave `--personas` with several roles, repeat 4–8 per persona; role-gated areas
  differ, so one map per persona gives the fullest picture.

## Naming & label convention (so it's discoverable as context)

- **Name:** `App Map — <app> (<persona>)`, e.g. `App Map — Storefront (Admin)`.
- Suggest labels the workspace can filter on: `type:exploration`, `type:app-map`,
  `readonly`. Follow the workspace's existing label scheme if it has one (check
  `search_mabl_tests` / existing test metadata). Don't invent IDs or hardcode values.

## Defaults and conventions

- **Read-only is non-negotiable.** The value of this test is that it can be re-run any time to
  refresh the map without side effects. Any step that persists data defeats that.
- **Browser test, front-end URL.** App-map crawls target the app's front-end URL, not an API
  base URL.
- **One representative per template.** `/users/:id` is mapped once, not once per record —
  keeps the map compact and the crawl fast.
- **Reuse the login flow.** Reference an existing `Login - <persona>` flow by name so the
  generator wires it up instead of duplicating login steps.
- **Never production.** Re-state this to the user if they ask to point it at prod.

## Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Cloud runner can't reach the app | Used `localhost` for a cloud env | Target a cloud-reachable env (mabl Link or a deployed URL) |
| Crawl authors a Transfer/Delete step | Brief's guardrails weakened or omitted | Re-fill from `crawl-prompt.md` verbatim; re-plan; drop the write step |
| Crawl hangs paging a long list / calendar | Trap-avoidance guidance dropped | Keep the "Trap avoidance" section; sample first page only |
| Map is thin / stops early | Budgets too low, or persona is heavily gated | Raise `--max-views`/`--max-depth`, or crawl as a higher-access persona |
| A re-run executes old steps / nothing | Test still on its authoring branch | `mabl_authoring_merge` (or `restore_mabl_test`) before running |

## Example

User: *"Crawl my storefront app in mabl as the admin so the agent has a map before I write checkout tests."*

1. `list_mabl_workspaces` → the storefront workspace.
2. `list_mabl_applications` → Storefront app, environment **Staging** (confirm not prod), URL `https://staging.shop.example`.
3. `list_mabl_credentials` → Admin.
4. `search_mabl_tests` → no existing app-map; a `Login - Admin` flow exists.
5. Fill `crawl-prompt.md` (base URL, persona=Admin, max-views=40, depth=3), `mabl_authoring_plan`, confirm it's login→navigation only, get sign-off.
6. `mabl_authoring_initiate` → poll `mabl_authoring_status` → complete.
7. Hand-read steps: no writes, forms cancelled, no early logout. `mabl_authoring_merge`.
8. Report: test `App Map — Storefront (Admin)` + link, the route map, and a Coverage & gaps note (Billing settings = `role-gated`, New order = `destructive-only`).
