from __future__ import annotations

from google.cloud import bigquery

from src.config import ROOT, Settings


def run_data_tests(bq: bigquery.Client, settings: Settings) -> None:
    """Each SQL file returns rows only when the assertion fails."""
    tests_dir = ROOT / "tests" / "data"
    failures: list[str] = []
    paths = sorted(tests_dir.glob("*.sql"))
    for path in paths:
        sql = path.read_text().replace("${project}", settings.project)
        rows = list(bq.query(sql).result())
        if rows:
            preview = [dict(row) for row in rows[:5]]
            failures.append(f"{path.name}: {len(rows)} filas, ejemplo {preview}")
            print(f"FAIL {path.name} ({len(rows)})", flush=True)
        else:
            print(f"ok   {path.name}", flush=True)
    if failures:
        detail = "\n".join(failures)
        raise RuntimeError(f"Data tests failed:\n{detail}")
    print(f"{len(paths)} data tests passed", flush=True)
