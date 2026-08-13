# feature-dev — Kiro skill (template)

The **conductor**. Takes a feature from a one-line request to PR-ready, with a Kiro spec
plus a Jira Epic documenting the intent and mabl proving the result:

| Phase | What happens |
|-------|--------------|
| **1 — Plan** | Explore the code, write a Kiro spec (`requirements.md` with EARS criteria, `design.md` naming the `data-testid`s, `tasks.md`), create the Jira Epic, confirm scope |
| **2 — Build** | Work `tasks.md`, build + type-check, then **browser-verify the real app** with a screenshot |
| **3 — Test** | Find existing mabl coverage, author what's missing, resolve credentials, run locally, triage failures with a live step-through |
| **4 — Ship** | Analyze every failed run, summarize, and — on your go — commit against the Epic and open the PR |

It composes the other skills in this tree (`mabl-pre-pr-check`, `mabl-failure-rca`) rather
than reimplementing them.

## 📋 This is a template

`SKILL.md` ships with `<PLACEHOLDER>` values. Before using it:

1. Fill in the **Project constants** table — the "How to find it" column tells you where
   each value comes from (mabl MCP calls, Atlassian MCP calls, your app).
2. Swap the build / type-check / dev-server commands in Phases 2–3 for your repo's.
3. Generalize or delete the app-specific gotchas at the bottom that don't apply to your
   stack — but keep the principles; they're the expensive part.
4. Consider parking the constants table in `.kiro/steering/mabl.md` (`inclusion: manual`)
   so other skills and ad-hoc chats can pull it in with `#mabl`.

## Prerequisites

Shared setup is in [`../README.md`](../README.md). This skill needs the most of any in the
tree:

| Requirement | Used for |
|-------------|----------|
| **mabl CLI** authenticated | Local test runs and authoring sessions |
| **`mabl` MCP server** | Test search, credentials/environments, run status, failure analysis |
| **`chrome-for-mabl` MCP server** | Phase 2 browser verification, Phase 3 live triage |
| **`Atlassian` MCP server** | Creating and updating the Jira Epic (skip Phase 1.3 if you don't use Jira) |
| **Local dev server** | Everything in Phases 2–3 runs against it |

## Install

```bash
cp -r feature-dev ~/.kiro/skills/        # or <your-repo>/.kiro/skills/
```

## Usage

```
/feature-dev add a recent-activity card to the portfolio page
```

Kiro will walk Phases 1→4, pausing to confirm the spec before building and the PR decision
before shipping. It never opens or merges a PR on its own.

## Why the spec matters for test quality

Phase 1 asks you to name the `data-testid`s in `design.md`, and that isn't bookkeeping.
mabl's authoring agent gets steps **right** when it's handed a literal selector
(`button[aria-label="Remove Sweetums"]`) and **guesses** when it's handed intent
("un-track Sweetums") — in one observed run it generated a click on the *add* button for an
unrelated stock, inside an `IF` branch that never executed during authoring, so validation
passed and the defect would have shipped silently. Writing the selectors down in Phase 1 is
what makes Phase 3 reliable.

## Kiro-specific notes

- **Long commands block.** A local test run (1–5 min) goes in the foreground and Kiro reads
  the result directly. An authoring session (**budget 30–45 min**, not the documented 5–20)
  must be `nohup`-detached and polled on a later turn.
- **Install at user scope if you work on feature branches.** A workspace-scoped copy lives
  on the branch; cutting a fresh branch mid-feature deletes it and every skill in the chain
  resolves as unknown.
- **Never `grep` an authoring or run log raw** — they embed base64 screenshots. Filter with
  `awk 'length($0) < 300'` first.

---

*Built by a mabl Solutions Engineer. Questions → your mabl contact.*
