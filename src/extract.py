from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.client import ApiClient
from src.parsing import (
    clean_currency,
    decimal_string,
    is_after,
    parse_date,
    parse_timestamp,
)


@dataclass
class ExtractResult:
    resource: str
    path: Path
    rows: int
    api_total: int | None
    mode: str


def poliza_params(cursor: str | None, updated_since: str | None) -> dict[str, str]:
    """updated_since is only sent on the first page. Later pages follow the cursor."""
    if cursor:
        return {"cursor": cursor}
    if updated_since:
        return {"updated_since": updated_since}
    return {}


def next_cursor(pagination: dict[str, Any] | None) -> str | None:
    if not pagination:
        return None
    if pagination.get("has_more") and pagination.get("next_cursor"):
        return str(pagination["next_cursor"])
    return None


def filter_polizas_since(rows: list[dict[str, Any]], watermark: str | None) -> list[dict[str, Any]]:
    """The API skips to a page, and that page still contains rows at or before the watermark."""
    if not watermark:
        return rows
    return [row for row in rows if is_after(row.get("updated_at"), watermark)]


def header_total(headers: dict[str, str]) -> int | None:
    for key, value in headers.items():
        if key.lower() == "x-total-count" and value not in (None, ""):
            return int(value)
    return None


def _audit(batch_id: str, ingested_at: str) -> dict[str, str]:
    return {"_batch_id": batch_id, "_ingested_at": ingested_at}


def normalize_poliza(row: dict[str, Any], batch_id: str, ingested_at: str) -> dict[str, Any]:
    return {
        "poliza_id": row.get("poliza_id"),
        "cliente_id": row.get("cliente_id"),
        "producto_id": row.get("producto_id"),
        "agencia_id": row.get("agencia_id"),
        "pais_emision": row.get("pais_emision"),
        "canal_origen": row.get("canal_origen"),
        "fecha_emision_utc": parse_timestamp(row.get("fecha_emision_utc")),
        "inicio_vigencia": parse_date(row.get("inicio_vigencia")),
        "fin_vigencia": parse_date(row.get("fin_vigencia")),
        "prima": decimal_string(row.get("prima")),
        "moneda": clean_currency(row.get("moneda")),
        "estado": row.get("estado"),
        "op": row.get("op"),
        "updated_at": parse_timestamp(row.get("updated_at")),
        **_audit(batch_id, ingested_at),
    }


def normalize_siniestro(row: dict[str, Any], batch_id: str, ingested_at: str) -> dict[str, Any]:
    amount = row.get("amount") if isinstance(row.get("amount"), dict) else {}
    detail = row.get("detail")
    detail_text = json.dumps(detail, ensure_ascii=False) if detail is not None else None
    return {
        "claim_id": row.get("claim_id"),
        "policy_id": row.get("policy_id"),
        "occurred_at_raw": None if row.get("occurred_at") is None else str(row.get("occurred_at")),
        "reported_at_raw": None if row.get("reported_at") is None else str(row.get("reported_at")),
        "occurred_on": parse_date(row.get("occurred_at")),
        "reported_on": parse_date(row.get("reported_at")),
        "type": row.get("type"),
        "status": row.get("status"),
        "amount_value": decimal_string(amount.get("value")),
        "amount_currency": clean_currency(amount.get("currency")),
        "detail": detail_text,
        **_audit(batch_id, ingested_at),
    }


def normalize_producto(row: dict[str, Any], batch_id: str, ingested_at: str) -> dict[str, Any]:
    return {
        "producto_id": row.get("producto_id"),
        "nombre_plan": row.get("nombre_plan"),
        "cobertura_max_usd": decimal_string(row.get("cobertura_max_usd")),
        "tipo": row.get("tipo"),
        "es_premium": None if row.get("es_premium") is None else str(row.get("es_premium")),
        **_audit(batch_id, ingested_at),
    }


def normalize_agencia(row: dict[str, Any], batch_id: str, ingested_at: str) -> dict[str, Any]:
    return {
        "agencia_id": row.get("agencia_id"),
        "nombre": row.get("nombre"),
        "pais": row.get("pais"),
        "canal": row.get("canal"),
        **_audit(batch_id, ingested_at),
    }


def normalize_tipo_cambio(row: dict[str, Any], batch_id: str, ingested_at: str) -> dict[str, Any]:
    return {
        "fecha": parse_date(row.get("fecha")),
        "moneda": clean_currency(row.get("moneda")),
        "unidades_por_usd": decimal_string(row.get("unidades_por_usd")),
        "factor_usd": decimal_string(row.get("factor_usd")),
        **_audit(batch_id, ingested_at),
    }


def write_ndjson(path: Path, records: Iterator[dict[str, Any]] | list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False))
            handle.write("\n")
            count += 1
    return count


def extract_catalog(
    client: ApiClient,
    tipo: str,
    normalizer,
    path: Path,
    batch_id: str,
    ingested_at: str,
) -> ExtractResult:
    payload, headers = client.get_json("/catalogos", {"tipo": tipo})
    rows = payload.get("data") or []
    count = write_ndjson(path, (normalizer(row, batch_id, ingested_at) for row in rows))
    meta_total = (payload.get("meta") or {}).get("total")
    api_total = int(meta_total) if meta_total is not None else header_total(headers)
    print(f"catalogo {tipo}: {count} filas", flush=True)
    return ExtractResult(tipo, path, count, api_total, "full")


def extract_polizas(
    client: ApiClient,
    path: Path,
    batch_id: str,
    ingested_at: str,
    watermark: str | None,
) -> ExtractResult:
    """Cursor pagination. A watermark keeps only events strictly after it."""
    mode = "incremental" if watermark else "full"
    cursor: str | None = None
    pages = 0
    written = 0
    api_total: int | None = None
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        while True:
            payload, headers = client.get_json("/polizas", poliza_params(cursor, watermark))
            api_total = header_total(headers) or api_total
            rows = filter_polizas_since(payload.get("data") or [], watermark)
            for row in rows:
                record = normalize_poliza(row, batch_id, ingested_at)
                handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False))
                handle.write("\n")
                written += 1
            pages += 1
            if pages == 1 or pages % 25 == 0:
                print(
                    f"polizas page {pages} kept {written} retries {client.retries}",
                    flush=True,
                )
            cursor = next_cursor(payload.get("pagination"))
            if not cursor:
                break
    print(
        f"polizas done pages={pages} rows={written} mode={mode} api_total={api_total}",
        flush=True,
    )
    return ExtractResult("polizas", path, written, api_total, mode)


def extract_siniestros(
    client: ApiClient,
    path: Path,
    batch_id: str,
    ingested_at: str,
) -> ExtractResult:
    """Offset pagination. The page size is fixed at 500 and the offset must be a multiple of 500."""
    offset = 0
    pages = 0
    written = 0
    api_total: int | None = None
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        while True:
            payload, headers = client.get_json("/siniestros", {"offset": offset})
            meta = payload.get("meta") or {}
            if meta.get("total") is not None:
                api_total = int(meta["total"])
            api_total = header_total(headers) or api_total
            rows = payload.get("data") or []
            if not rows:
                break
            for row in rows:
                record = normalize_siniestro(row, batch_id, ingested_at)
                handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False))
                handle.write("\n")
                written += 1
            pages += 1
            if pages == 1 or pages % 25 == 0:
                print(
                    f"siniestros offset {offset} kept {written} retries {client.retries}",
                    flush=True,
                )
            offset += 500
            if api_total is not None and offset >= api_total:
                break
    print(f"siniestros done pages={pages} rows={written} api_total={api_total}", flush=True)
    return ExtractResult("siniestros", path, written, api_total, "full")
