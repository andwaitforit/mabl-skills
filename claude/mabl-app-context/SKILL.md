---
name: mabl-app-context
description: Generate a client-side application-context briefing for mabl's test-creation agent. Produces a markdown file (default docs/mabl/app-context.md) describing the app's pages, personas/credentials, core user flows, UI selector conventions, and known quirks — derived only from the client/front-end code (never the server), optionally enriched with extra data sources. Use when the user wants to "generate mabl agent context", "bootstrap app context for mabl test creation", "create application instructions for the mabl agent", or hand mabl a description of the app's user flows. Portable across Vite/React/Next client apps; defaults tuned for a Vite + React Router repo.
---

# Generate client-side app context for the mabl test agent

Use this skill to produce a markdown briefing that gives mabl's test-creation agent the **client-side mental model** of an application: what pages exist, who logs in, what the core user flows are, the UI selector conventions, and the quirks worth knowing. The agent that consumes this file only sees the browser — so this skill deliberately describes the app **from the client's perspective only** and never documents server internals.

The output is a hand-off artifact: paste it into mabl as agent instructions, or feed it to the `mabl-test-from-requirement` skill as context.

## Core principles

- **Client-only.** Read only the front-end source (default `client/src`). Never open `server/`, Prisma schema, or DB code — if mabl's browser agent can't observe it, it doesn't belong in the doc. Business rules that aren't visible in the UI come in via `--sources`, not by reading the backend.
- **Don't invent flows.** Describe what the code actually renders. If a page's behavior is ambiguous from source, mark the step `⚠️ needs confirmation` rather than guessing.
- **Selectors mabl can use.** Prefer stable hooks the agent can target: visible labels, ARIA labels, `data-testid`, roles, `id`s. Call out where a label is dynamic or role-gated.
- **Idempotent.** Safe to re-run; overwrites the output file. If a live-crawl pass disagrees with the static map, note the drift instead of silently picking one.

## Arguments

Parse these from the user's invocation (all optional):

| Arg | Default | Meaning |
|---|---|---|
| `--client-root <path>` | `client/src` | Front-end source root to analyze |
| `--out <path>` | `docs/mabl/app-context.md` | Where to write the briefing |
| `--sources <a,b,...>` | none | Extra context: file paths, doc folders, Jira/Confluence URLs, pasted ACs |
| `--live` | off | Also drive the running app via preview tools to verify/enrich selectors + capture screenshots |

If the user gives no args, use the defaults and proceed (don't interrogate them).

## Workflow

Run the phases in order. Track them with TaskCreate/TaskUpdate if the repo is large.

### 1. Resolve config & detect stack

- Confirm the client root exists. If `client/src` is absent, detect it: look for `src/` next to a `package.json` that depends on `react`/`next`/`vue`/`svelte`.
- Read the client `package.json` to identify the router (`react-router-dom`, Next app/pages router, etc.) and any test-id conventions.
- Find the route-definition file (e.g. `App.tsx`, `routes.tsx`, Next `app/` tree).

### 2. Static analysis (the backbone)

Read client source only and extract:

- **Route / page map** — every route, its component, its purpose, and any **role/auth gating** (e.g. admin-only vs authenticated-only vs public). Get this from the router file's conditional rendering.
- **Navigation** — sidebar/nav/menu components: the human-readable link labels and grouping a user actually sees and clicks.
- **Personas & credentials** — login page + auth context + any test creds noted in `CLAUDE.md`/README. Capture role → login → what that role can reach.
- **Per-page user flows** — open each `pages/*` component and derive the primary flow as numbered user steps (the inputs, the primary button, the success/error feedback). One flow block per meaningful page.
- **UI selector hints & quirks** — `data-testid`s, ARIA labels, `id`s, element roles, and gotchas (e.g. "nav links are `<a>` tags → target by link role, not button"; feature-flagged button label variants). Pull quirks from code + any Testing Notes in `CLAUDE.md`.

### 3. Optional extra sources (`--sources`)

For each source, fetch/read it and extract only **business intent the UI can't reveal** — acceptance criteria, business rules, validation rules, conditional behaviors (e.g. "donation applies on withdraw only, not deposit"). Add these under an **Additional context** section with a citation back to the source. Never let a source pull you into documenting server internals.

### 4. Optional live-crawl pass (`--live`, or if a dev server is already running)

Using the `preview_*` MCP tools only:
- Start (or reuse) the dev server, log in with each persona, visit the key routes.
- Capture the **real rendered** labels/selectors and one screenshot per page.
- Reconcile against the static map; where they disagree, keep the live value and add a short `drift:` note.
- If the app can't be started (DB/server down), skip this phase gracefully — never block generation on it. Note in the doc that selectors are static-derived.

### 5. Synthesize & write

- Fill `template.md` (in this skill dir) with the gathered data and write to `--out`. Create parent dirs if needed.
- Keep it concise and scannable — this is agent instructions, not prose. Bullets and tables over paragraphs.
- Print a short summary: file path, # pages, # flows, personas found, whether live-crawl ran.
- Offer next step: hand the file to mabl as agent instructions, or pass it to `mabl-test-from-requirement`.

## Output

The file follows `template.md`:
1. App overview (name, purpose, theme, base URL, environments)
2. Personas & credentials
3. Page / route map (with role gating)
4. Core user flows (numbered steps)
5. UI conventions & selector hints
6. Known quirks / things to avoid
7. Additional context (only when `--sources` provided)
