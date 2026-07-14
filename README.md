# mabl Skills for Claude Code

A growing collection of [Claude Code](https://docs.claude.com/en/docs/claude-code) **skills**
that bring [mabl](https://www.mabl.com) into your AI coding workflow — finding, running, and
reasoning about mabl tests right from your editor or terminal.

Each skill is self-contained and portable: drop it into your `.claude/skills/` directory and
Claude Code discovers it automatically.

---

## Skills

| Skill | What it does | Status |
|-------|--------------|--------|
| [`mabl-pre-pr-check`](mabl-pre-pr-check) | Analyzes your current commit, finds the mabl tests most relevant to what changed, and runs them locally for fast pre-PR feedback. | ✅ Stable |
| [`mabl-app-context`](mabl-app-context) | Generates an app-context briefing for mabl's test-creation agent from your **front-end source code** (pages, personas, flows, selectors, quirks). | ✅ Stable |
| [`mabl-app-context-crawl`](mabl-app-context-crawl) | Generates the same briefing by **crawling a deployed app** in a browser — no source needed (black-box sibling). | ✅ Stable |
| [`mabl-failure-rca`](mabl-failure-rca) | Root-causes a **failed test run** against the source: pulls mabl's AI analysis + artifacts (DOM, HAR, console), correlates with code, and classifies the failure. | ✅ Stable |
| [`mabl-dom-sanitizer`](mabl-dom-sanitizer) | Strips executable JavaScript from a captured mabl DOM snapshot so it can be opened locally without the app forcing a logout/re-hydration. | ✅ Stable |
| [`feature-dev`](feature-dev) | Orchestrates the full **plan → build → test → ship** lifecycle for a feature — Jira epic, browser-verified build, mabl test coverage, PR — by composing the other skills. | 📋 Template (fill in placeholders) |
| _more coming_ | | |

> Each skill has its own `README.md` with skill-specific usage and notes. This top-level
> README covers the shared setup every skill depends on.

---

## Prerequisites

Most skills here share the same foundation: **Claude Code**, the **mabl CLI**, and the
**mabl MCP server**. Set these up once.

### 1. Claude Code

Install and sign in to Claude Code (CLI, desktop, or an IDE extension). See the
[Claude Code docs](https://docs.claude.com/en/docs/claude-code).

### 2. A mabl account, workspace, and API key

You need access to a mabl workspace that already contains tests. Generate an **API key** in
the mabl app under **Settings → APIs** — you'll use it to authenticate both the CLI and the
MCP server.

### 3. The mabl CLI

The CLI runs tests locally and exposes workspace/test/plan commands. It's distributed on npm
(requires Node.js 18+); there is **no Homebrew formula**.

```bash
# install
npm install -g @mablhq/mabl-cli

# authenticate (either interactive login or an API key)
mabl auth login
#   …or, for headless / CI:
mabl auth activate-key <your-api-key>

# verify
mabl --version
mabl auth info
```

Full CLI reference: <https://help.mabl.com/docs/mabl-cli>

### 4. The mabl MCP server

Skills that match your code to tests rely on the **mabl MCP server** for semantic test search
(`get_mabl_tests`, `get_workspaces`, `run_mabl_test_local`, etc.). Connect it to Claude Code one
of these ways:

- **Via the CLI helper (easiest):**
  ```bash
  mabl agent install <target>     # e.g. claude-code — adds the mabl MCP entry (+ debug skill)
  ```
- **Cloud MCP server:** the hosted mabl MCP can be added directly to your MCP client config
  without going through the CLI. See the mabl Help Center ("mabl cloud MCP server").

**Verify** it's connected by starting a session and confirming mabl tools are available (in
Claude Code, run `/mcp` or check that `mabl` appears as a connected server).

### 5. Git

Skills that diff your changes assume the project is a git repository.

---

## Installing a skill

Copy a skill folder into one of:

- **User scope (all your repos):** `~/.claude/skills/<skill-name>/`
- **Project scope (one repo, shareable with your team):** `<repo>/.claude/skills/<skill-name>/`

For example:

```bash
# from a clone of this repo
cp -r mabl-pre-pr-check ~/.claude/skills/
```

Then start Claude Code and type `/` to confirm the skill is listed, or invoke it directly,
e.g. `/mabl-pre-pr-check`.

---

## Repository structure

```
mabl-skills/
├── README.md                     # this file — shared setup + catalog
└── mabl-pre-pr-check/            # one folder per skill
    ├── SKILL.md                  # the skill definition (frontmatter + instructions)
    └── README.md                 # skill-specific usage
```

---

## Contributing a new skill

1. Create `<your-skill-name>/SKILL.md`. The frontmatter must include a `name` and a
   `description` — the description is how Claude decides when to use the skill, so make it
   trigger-rich (include the phrases a user would actually say):

   ```markdown
   ---
   name: my-mabl-skill
   description: >-
     One or two sentences on what it does, plus the phrasings that should trigger it
     ("run mabl X", "check Y in mabl", …).
   ---

   # Instructions for the model…
   ```

2. Add a `<your-skill-name>/README.md` with prerequisites *beyond* the shared ones,
   usage, and any gotchas.
3. **Keep it portable** — no hardcoded workspace/test/application IDs, URLs, or
   customer-specific values. Resolve those at runtime (via the MCP `get_workspaces` /
   `get_mabl_tests` tools or CLI config) so the skill works in any workspace.
4. Add a row to the **Skills** table above.
5. Open a PR.

Conventions: kebab-case skill names, one folder per skill, prefer the mabl MCP tools for
discovery and the mabl CLI for local execution.

---

## Links

- [mabl CLI reference](https://help.mabl.com/docs/mabl-cli)
- [mabl Help Center](https://help.mabl.com)
- [Claude Code documentation](https://docs.claude.com/en/docs/claude-code)

## License

_Add a license before publishing (MIT is a common choice for shareable tooling)._
