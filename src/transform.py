from __future__ import annotations

from pathlib import Path

from google.cloud import bigquery

from src.config import ROOT, Settings

SQL_FILES = (
    "sql/01_dimensions.sql",
    "sql/02_facts.sql",
    "sql/03_mart.sql",
)


def run_sql(bq: bigquery.Client, settings: Settings, sql: str) -> None:
    job = bq.query(sql)
    job.result()


def run_sql_file(bq: bigquery.Client, settings: Settings, relative_path: str) -> None:
    path = ROOT / relative_path
    sql = path.read_text().replace("${project}", settings.project)
    print(f"sql {relative_path}", flush=True)
    run_sql(bq, settings, sql)


def transform(bq: bigquery.Client, settings: Settings) -> None:
    for relative in SQL_FILES:
        run_sql_file(bq, settings, relative)


def sql_roots() -> list[Path]:
    return [ROOT / "sql", ROOT / "tests" / "data"]
