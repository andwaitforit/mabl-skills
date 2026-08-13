# mabl Skills

A growing collection of **agent skills** that bring [mabl](https://www.mabl.com) into your
AI coding workflow — finding, running, and reasoning about mabl tests right from your
editor or terminal.

Skills follow the open [Agent Skills](https://kiro.dev/docs/skills/) standard (a `SKILL.md`
with YAML frontmatter), so the same workflows ship for more than one host. This repo keeps
one tree per host:

```
mabl-skills/
├── claude/     # Claude Code  →  install into .claude/skills/
└── kiro/       # Kiro         →  install into .kiro/skills/
```

Each tree has its own `README.md` with host-specific setup, and each skill has a `README.md`
with skill-specific usage and gotchas. Start there:

- **[`claude/`](claude)** — for [Claude Code](https://docs.claude.com/en/docs/claude-code)
- **[`kiro/`](kiro)** — for [Kiro](https://kiro.dev/docs/)

---

## Skills

| Skill | What it does | claude | kiro |
|-------|--------------|:------:|:----:|
| `mabl-pre-pr-check` | Analyzes your current commit, finds the mabl tests most relevant to what changed, and runs them locally for fast pre-PR feedback. | ✅ | ✅ |
| `mabl-app-context` | Generates an app-context briefing for mabl's test-creation agent from your **front-end source code** (pages, personas, flows, selectors, quirks). | ✅ | ✅ |
| `mabl-app-context-crawl` | Generates the same briefing by **crawling a deployed app** in a browser — no source needed (black-box sibling). | ✅ | ✅ |
| `mabl-failure-rca` | Root-causes a **failed test run** against the source: pulls mabl's AI analysis + artifacts (DOM, HAR, console), correlates with code, and classifies the failure. | ✅ | ✅ |
| `mabl-dom-sanitizer` | Strips executable JavaScript from a captured mabl DOM snapshot so it can be opened locally without the app forcing a logout/re-hydration. | ✅ | ✅ |
| `feature-dev` | Orchestrates the full **plan → build → test → ship** lifecycle for a feature — spec, Jira epic, browser-verified build, mabl test coverage, PR — by composing the other skills. 📋 Template. | ✅ | ✅ |
| _more coming_ | | | |

---

## Shared prerequisites

Every skill here (except `mabl-dom-sanitizer`, which is pure Python) builds on the same
foundation. Set these up once; the host-specific bits are in each tree's README.

### 1. A mabl account, workspace, and API key

You need access to a mabl workspace that already contains tests. Generate an **API key** in
the mabl app under **Settings → APIs** — you'll use it to authenticate both the CLI and the
MCP server.

### 2. The mabl CLI

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

### 3. The mabl MCP server

Skills that match your code to tests rely on the **mabl MCP server** for semantic test
search (`search_mabl_tests`, `list_mabl_workspaces`, `run_mabl_test_local`, …).

- **Claude Code** — `mabl agent install claude` adds the MCP entry (+ the `mabl-debug`
  skill) for you. See [`claude/README.md`](claude/README.md).
- **Kiro** — there is **no `kiro` install target**; add the server to
  `.kiro/settings/mcp.json` by hand. The exact JSON is in [`kiro/README.md`](kiro/README.md).

Either way, the hosted mabl MCP server can be added directly to any MCP client config. See
the mabl Help Center ("mabl cloud MCP server").

**Verify** it's connected by starting a session and confirming mabl tools are available.

### 4. Git

Skills that diff your changes assume the project is a git repository.

---

## Installing a skill

Copy the skill folder from the tree matching your host into the corresponding skills
directory:

| Host | User scope (all repos) | Project scope (one repo) |
|------|------------------------|--------------------------|
| Claude Code | `~/.claude/skills/<skill>/` | `<repo>/.claude/skills/<skill>/` |
| Kiro | `~/.kiro/skills/<skill>/` | `<repo>/.kiro/skills/<skill>/` |

```bash
# from a clone of this repo
cp -r claude/mabl-pre-pr-check ~/.claude/skills/
cp -r kiro/mabl-pre-pr-check   ~/.kiro/skills/
```

Both hosts require each skill in its **own subfolder** — a bare `SKILL.md` dropped directly
in `skills/` is not discovered. Then start a session and type `/` to confirm the skill is
listed, or invoke it directly, e.g. `/mabl-pre-pr-check`.

> **Tip:** prefer **user scope** if you work on feature branches. A project-scoped skill
> lives on the branch — cutting a fresh branch mid-task deletes it, and every skill suddenly
> resolves as unknown.

---

## Host differences worth knowing

The instruction bodies are ~90% identical between trees. The substantive divergences:

| Area | Claude Code | Kiro |
|------|-------------|------|
| **Long-running commands** | Backgrounded; the harness re-invokes the agent when the process exits | Blocking — Kiro waits and hands back stdout. Short runs go foreground; long ones are `nohup`-detached and polled. |
| **Planning** | Explore/Plan subagents, plan mode | The [spec workflow](https://kiro.dev/docs/specs/) — `.kiro/specs/<feature>/{requirements,design,tasks}.md` |
| **Browser automation** | *Claude in Chrome* MCP | Chrome DevTools MCP (`chrome-for-mabl`) |
| **Repo conventions** | `CLAUDE.md` | [`.kiro/steering/`](https://kiro.dev/docs/steering/) |
| **Frontmatter** | `name`, `description`, `allowed-tools` | `name`, `description` (≤1024 chars), `metadata`, `compatibility`, `license` — no `allowed-tools` |

Full detail in [`kiro/README.md`](kiro/README.md#what-changed-from-the-claude-code-originals).

---

## Contributing a new skill

1. Create `<host>/<your-skill-name>/SKILL.md`. The frontmatter must include a `name` (which
   must match the folder name) and a `description` — the description is how the agent
   decides when to use the skill, so make it trigger-rich (include the phrases a user would
   actually say):

   ```markdown
   ---
   name: my-mabl-skill
   description: >-
     One or two sentences on what it does, plus the phrasings that should trigger it
     ("run mabl X", "check Y in mabl", …).
   ---

   # Instructions for the model…
   ```

2. Add a `<host>/<your-skill-name>/README.md` with prerequisites *beyond* the shared ones,
   usage, and any gotchas.
3. **Port it to the other tree** if the workflow isn't host-specific, and note any
   divergence in that tree's README.
4. **Keep it portable** — no hardcoded workspace/test/application IDs, URLs, or
   customer-specific values. Resolve those at runtime (via the mabl MCP
   `list_mabl_workspaces` / `search_mabl_tests` tools or CLI config) so the skill works in
   any workspace.
5. Add a row to the **Skills** table above.
6. Open a PR.

Conventions: kebab-case skill names, one folder per skill per host, prefer the mabl MCP
tools for discovery and the mabl CLI for local execution.

---

## Links

- [mabl CLI reference](https://help.mabl.com/docs/mabl-cli)
- [mabl Help Center](https://help.mabl.com)
- [Claude Code documentation](https://docs.claude.com/en/docs/claude-code)
- [Kiro documentation](https://kiro.dev/docs/) · [Agent Skills](https://kiro.dev/docs/skills/)

## License

_Add a license before publishing (MIT is a common choice for shareable tooling)._
