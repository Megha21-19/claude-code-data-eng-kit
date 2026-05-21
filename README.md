# claude-code-data-eng-kit

A minimal, opinionated Claude Code setup for data-engineering teams running PySpark on Databricks with a medallion (bronze / silver / gold) lakehouse.

This repo is not a framework. It's the smallest configuration I'd commit to a real data platform repo to make Claude Code a competent engineering partner — not a clever autocomplete. Every file in `.claude/` answers one question: *what does Claude need to know, do, or be stopped from doing, to be useful on a real pipeline PR?*

> **Why this exists.** Most Claude Code demos show one primitive in isolation. In a production data repo you need all of them composing: rules so Claude writes idiomatic PySpark, skills so common workflows are one prompt away, sub-agents so reviews don't pollute the main context, hooks so prod is genuinely protected, and an MCP server so Claude can see real cluster/job state instead of guessing. This is that composition.

---

## TL;DR — what's in here and why

| Layer | File / Path | What it does | Why it exists |
|---|---|---|---|
| **Memory** | `CLAUDE.md` | Project-wide conventions Claude loads on every session | Stable rules belong here, not in chat. Compaction loses chat; this survives. |
| **Path-scoped rules** | `.claude/rules/pyspark.md`, `medallion.md` | Auto-loaded when Claude opens files in matching paths | Keeps `CLAUDE.md` short. PySpark idioms only matter when editing PySpark. |
| **Skills** | `.claude/skills/*/SKILL.md` | Packaged workflows: `new-bronze-ingest`, `promote-to-silver`, `dq-check`, `prompt-eval` | Repeatable multi-step jobs that benefit from progressive disclosure. Invoked by name or auto-triggered by description match. |
| **Slash command** | `.claude/commands/ship-checklist.md` | `/ship-checklist` — pre-PR gate I run manually | A skill is auto-discoverable; a command is for things I want to invoke deliberately, never accidentally. |
| **Sub-agents** | `.claude/agents/pipeline-reviewer.md`, `cost-watchdog.md`, `eval-runner.md` | Specialized reviewers spawned in fresh context | Code review burns tokens and pollutes the main thread. A sub-agent with `Read+Grep+Bash` (no `Write`) keeps reviews clean and capability-narrowed. |
| **Hooks** | `.claude/hooks/*.sh` + `.claude/settings.json` | Deterministic guardrails: block prod writes, run lint/typecheck after edits, inject branch context at session start | Rules in `CLAUDE.md` are advisory. Hooks are enforced. Exit code 2 on a `PreToolUse` hook is the only thing Claude actually cannot ignore. |
| **MCP server** | `mcp-servers/databricks_mini/` + `.mcp.json` | Read-only Databricks introspection: list jobs, get run status, cluster state | Without this, Claude guesses at job names and run IDs. With it, every pipeline question starts from ground truth. Read-only by design — see below. |
| **Settings** | `.claude/settings.json` | Permissions, hooks wiring, MCP wiring | Project-scoped so the whole team gets the same gates. `settings.local.json` is for personal overrides and `.gitignore`'d. |

---

## Design principles (the opinions that drove the file choices)

**1. Memory is layered, not monolithic.** `CLAUDE.md` is under 300 tokens on purpose — global truths only. Path-scoped rules in `.claude/rules/` carry the long explanations and load only when relevant. This stops Claude from reading PySpark conventions when it's editing a YAML file.

**2. A skill is for a workflow; a slash command is for a ritual.** Skills are progressively disclosed and Claude can pull them in itself when it sees a matching task. Slash commands are explicit user-triggered actions. I use slash commands for things I want a human to consciously kick off (`/ship-checklist`) and skills for things Claude should reach for when the task description matches (`new-bronze-ingest`).

**3. Sub-agents narrow capability, not just parallelize work.** `pipeline-reviewer` has no `Write` or `Edit` tools. It can read, grep, and run read-only Bash. That's not because review needs less compute — it's because a code review that can edit the code under review is a bad code review. Sub-agents are the cheapest way to give Claude a least-privilege boundary.

**4. Hooks are the enforcement layer.** Advisory rules in CLAUDE.md tell Claude what not to do. Hooks make it impossible. The `pre-tool-protect-prod.sh` hook exits 2 on any write to a path matching `**/prod/**` or any Bash command containing `--target-env prod`. There is no prompt that talks Claude past this — the tool call never executes.

**5. The MCP server is the read-only ground truth.** I deliberately did *not* expose `jobs/run-now` or any mutating Databricks call through the MCP server. Read state from MCP; write state through code review + CI. Mutating production from a chat-driven loop is how you get 3 AM pages.

**6. Cost is a first-class concern.** The `cost-watchdog` sub-agent and the `prompt-eval` skill exist because the JD calls out cost governance (prompt caching, model routing, drift detection) — and because anyone running real pipelines on Databricks has had the "why was my bill $X this month" conversation. Surface cost before it surprises you.

---

## How the pieces compose on a real PR

A realistic flow for adding a new bronze ingest:

1. Engineer: *"I need to ingest the new `equipment_telemetry` feed into bronze."*
2. Claude reads `CLAUDE.md` (project conventions) and, because the task touches `bronze/`, auto-loads `.claude/rules/medallion.md`.
3. Description matches the `new-bronze-ingest` skill → Claude pulls its checklist.
4. While drafting the PySpark job, Claude calls the **databricks-mini MCP server** to confirm the target catalog/schema and list existing bronze jobs (avoids name collisions).
5. After each file write, the **post-edit hook** runs `ruff` + `pyright` + `pytest -k bronze` and feeds failures back to Claude.
6. When Claude tries to add a `dbutils.fs.rm` to a path under `prod/`, the **pre-tool hook** exits 2 and blocks it. Claude proposes a `dev/` path instead.
7. Engineer runs `/ship-checklist` — slash command kicks off the **pipeline-reviewer sub-agent** in fresh context with Read+Grep+Bash only. Review comes back; main context is untouched.
8. Separately, **cost-watchdog** sub-agent estimates the cluster-hours and flags that the planned job uses an oversized SKU for the volume.

Five primitives. One PR. Nothing magical — but Claude is finally operating like an engineer who's read the runbook.

---

## What I deliberately did *not* build

This is a hiring artifact, not a platform, so it should be honest about scope:

- **No write-side Databricks MCP.** Mutations go through CI, not chat. (See principle 5.)
- **No vector store / RAG.** The JD mentions RAG over maintenance and tariff data — that's a real product, not a `.claude/` config concern. A skill that *calls* a RAG service is one file; standing up the service itself doesn't belong here.
- **No agent for "write the whole pipeline."** Sub-agents in this kit are reviewers and runners. The main session is still where code gets written. End-to-end autonomous codegen is impressive in demos and unreliable in production data work.
- **No plugin packaging.** Plugins are how you distribute this kind of setup across many repos. For one repo, project-scoped config in `.claude/` is simpler and easier to review.

---

## Layout

```
.
├── README.md                      ← you are here
├── CLAUDE.md                      ← project memory (global rules, short)
├── .mcp.json                      ← MCP server registration
├── .claude/
│   ├── settings.json              ← permissions, hooks wiring
│   ├── rules/
│   │   ├── pyspark.md             ← PySpark idioms (path-scoped)
│   │   └── medallion.md           ← bronze/silver/gold conventions
│   ├── skills/
│   │   ├── new-bronze-ingest/SKILL.md
│   │   ├── promote-to-silver/SKILL.md
│   │   ├── dq-check/SKILL.md
│   │   └── prompt-eval/SKILL.md
│   ├── commands/
│   │   └── ship-checklist.md
│   ├── agents/
│   │   ├── pipeline-reviewer.md
│   │   ├── cost-watchdog.md
│   │   └── eval-runner.md
│   └── hooks/
│       ├── pre-tool-protect-prod.sh
│       ├── post-edit-pyspark-checks.sh
│       └── session-start-context.sh
├── mcp-servers/
│   └── databricks_mini/           ← read-only Databricks MCP server
│       ├── README.md
│       ├── pyproject.toml
│       └── server.py
└── examples/                      ← reference pipelines
    ├── bronze_ingest_example.py
    ├── silver_transform_example.py
    └── gold_kpi_example.py
```

---

## Running it locally

```bash
# 1. Install Claude Code (skip if you have it)
npm i -g @anthropic-ai/claude-code

# 2. Clone & enter
git clone <this-repo>
cd claude-code-data-eng-kit

# 3. Install the MCP server (optional, for the live Databricks bits)
cd mcp-servers/databricks_mini
pip install -e .
export DATABRICKS_HOST=...
export DATABRICKS_TOKEN=...
cd ../..

# 4. Make hook scripts executable
chmod +x .claude/hooks/*.sh

# 5. Open Claude Code in the repo
claude
```

The skills, rules, agents, and hooks load automatically. The MCP server requires env vars and runs only when you ask Claude something that triggers it.

---

## License

MIT.

## Notes for reviewers

If you're reading this as part of a hiring evaluation: every file in `.claude/` is intentionally short and intentionally opinionated. I'd rather defend three decisions than show ten files of boilerplate. Happy to walk through any of these in a technical round, including the trade-offs I rejected.
