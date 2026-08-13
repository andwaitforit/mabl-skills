# mabl-app-context-crawl — Claude Code skill

Generates an **application-context briefing** for mabl's test-creation agent by **crawling a
deployed instance of the app in a real browser — no source code required**. It logs in per
persona, discovers routes by crawling navigation, and captures rendered pages, labels,
selectors, and screenshots, then writes the briefing (default `docs/mabl/app-context.md`).

This is the **black-box** path: it sees exactly what mabl's agent sees, making it the right
tool when you don't have the repo (e.g. a customer's app). Hand the output to mabl as agent
instructions, or feed it to the `mabl-test-from-requirement` skill.

## Prerequisites

- The **Claude in Chrome** MCP server connected (`mcp__Claude_in_Chrome__*`). If it isn't, the
  skill stops and asks you to connect it (`/mcp`) — it will not silently fall back to the
  source-based skill.
- A reachable **deployed URL** and at least one **login persona** (label + credentials).
- This skill does **not** require the mabl CLI or mabl MCP server.

## Usage

```
/mabl-app-context-crawl --url https://staging.example.com --personas "client:user@example.com:pass"
```

| Arg | Default | Meaning |
|---|---|---|
| `--url <url>` | **required** | Base URL of the deployed app |
| `--personas <label:user:pass,…>` | asks you | Login personas to crawl as |
| `--out <path>` | `docs/mabl/app-context.md` | Where to write the briefing |
| `--safe-env` | off | Asserts the target is disposable/staging — permits executing non-destructive happy-path flows |
| `--max-depth <n>` | `2` | Link-crawl depth from each post-login landing page |
| `--sources <a,b,…>` | none | Extra business context (files, Jira/Confluence URLs, pasted ACs) |

## ⚠️ Safety — it operates against a live environment

- **Read-first crawl.** Flows are discovered by inspecting forms/buttons, not submitting them.
- **Never submits destructive or irreversible actions** (transfers, deposits/withdrawals,
  create/delete, anything that charges/emails) unless you pass `--safe-env` to confirm a
  disposable/staging target — **never on production**.
- Without `--safe-env`, flow assertions are documented but marked `⚠️ inferred — not executed`.
- It logs out the sessions it opens when finished.

## Good to know

- Output includes a **Coverage & gaps** section listing routes/areas not reached and flows
  left inferred — so the mabl agent knows the doc's blind spots.
- **Idempotent** — safe to re-run; overwrites the output file.

## Sibling skill

Use [`mabl-app-context`](../mabl-app-context) when you **have the repo** — it derives the same
briefing from front-end source (more complete route enumeration, flag-variant awareness). The
two write the same template and are interchangeable downstream.
