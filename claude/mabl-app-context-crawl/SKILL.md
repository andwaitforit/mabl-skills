---
name: mabl-app-context-crawl
description: Generate a client-side application-context briefing for mabl's test-creation agent by crawling a DEPLOYED instance of the app in a real browser — no source code required. Logs in per persona, discovers routes by crawling navigation, and captures rendered pages/labels/selectors/screenshots, then writes a markdown file (default docs/mabl/app-context.md) describing pages, personas, core user flows, UI selectors, and quirks. Use when the user wants to "bootstrap mabl context from a URL", "generate app context from the deployed site", "crawl the app for mabl agent instructions", or has no repo access. Black-box sibling of the source-based `mabl-app-context` skill; produces the same template so the two are interchangeable.
---

# Generate client-side app context for the mabl test agent — by crawling a deployed app

Use this skill to produce the same app-context briefing as `mabl-app-context`, but derived **purely from a running, deployed instance in a browser** — no source code. This is the black-box path: it sees exactly what mabl's agent sees, which makes it the right tool when you don't have the repo (e.g. a customer's app).

The output is a hand-off artifact: paste it into mabl as agent instructions, or feed it to `mabl-test-from-requirement`.

## Required tooling

This skill drives a real browser via the **Claude in Chrome** MCP server (`mcp__Claude_in_Chrome__*`). If it isn't connected, tell the user to connect it (`/mcp`) and stop — do **not** fall back to the source-based skill silently. Tools used: `list_connected_browsers`/`select_browser`, `navigate`, `read_page`, `get_page_text`, `find`, `read_network_requests`, `read_console_messages`, and `form_input`/`computer` only when a safe interaction is required (see guardrails).

## Core principles

- **Observe, don't assume.** Document only what the deployed app actually renders for the credentials you were given. Anything you couldn't reach, mark `⚠️ not reached` rather than inventing it.
- **The credentials bound the map.** You can only document pages a persona can actually open. Note which persona reached each page, and explicitly list routes/areas you could not access.
- **Selectors are observed, not authoritative.** Capture the real `data-testid`, `id`, `aria-label`, link text, and roles you see. Flag where a label looks dynamic (changes per record/time) so tests don't pin to it.
- **Idempotent.** Safe to re-run; overwrites the output file.

## ⚠️ Safety guardrails — read before crawling

You are acting against a **live environment**. Treat every state-changing action as risky.

- **Read-first crawl.** Prefer navigation + reading. Discover flows by inspecting forms/buttons, not by submitting them.
- **Never submit destructive or irreversible actions** — money transfers, deposits/withdrawals, account creation/deletion, policy submit/delete, anything that emails/charges/notifies — UNLESS the user passed `--safe-env` confirming a disposable/seed/staging environment. **Never** on production.
- When `--safe-env` is NOT set: document the flow steps from the rendered form (fields, primary button, expected result inferred from labels) and mark the assertion `⚠️ inferred — not executed`. Do not click the final submit.
- When `--safe-env` IS set: you may execute non-destructive happy-path flows to confirm success/error text, but still skip anything that deletes data or can't be undone unless the user explicitly named that flow as safe.
- **Log out / clean up** sessions you opened when finished.
- If anything is ambiguous about whether an action is safe, **ask before acting** — don't guess.

## Arguments

| Arg | Default | Meaning |
|---|---|---|
| `--url <url>` | (required) | Base URL of the deployed app |
| `--personas <label:user:pass,...>` | ask the user | One or more login personas to crawl as. If omitted, ask for at least one. |
| `--out <path>` | `docs/mabl/app-context.md` | Where to write the briefing |
| `--safe-env` | off | Asserts the target is disposable/staging — permits executing non-destructive happy-path flows |
| `--max-depth <n>` | `2` | Link-crawl depth from each post-login landing page |
| `--sources <a,b,...>` | none | Extra business context (files, Jira/Confluence URLs, pasted ACs) |

If `--url` is missing, ask for it. If no personas are given, ask for at least one (and confirm whether the env is safe).

## Workflow

Track phases with TaskCreate/TaskUpdate.

### 1. Connect & confirm scope
- `list_connected_browsers` → `select_browser`. If none, stop and ask the user to connect Claude in Chrome.
- Confirm the target URL and **whether it's a safe/disposable environment**. If the user can't confirm it's safe, operate in read-only mode (no final submits) regardless of `--safe-env`.

### 2. Log in per persona
For each persona: `navigate` to `--url`, locate the login form (`find` / `read_page`), fill username + password (`form_input`), submit, and confirm landing. Logging in is the one expected state change; if a persona's creds fail, note it and continue with the others. Capture the login page's selectors before authenticating.

### 3. Discover routes (BFS link crawl)
From each persona's landing page:
- `read_page` to enumerate nav/sidebar/menu links and their visible text + hrefs.
- Visit each in-app link up to `--max-depth`, deduping by path. Record which persona could reach each route (role gating shows up as routes one persona sees and another doesn't, or redirects).
- Note redirects (e.g. a client hitting an admin route bouncing to `/`) as access-control observations.

### 4. Capture each page
Per reached page:
- `get_page_text` + `read_page` for headings, section titles, and the primary purpose.
- Enumerate **forms** (fields with their labels/names/ids/types), **primary buttons**, and stable hooks (`data-testid`, `id`, `aria-label`, roles, link text).
- Derive the page's **primary user flow** as numbered steps from the observed form + primary action. Mark the success/error assertion `⚠️ inferred — not executed` unless you actually executed it under `--safe-env`.
- Take a `screenshot` (via `computer`) for the page; note the saved reference in the doc.
- Watch `read_console_messages` / `read_network_requests` for obvious errors or the API shape (useful selector/quirk notes) — but never document server internals beyond what the browser exposes.

### 5. Optional extra sources (`--sources`)
Same as the source-based skill: fold in business rules the UI can't reveal, cited, under "Additional context".

### 6. Synthesize & write
- Fill `template.md` (in this skill dir) and write to `--out` (create parent dirs).
- In the generation note, state it was **crawled from `<url>`**, which personas were used, env safety mode, and crawl depth.
- Add a **Coverage & gaps** note listing routes/areas not reached and any flows left `inferred — not executed`, so the mabl agent knows the doc's blind spots.
- Print a summary: file path, # pages reached, # flows, personas used, executed-vs-inferred counts.
- Offer next step: hand to mabl as agent instructions, or to `mabl-test-from-requirement`.
- Clean up: log out the sessions you opened.

## Output

Follows `template.md` (overview, personas & credentials, page/route map, core user flows, UI conventions & selector hints, known quirks, additional context) — identical structure to `mabl-app-context`, plus a **Coverage & gaps** subsection noting blind spots inherent to black-box crawling.

## Relationship to `mabl-app-context`
- `mabl-app-context` = static source analysis (+ optional live verify). Best when you have the repo: complete route enumeration, flag-variant awareness.
- `mabl-app-context-crawl` (this skill) = pure black-box browser crawl. Best when you only have a URL. Weaker on completeness and runtime-flag awareness; stronger at reflecting exactly what mabl observes.
