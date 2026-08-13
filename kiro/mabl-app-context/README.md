# mabl-app-context — Kiro skill

Generate the **application-context briefing** that mabl's test-creation agent needs, from
your front-end source code. The output is a single markdown file describing:

- what pages/routes exist and who can reach them,
- the personas and their credentials,
- the core user flows as numbered steps,
- the selector conventions mabl should target,
- the quirks worth avoiding (dynamic text, role-gated labels, filtered lists).

Hand the file to mabl as agent instructions, or feed it to `mabl-test-from-requirement`.

## Client-only, by design

The agent that consumes this file **only sees the browser**, so the skill reads only your
front-end source (default `client/src`) and never opens `server/`, the ORM schema, or DB
code. Business rules that aren't visible in the UI come in through `--sources`, cited —
not by reading the backend.

## Prerequisites

Shared setup is in [`../README.md`](../README.md). This skill needs **no MCP server** for
its default static pass. The optional `--live` pass needs `chrome-for-mabl` connected and a
running dev server.

## Install

```bash
cp -r mabl-app-context ~/.kiro/skills/        # or <your-repo>/.kiro/skills/
```

The folder ships a `template.md` the skill fills in — keep it alongside `SKILL.md`.

## Usage

```
/mabl-app-context
```

Defaults to `client/src` → `docs/mabl/app-context.md`. Or ask in plain language —
*"generate mabl agent context for this app."*

### Optional arguments

| Arg | Meaning | Default |
|-----|---------|---------|
| `--client-root <path>` | Front-end source root to analyze | `client/src` (auto-detected if absent) |
| `--out <path>` | Where to write the briefing | `docs/mabl/app-context.md` |
| `--sources <a,b,…>` | Extra context: files, doc folders, Jira/Confluence URLs, pasted ACs | none |
| `--live` | Also drive the running app to verify selectors + capture screenshots | off |

## Good to know

- **Idempotent** — safe to re-run; it overwrites the output file.
- **It won't invent flows.** Where a page's behavior is ambiguous from source, the step is
  marked `⚠️ needs confirmation` rather than guessed.
- **Personas come from your repo's agent context.** In Kiro that's `.kiro/steering/`
  (`product.md`, `tech.md`, `structure.md`, or a project-specific doc); it also checks
  `AGENTS.md` / `README.md`.
- **Drift is reported, not resolved.** If `--live` disagrees with the static map, the live
  value wins and a short `drift:` note is added.
- **Portable** across Vite/React/Next client apps; defaults are tuned for Vite + React Router.

## Sibling skill

[`mabl-app-context-crawl`](../mabl-app-context-crawl) produces the **same** document by
crawling a deployed app in a browser — use it when you don't have the repo. The two are
interchangeable; they share `template.md`.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
