# mabl-app-context-crawl — Kiro skill

The **black-box** sibling of [`mabl-app-context`](../mabl-app-context). It produces the same
application-context briefing for mabl's test-creation agent, but derived purely from a
**deployed instance in a real browser** — no source code required. Use it when you only
have a URL (a customer's app, a staging deploy, an app you don't have repo access to).

It logs in per persona, crawls the navigation to discover routes, and captures the rendered
pages, labels, selectors, and screenshots — seeing exactly what mabl's agent will see.

## Prerequisites

Shared setup is in [`../README.md`](../README.md). This skill additionally requires:

| Requirement | Why |
|-------------|-----|
| **`chrome-for-mabl` MCP server** connected | Drives the browser. Without it the skill stops — it will not silently fall back to the source-based sibling. |
| **A reachable deployed URL** | The crawl target |
| **At least one set of working credentials** | The crawl map is bounded by what a persona can open |

> The Claude Code original drives the *Claude in Chrome* MCP server, which has no Kiro
> equivalent. The Kiro port uses Chrome DevTools MCP instead; the full tool mapping is
> documented at the top of `SKILL.md`.

## Install

```bash
cp -r mabl-app-context-crawl ~/.kiro/skills/        # or <your-repo>/.kiro/skills/
```

The folder ships a `template.md` the skill fills in — keep it alongside `SKILL.md`.

## Usage

```
/mabl-app-context-crawl --url https://staging.example.com --personas "admin:admin:admin"
```

Or ask in plain language — *"bootstrap mabl context from this URL."*

### Arguments

| Arg | Meaning | Default |
|-----|---------|---------|
| `--url <url>` | Base URL of the deployed app | **required** |
| `--personas <label:user:pass,…>` | Login personas to crawl as | asks for at least one |
| `--out <path>` | Where to write the briefing | `docs/mabl/app-context.md` |
| `--safe-env` | Asserts the target is disposable/staging — permits executing non-destructive happy-path flows | off |
| `--max-depth <n>` | Link-crawl depth from each landing page | `2` |
| `--sources <a,b,…>` | Extra business context (files, Jira/Confluence URLs, pasted ACs) | none |

## ⚠️ Safety

This skill acts against a **live environment**, so it is read-first by default:

- It discovers flows by **inspecting** forms and buttons, not submitting them.
- Without `--safe-env` it **never** clicks a final submit. Flow assertions are recorded as
  `⚠️ inferred — not executed`.
- With `--safe-env` it may execute non-destructive happy paths, but still skips anything
  irreversible unless you name that flow as safe.
- **Never** point it at production.
- It logs out and closes the tabs it opened when finished.

If anything is ambiguous about whether an action is safe, it asks before acting.

## Good to know

- **The output flags its own blind spots.** A **Coverage & gaps** section lists routes the
  crawl couldn't reach and every flow left inferred-but-unexecuted, so the mabl agent knows
  what the doc doesn't cover.
- **Role gating shows up naturally** — routes one persona sees and another doesn't, or a
  redirect back to `/`, are recorded as access-control observations.
- **Weaker on completeness than the source-based sibling** (no route enumeration, no
  feature-flag awareness), **stronger at reflecting what mabl actually observes.**
- **Idempotent** — safe to re-run; it overwrites the output file.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
