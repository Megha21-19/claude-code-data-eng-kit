# databricks-mini

A minimal, **read-only** MCP server that lets Claude Code see what's actually
in your Databricks workspace: jobs, recent runs, and Unity Catalog state.

## Why read-only

The principle is simple: Claude can read state, propose code, and have a human
+ CI execute the change. Letting an agent trigger `jobs/run-now` against
production has a bad failure mode and a great one — and we don't ship code
that depends on which one fires.

## Tools

| Tool | Purpose |
|---|---|
| `list_jobs(name_filter)` | Discover what's deployed before naming a new job. |
| `get_recent_runs(job_id, limit)` | "Did the upstream job succeed?" before downstream work. |
| `list_catalogs()` | UC discovery. |
| `list_schemas(catalog)` | UC discovery. |
| `list_tables(catalog, schema)` | Avoid collisions when proposing new tables. |

## Setup

```bash
cd mcp-servers/databricks_mini
pip install -e .

export DATABRICKS_HOST=https://<workspace>.cloud.databricks.com
export DATABRICKS_TOKEN=dapi...

# Claude Code picks it up via the project's .mcp.json
```

## Status

The wire format is real (MCP via stdio, FastMCP SDK). The Databricks REST calls
are stubbed — see `# TODO` comments in `server.py`. Wiring them up is one HTTP
client and one auth header.
