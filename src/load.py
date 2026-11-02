from __future__ import annotations

import gzip
import shutil
from pathlib import Path

from google.api_core.exceptions import NotFound
from google.cloud import bigquery, storage

from src.config import Settings
from src.extract import ExtractResult
from src.parsing import format_watermark
from src.schemas import (
    AGENCIAS_SCHEMA,
    POLIZAS_SCHEMA,
    PRODUCTOS_SCHEMA,
    SINIESTROS_SCHEMA,
    TIPO_CAMBIO_SCHEMA,
)

SCHEMAS = {
    "polizas": POLIZAS_SCHEMA,
    "siniestros": SINIESTROS_SCHEMA,
    "productos": PRODUCTOS_SCHEMA,
    "agencias": AGENCIAS_SCHEMA,
    "tipo_cambio": TIPO_CAMBIO_SCHEMA,
}

POLIZA_COLUMNS = [field.name for field in POLIZAS_SCHEMA]


def gzip_file(source: Path) -> Path:
    destination = source.with_suffix(source.suffix + ".gz")
    with source.open("rb") as raw, gzip.open(destination, "wb") as compressed:
        shutil.copyfileobj(raw, compressed)
    return destination


def upload_ndjson(settings: Settings, local_gz: Path, object_name: str) -> str:
    client = storage.Client(project=settings.project)
    bucket = client.bucket(settings.bucket)
    blob = bucket.blob(object_name)
    blob.upload_from_filename(str(local_gz), timeout=900)
    return f"gs://{settings.bucket}/{object_name}"


def load_ndjson(
    bq: bigquery.Client,
    uri: str,
    table_id: str,
    schema: list[bigquery.SchemaField],
    disposition: str,
    clustering: list[str] | None = None,
) -> int:
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=disposition,
        ignore_unknown_values=False,
    )
    if clustering:
        job_config.clustering_fields = clustering
    job = bq.load_table_from_uri(uri, table_id, job_config=job_config)
    job.result(timeout=1800)
    return int(job.output_rows or 0)


def table_exists(bq: bigquery.Client, table_id: str) -> bool:
    try:
        bq.get_table(table_id)
    except NotFound:
        return False
    return True


def merge_polizas(bq: bigquery.Client, settings: Settings) -> None:
    target = settings.table(settings.raw_dataset, "polizas")
    stage = settings.table(settings.raw_dataset, "polizas_stage")
    columns = ", ".join(POLIZA_COLUMNS)
    values = ", ".join(f"S.{name}" for name in POLIZA_COLUMNS)
    sql = f"""
    MERGE `{target}` T
    USING `{stage}` S
    ON T.poliza_id = S.poliza_id
      AND T.updated_at = S.updated_at
      AND IFNULL(T.op, '') = IFNULL(S.op, '')
    WHEN NOT MATCHED THEN
      INSERT ({columns})
      VALUES ({values})
    """
    bq.query(sql).result()
    bq.delete_table(stage, not_found_ok=True)


def update_watermark(bq: bigquery.Client, settings: Settings) -> str | None:
    target = settings.table(settings.ops_dataset, "watermarks")
    source = settings.table(settings.raw_dataset, "polizas")
    sql = f"""
    MERGE `{target}` T
    USING (
      SELECT 'polizas' AS resource, MAX(updated_at) AS watermark_ts
      FROM `{source}`
    ) S
    ON T.resource = S.resource
    WHEN MATCHED THEN
      UPDATE SET watermark_ts = S.watermark_ts, updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
      INSERT (resource, watermark_ts, updated_at)
      VALUES (S.resource, S.watermark_ts, CURRENT_TIMESTAMP())
    """
    bq.query(sql).result()
    rows = list(
        bq.query(
            f"SELECT watermark_ts FROM `{target}` WHERE resource = 'polizas'"
        ).result()
    )
    if not rows:
        return None
    return format_watermark(rows[0]["watermark_ts"])


def read_watermark(bq: bigquery.Client, settings: Settings) -> str | None:
    table = settings.table(settings.ops_dataset, "watermarks")
    if not table_exists(bq, table):
        return None
    rows = list(
        bq.query(f"SELECT watermark_ts FROM `{table}` WHERE resource = 'polizas'").result()
    )
    if not rows or rows[0]["watermark_ts"] is None:
        return None
    return format_watermark(rows[0]["watermark_ts"])


def record_extract(
    bq: bigquery.Client, settings: Settings, result: ExtractResult, batch_id: str
) -> None:
    table = settings.table(settings.ops_dataset, "extract_counts")
    api_total = "NULL" if result.api_total is None else str(int(result.api_total))
    sql = f"""
    INSERT INTO `{table}` (resource, batch_id, mode, api_total, loaded_rows, extracted_at)
    VALUES (
      '{result.resource}',
      '{batch_id}',
      '{result.mode}',
      {api_total},
      {int(result.rows)},
      CURRENT_TIMESTAMP()
    )
    """
    bq.query(sql).result()


def load_result(
    bq: bigquery.Client,
    settings: Settings,
    result: ExtractResult,
    batch_id: str,
) -> None:
    if result.rows == 0 and result.resource == "polizas" and result.mode == "incremental":
        print("polizas incremental: no new events", flush=True)
        record_extract(bq, settings, result, batch_id)
        return
    gz_path = gzip_file(result.path)
    object_name = f"raw/{result.resource}/{batch_id}/{gz_path.name}"
    uri = upload_ndjson(settings, gz_path, object_name)
    print(f"uploaded {uri}", flush=True)
    schema = SCHEMAS[result.resource]
    if result.resource == "polizas" and result.mode == "incremental":
        stage = settings.table(settings.raw_dataset, "polizas_stage")
        load_ndjson(
            bq,
            uri,
            stage,
            schema,
            bigquery.WriteDisposition.WRITE_TRUNCATE,
            clustering=["poliza_id"],
        )
        merge_polizas(bq, settings)
    else:
        table = settings.table(settings.raw_dataset, result.resource)
        clustering = ["poliza_id"] if result.resource == "polizas" else None
        if result.resource == "siniestros":
            clustering = ["claim_id"]
        load_ndjson(
            bq,
            uri,
            table,
            schema,
            bigquery.WriteDisposition.WRITE_TRUNCATE,
            clustering=clustering,
        )
    record_extract(bq, settings, result, batch_id)
    if result.resource == "polizas":
        watermark = update_watermark(bq, settings)
        print(f"polizas watermark {watermark}", flush=True)
