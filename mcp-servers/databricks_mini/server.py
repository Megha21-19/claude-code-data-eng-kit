"""databricks_mini: a minimal, read-only MCP server for Databricks.

Why this exists
---------------
Out of the box, Claude has no idea what jobs exist in your Databricks
workspace, what their run history looks like, or what schemas are in your
catalog. It will cheerfully invent plausible-looking names. This MCP server
gives it real ground truth — and *only* read access. Mutations stay in CI.

Tools exposed
-------------
- list_jobs(name_filter)            -> [{job_id, name, schedule}]
- get_recent_runs(job_id, limit)    -> [{run_id, state, start_time, duration_ms}]
- list_catalogs()                   -> [str]
- list_schemas(catalog)             -> [str]
- list_tables(catalog, schema)      -> [str]

Deliberately not exposed: jobs/run-now, workspace/delete, anything that mutates.
If you want to run a job, open a PR; CI runs it. The chat-driven loop should
not be able to trigger production work.

Run
---
    DATABRICKS_HOST=... DATABRICKS_TOKEN=... python -m databricks_mini.server

This is a stub. Real implementation calls the Databricks REST API
(/api/2.1/jobs/list, /api/2.1/jobs/runs/list, /api/2.1/unity-catalog/*).
"""

from __future__ import annotations

import os
import sys
from typing import Any

# This stub uses the official MCP Python SDK. Install with: pip install mcp
# https://github.com/modelcontextprotocol/python-sdk
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.stderr.write(
        "databricks_mini: install the MCP SDK first: pip install mcp\n"
    )
    raise


mcp = FastMCP("databricks-mini")


def _require_env() -> tuple[str, str]:
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError(
            "DATABRICKS_HOST and DATABRICKS_TOKEN must be set. "
            "This server is read-only but it still needs auth."
        )
    return host, token


@mcp.tool()
def list_jobs(name_filter: str = "") -> list[dict[str, Any]]:
    """List jobs in the workspace, optionally filtered by name substring.

    Returns a list of {job_id, name, schedule}. Use this to discover what's
    actually deployed before authoring a new job.
    """
    _require_env()
    # TODO: GET {host}/api/2.1/jobs/list, filter, return.
    return [
        {"job_id": 0, "name": "STUB: implement via Databricks REST API", "schedule": "n/a"}
    ]


@mcp.tool()
def get_recent_runs(job_id: int, limit: int = 5) -> list[dict[str, Any]]:
    """Recent runs for a job. Useful for checking 'did upstream succeed?'
    before kicking off downstream work.
    """
    _require_env()
    # TODO: GET {host}/api/2.1/jobs/runs/list?job_id=...&limit=...
    return [{"run_id": 0, "state": "STUB", "start_time": 0, "duration_ms": 0}]


@mcp.tool()
def list_catalogs() -> list[str]:
    """List Unity Catalog catalogs visible to the calling token."""
    _require_env()
    # TODO: GET {host}/api/2.1/unity-catalog/catalogs
    return ["bronze", "silver", "gold"]


@mcp.tool()
def list_schemas(catalog: str) -> list[str]:
    """List schemas in a catalog."""
    _require_env()
    # TODO: GET {host}/api/2.1/unity-catalog/schemas?catalog_name={catalog}
    return ["maintenance", "operations", "assets"]


@mcp.tool()
def list_tables(catalog: str, schema: str) -> list[str]:
    """List tables in a schema. Use this to avoid naming collisions when
    proposing a new bronze table."""
    _require_env()
    # TODO: GET {host}/api/2.1/unity-catalog/tables?catalog_name={catalog}&schema_name={schema}
    return ["equipment", "workorders"]


if __name__ == "__main__":
    mcp.run()
