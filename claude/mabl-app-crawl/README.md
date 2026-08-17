# mabl-app-crawl — Claude Code skill

Authors a **saved, read-only breadth-crawl test** in mabl — an *app map* that enumerates as
many pages, views, and UI states as it can reach without changing data. The saved test doubles
as **navigational context**: when you later ask mabl to author specific tests, its agent can
lean on this map for the app's routes, waypoints, and stable landmarks instead of
rediscovering them each time.

Unlike the two `mabl-app-context*` skills (which write a **markdown doc**), this one creates a
**mabl test** via the authoring agent, so the map lives *inside* the workspace.

## The reusable brief

The natural-language brief handed to mabl's authoring agent lives in
[`crawl-prompt.md`](crawl-prompt.md) — a portable, improved version of a "crawl my app"
prompt. You can also paste it straight into the mabl UI when authoring by hand; just fill in
the `{{PLACEHOLDERS}}` (at minimum `{{BASE_URL}}` and `{{PERSONA}}`). The skill fills them in
for you.

What the improved brief adds over a naive "click around and record pages" prompt:

- **Structured output** — a route map with a **stable landmark** (arrival-proof) per view, a
  **nav path** to retrace it, and flows described as ordered waypoints — consumable by the
  next test-generation pass, not just prose.
- **Persona / access-control awareness** — records which persona reached each route and marks
  role-gated areas, so the map's boundaries are explicit.
- **Selector-stability rules** — prefers `data-testid` / `aria-label` / role+name / link text
  and **flags volatile text** (balances, timestamps, per-record ids, greetings) so downstream
  tests don't pin to it.
- **Budgets, dedup, and trap avoidance** — a normalized visited-set (`/users/:id` mapped
  once), caps on views/depth/steps, and explicit handling of pagination, calendars, infinite
  scroll, and redirect loops that hang crawlers.
- **Tighter, mabl-aware guardrails** — never leaves the app origin, doesn't click Logout until
  the end, dismisses confirm dialogs, no downloads/new tabs — on top of the destructive-button
  blacklist.
- **Coverage & gaps report** — what wasn't reached and why (`role-gated`, `destructive-only`,
  `external`, `budget-reached`).

## Prerequisites

- The **mabl** MCP server connected. If a tool isn't authenticated, the skill stops and asks
  you to authenticate it (`/mcp`).
- A mabl **application + non-production environment** and at least one **credential/persona**
  to crawl as.

## Usage

```
/mabl-app-crawl --persona Admin --env Staging
```

| Arg | Default | Meaning |
|---|---|---|
| `--persona <label>` | asks you | Credential/persona to crawl as (bounds the map) |
| `--env <name>` | asks you | Environment to target — **never production** |
| `--max-views <n>` | `40` | Stop after this many distinct views |
| `--max-depth <n>` | `3` | Link-crawl depth from the landing page |
| `--name <name>` | `App Map — <app> (<persona>)` | Test name |
| `--personas <l1,l2,…>` | one | Author one app-map test per persona (access differs by role) |

## ⚠️ Safety — read-only, non-production

- **The crawl never commits a change** — it opens forms to read them and closes them, retraces
  navigation, but never Saves/Submits/Creates/Deletes/Transfers. That's what lets it be re-run
  any time to refresh the map.
- **Never production.** An exploration crawl touches far more UI than a focused test; the skill
  refuses to target a production environment.
- Step 7 **hand-reads the generated steps** to confirm zero write actions before promoting —
  don't skip it.

## Good to know

- **Discoverable as context:** saved as `App Map — <app> (<persona>)` with suggested labels
  `type:exploration` / `type:app-map` / `readonly` so the workspace can filter for it.
- **One map per persona:** role-gated areas differ, so `--personas Admin,Client` gives the
  fullest picture.
- **Complements the doc skills:** if `docs/mabl/app-context.md` exists, the skill seeds known
  routes from it, then the crawl confirms and extends them live.

## Sibling skills

- [`mabl-app-context`](../mabl-app-context) — same map as a **doc, from source**.
- [`mabl-app-context-crawl`](../mabl-app-context-crawl) — same map as a **doc, from a browser
  crawl**.
- [`mabl-test-from-requirement`](../mabl-test-from-requirement) — turn a specific requirement
  into a test; it benefits from the map this skill saves.
