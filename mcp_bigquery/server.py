from __future__ import annotations

import json
import re

from google.cloud import bigquery
from mcp.server.fastmcp import FastMCP

PROJECT = "a365-de-imangini"
LOCATION = "US"
MAX_BYTES = 1_000_000_000
DATASETS = ("raw", "core", "mart", "ops")
FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|CALL|EXPORT|LOAD)\b",
    re.IGNORECASE,
)

mcp = FastMCP("assist365-bigquery")


def validate_select(sql: str) -> str:
    """Accept one read-only SELECT or WITH statement."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        raise ValueError("SQL is empty")
    if ";" in stripped:
        raise ValueError("Only a single SELECT is allowed")
    if not re.match(r"(?is)^(SELECT|WITH)\b", stripped):
        raise ValueError("Only SELECT statements are allowed")
    if FORBIDDEN.search(stripped):
        raise ValueError("Statement is not read-only")
    return stripped


def _client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT, location=LOCATION)


@mcp.tool()
def list_tables() -> str:
    """List tables in the Assist-365 datasets raw, core, mart, and ops."""
    client = _client()
    found: dict[str, list[str]] = {}
    for dataset in DATASETS:
        tables = client.list_tables(f"{PROJECT}.{dataset}")
        found[dataset] = sorted(table.table_id for table in tables)
    return json.dumps(found, ensure_ascii=False, indent=2)


@mcp.tool()
def describe_table(dataset: str, table: str) -> str:
    """Describe one table. dataset is raw, core, mart, or ops."""
    if dataset not in DATASETS:
        raise ValueError(f"dataset must be one of {DATASETS}")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError("invalid table name")
    client = _client()
    full = client.get_table(f"{PROJECT}.{dataset}.{table}")
    columns = [
        {"name": field.name, "type": field.field_type, "mode": field.mode} for field in full.schema
    ]
    payload = {
        "table": f"{dataset}.{table}",
        "num_rows": full.num_rows,
        "num_bytes": full.num_bytes,
        "columns": columns,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def run_select(sql: str) -> str:
    """Run one read-only SELECT. Bytes billed are capped at 1 GB."""
    statement = validate_select(sql)
    client = _client()
    job_config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES)
    job = client.query(statement, job_config=job_config)
    rows = list(job.result(max_results=200))
    records = [dict(row) for row in rows]
    payload = {
        "job_id": job.job_id,
        "total_bytes_processed": job.total_bytes_processed,
        "row_count_returned": len(records),
        "rows": records,
    }
    return json.dumps(payload, ensure_ascii=False, default=str, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
