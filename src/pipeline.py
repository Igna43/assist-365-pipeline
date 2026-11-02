from __future__ import annotations

import argparse
from datetime import datetime, timezone

from google.cloud import bigquery

from src.client import ApiClient
from src.config import ROOT, Settings
from src.data_tests import run_data_tests
from src.extract import (
    extract_catalog,
    extract_polizas,
    extract_siniestros,
    normalize_agencia,
    normalize_producto,
    normalize_tipo_cambio,
)
from src.load import load_result, read_watermark
from src.parsing import utc_now_iso
from src.transform import run_sql_file, transform


def _batch_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _log_run(
    bq: bigquery.Client, settings: Settings, batch_id: str, status: str, detail: str
) -> None:
    table = settings.table(settings.ops_dataset, "pipeline_runs")
    safe_detail = detail.replace("'", " ")[:500]
    bq.query(
        f"""
        INSERT INTO `{table}` (batch_id, started_at, finished_at, status, detail)
        VALUES ('{batch_id}', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), '{status}', '{safe_detail}')
        """
    ).result()


def run(full: bool = False, skip_extract: bool = False, only: str = "all") -> None:
    require_token = only == "all" and not skip_extract
    settings = Settings.from_env(require_token=require_token)
    bq = bigquery.Client(project=settings.project, location=settings.location)
    run_sql_file(bq, settings, "sql/00_ops.sql")
    batch_id = _batch_id()

    if only == "test":
        run_data_tests(bq, settings)
        return
    if only == "transform" or skip_extract:
        transform(bq, settings)
        run_data_tests(bq, settings)
        _log_run(bq, settings, batch_id, "ok", "transform only")
        return

    ingested_at = utc_now_iso()
    batch_dir = ROOT / "data" / batch_id
    client = ApiClient(settings.api_base, settings.api_token, max_attempts=8)
    watermark = None if full else read_watermark(bq, settings)
    print(f"batch {batch_id} polizas watermark {watermark}", flush=True)

    results = [
        extract_catalog(
            client,
            "productos",
            normalize_producto,
            batch_dir / "productos.ndjson",
            batch_id,
            ingested_at,
        ),
        extract_catalog(
            client,
            "agencias",
            normalize_agencia,
            batch_dir / "agencias.ndjson",
            batch_id,
            ingested_at,
        ),
        extract_catalog(
            client,
            "tipo_cambio",
            normalize_tipo_cambio,
            batch_dir / "tipo_cambio.ndjson",
            batch_id,
            ingested_at,
        ),
        extract_siniestros(client, batch_dir / "siniestros.ndjson", batch_id, ingested_at),
        extract_polizas(
            client,
            batch_dir / "polizas.ndjson",
            batch_id,
            ingested_at,
            watermark,
        ),
    ]
    print(f"extract retries {client.retries}", flush=True)
    for result in results:
        print(f"load {result.resource} rows={result.rows} mode={result.mode}", flush=True)
        load_result(bq, settings, result, batch_id)
    transform(bq, settings)
    run_data_tests(bq, settings)
    _log_run(bq, settings, batch_id, "ok", f"retries={client.retries}")
    print("pipeline ok", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Assist-365 API to BigQuery pipeline")
    parser.add_argument("--full", action="store_true", help="Reload every policy event")
    parser.add_argument("--skip-extract", action="store_true", help="Rebuild the model only")
    parser.add_argument("--only", choices=["all", "transform", "test"], default="all")
    args = parser.parse_args()
    run(full=args.full, skip_extract=args.skip_extract, only=args.only)


if __name__ == "__main__":
    main()
