# mabl Skills for Kiro

Kiro ports of the skills in [`../claude`](../claude). Kiro implements the open
[Agent Skills](https://kiro.dev/docs/skills/) standard, so the `SKILL.md` format is the
same — these are host-adapted copies, not rewrites.

| Skill | What it does |
|-------|--------------|
| [`mabl-pre-pr-check`](mabl-pre-pr-check) | Maps your diff to the mabl tests that cover it and runs them locally before you open the PR. |
| [`mabl-app-context`](mabl-app-context) | Generates an app-context briefing for mabl's test-creation agent from your **front-end source**. |
| [`mabl-app-context-crawl`](mabl-app-context-crawl) | Generates the same briefing by **crawling a deployed app** in a browser — no source needed. |
| [`mabl-failure-rca`](mabl-failure-rca) | Root-causes a **failed run** against the source: mabl's AI analysis + artifacts (DOM, HAR, console), classified. |
| [`mabl-dom-sanitizer`](mabl-dom-sanitizer) | Strips executable JS from a captured mabl DOM snapshot so it opens locally without forcing a logout. |
| [`feature-dev`](feature-dev) | Conductor: plan → build → test → ship, built on Kiro specs + Jira + mabl. 📋 Template — fill in placeholders. |

---

## Install

Skills live in one of two scopes; workspace wins on a name clash.

```bash
# User scope — available in every project
cp -r mabl-pre-pr-check ~/.kiro/skills/

# Workspace scope — one repo, shareable with the team
cp -r mabl-pre-pr-check <your-repo>/.kiro/skills/
```

Kiro requires each skill in its **own subfolder** — a bare `SKILL.md` dropped directly in
`skills/` is not recognized. Kiro loads only each skill's `name` + `description` up front
and pulls in the full instructions when one activates, so installing all six is cheap.

Skills activate two ways: automatically, when Kiro matches your request against the
description, or explicitly by typing `/` and picking one.

> ⚠️ If you work on feature branches, prefer the **user scope**. A workspace-scoped skill
> lives on the branch — cutting a fresh branch mid-task deletes it and every skill
> suddenly resolves as unknown.

## Prerequisites

**1. mabl CLI** (Node 18+; no Homebrew formula):

```bash
npm install -g @mablhq/mabl-cli
mabl auth login                      # or: mabl auth activate-key <api-key>
mabl --version && mabl auth info     # verify
```

**2. MCP servers.** There is **no `mabl agent install kiro`** target — the CLI's installer
supports claude · cursor · vscode · copilot · agents-md, so the Kiro entries are added by
hand. Create `.kiro/settings/mcp.json` (workspace) or `~/.kiro/settings/mcp.json` (global),
then connect the servers from Kiro's **MCP Servers** panel:

```jsonc
{
  "mcpServers": {
    "mabl": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote", "https://mcp.mabl.com/mcp",
        "--header", "x-api-key:${MABL_API_KEY}"
      ],
      "disabled": false,
      "autoApprove": [
        "search_mabl_tests", "list_mabl_workspaces", "list_mabl_environments",
        "list_mabl_credentials", "get_mabl_test", "get_mabl_test_run",
        "list_mabl_test_runs"
      ]
    },
    "chrome-for-mabl": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"],
      "disabled": false,
      "autoApprove": ["take_snapshot", "take_screenshot", "list_pages"]
    },
    "Atlassian": {
      "url": "https://mcp.atlassian.com/v1/sse",
      "disabled": false
    }
  }
}
```

Generate the API key in the mabl app under **Settings → APIs**. Don't commit the filled-in
file. `Atlassian` is only needed by `feature-dev`; `chrome-for-mabl` by
`feature-dev`, `mabl-app-context-crawl`, and the optional `--live` pass of
`mabl-app-context`.

| Server | Needed by |
|--------|-----------|
| `mabl` | `mabl-pre-pr-check`, `mabl-failure-rca`, `feature-dev` |
| `chrome-for-mabl` | `mabl-app-context-crawl`, `feature-dev`, `mabl-app-context --live` |
| `Atlassian` | `feature-dev` |
| _(none)_ | `mabl-dom-sanitizer` — pure Python 3 |

**3. Git**, for the skills that diff your changes.

---

## What changed from the Claude Code originals

The instruction bodies are ~90% identical. These are the substantive edits:

| Area | Claude Code | Kiro |
|------|-------------|------|
| **Long-running commands** | `run_in_background: true`; the harness re-invokes the agent when the process exits | Kiro **blocks** on a foreground command and hands back stdout — there is no completion callback. Test runs (1–5 min) go foreground; authoring sessions (30–45 min) use `nohup … &` + poll on a later turn. This is the single biggest behavioral difference. |
| **Planning** | Explore/Plan subagents, `ExitPlanMode`, `AskUserQuestion` | Kiro **spec workflow** — `feature-dev` Phase 1 writes `.kiro/specs/<feature>/{requirements,design,tasks}.md` with EARS acceptance criteria, then executes `tasks.md` in Phase 2 |
| **Browser automation** | *Claude in Chrome* MCP (`list_connected_browsers`, `navigate`, `read_page`, `find`, `form_input`, `computer`) | `chrome-for-mabl` / Chrome DevTools MCP (`list_pages`, `navigate_page`, `take_snapshot`, `fill_form`, `take_screenshot`). Full mapping is documented in `mabl-app-context-crawl/SKILL.md`. |
| **Repo conventions** | `CLAUDE.md` | `.kiro/steering/` (`product.md` / `tech.md` / `structure.md`, or a `#`-referenced manual doc) |
| **Frontmatter** | `name`, `description`, `allowed-tools` | `name`, `description` (≤1024 chars), plus Kiro's `metadata` / `compatibility` / `license`. `allowed-tools` is **not** supported — capability limits are expressed in `compatibility` prose. |
| **MCP setup** | `mabl agent install claude`, `/mcp` to verify | hand-written `.kiro/settings/mcp.json`; verify in the MCP Servers panel |
| **Task tracking** | `TaskCreate` / `TaskUpdate` | the spec's `tasks.md` checklist |
| **Scratch files** | session scratchpad dir | `$HOME/.kiro/tmp/` or `mktemp -d` |

### Known divergence

The Kiro copies use the **current** mabl MCP tool names; the `claude/` tree still carries
older ones (`get_mabl_tests`, `get_latest_test_runs`, `analyze_failure`, `get_workspaces`,
`get_credentials`, `get_mabl_test_details`, `get_environments`, `get_plan_run_result`,
`mabl_result_analysis_chat`, `edit_mabl_test`). The current names are `search_mabl_tests`,
`list_mabl_test_runs`, `analyze_mabl_failure`, `list_mabl_workspaces`,
`list_mabl_credentials`, `get_mabl_test`, `list_mabl_environments`, `get_mabl_plan_run`,
`analyze_mabl_results`, `edit_mabl_test_metadata`. Worth backporting to `claude/`.

---

## Links

- [Kiro Agent Skills](https://kiro.dev/docs/skills/) · [Kiro steering](https://kiro.dev/docs/steering/) · [Kiro specs](https://kiro.dev/docs/specs/)
- [mabl CLI reference](https://help.mabl.com/docs/mabl-cli) · [mabl Help Center](https://help.mabl.com)
