# mabl-app-context — Claude Code skill

Generates an **application-context briefing** for mabl's test-creation agent from your app's
**front-end source code**. The output (default `docs/mabl/app-context.md`) describes the app's
pages/routes, personas & credentials, core user flows, UI selector conventions, and known
quirks — everything the mabl browser agent needs as a mental model, derived **client-side only**
(it never reads server/DB code).

Hand the file to mabl as agent instructions, or feed it to the `mabl-test-from-requirement` skill.

## Prerequisites

- The app's **front-end source** available locally (default root `client/src`; auto-detected
  for Vite/React, Next, Vue, Svelte).
- This skill does **not** require the mabl CLI or mabl MCP server.
- Optional `--live` pass uses browser/preview MCP tools and a running dev server to verify
  selectors and capture screenshots — skipped gracefully if the app can't start.

## Usage

```
/mabl-app-context
/mabl-app-context --client-root src --out docs/mabl/app-context.md --live
```

| Arg | Default | Meaning |
|---|---|---|
| `--client-root <path>` | `client/src` | Front-end source root to analyze |
| `--out <path>` | `docs/mabl/app-context.md` | Where to write the briefing |
| `--sources <a,b,…>` | none | Extra business context the UI can't reveal (files, Jira/Confluence URLs, pasted ACs) |
| `--live` | off | Also drive the running app to verify selectors + capture screenshots |

## Good to know

- **Client-only by design.** It deliberately ignores `server/`, Prisma, and DB code — if the
  browser agent can't observe it, it doesn't belong in the doc. Business rules that aren't
  visible in the UI come in via `--sources`.
- **Doesn't invent flows** — ambiguous behavior is marked `⚠️ needs confirmation`.
- **Idempotent** — safe to re-run; overwrites the output file.

## Sibling skill

Use [`mabl-app-context-crawl`](../mabl-app-context-crawl) when you **don't have the repo** —
it produces the same briefing by crawling a deployed instance in a browser. The two write the
same template and are interchangeable downstream.
