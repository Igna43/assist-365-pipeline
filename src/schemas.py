from __future__ import annotations

from google.cloud import bigquery


def field(name: str, type_: str, mode: str = "NULLABLE") -> bigquery.SchemaField:
    return bigquery.SchemaField(name, type_, mode=mode)


def audit_fields() -> list[bigquery.SchemaField]:
    return [
        field("_batch_id", "STRING"),
        field("_ingested_at", "TIMESTAMP"),
    ]


POLIZAS_SCHEMA = [
    field("poliza_id", "STRING", "REQUIRED"),
    field("cliente_id", "STRING"),
    field("producto_id", "STRING"),
    field("agencia_id", "STRING"),
    field("pais_emision", "STRING"),
    field("canal_origen", "STRING"),
    field("fecha_emision_utc", "TIMESTAMP"),
    field("inicio_vigencia", "DATE"),
    field("fin_vigencia", "DATE"),
    field("prima", "NUMERIC"),
    field("moneda", "STRING"),
    field("estado", "STRING"),
    field("op", "STRING"),
    field("updated_at", "TIMESTAMP"),
    *audit_fields(),
]

SINIESTROS_SCHEMA = [
    field("claim_id", "STRING", "REQUIRED"),
    field("policy_id", "STRING"),
    field("occurred_at_raw", "STRING"),
    field("reported_at_raw", "STRING"),
    field("occurred_on", "DATE"),
    field("reported_on", "DATE"),
    field("type", "STRING"),
    field("status", "STRING"),
    field("amount_value", "NUMERIC"),
    field("amount_currency", "STRING"),
    field("detail", "STRING"),
    *audit_fields(),
]

PRODUCTOS_SCHEMA = [
    field("producto_id", "STRING", "REQUIRED"),
    field("nombre_plan", "STRING"),
    field("cobertura_max_usd", "NUMERIC"),
    field("tipo", "STRING"),
    field("es_premium", "STRING"),
    *audit_fields(),
]

AGENCIAS_SCHEMA = [
    field("agencia_id", "STRING", "REQUIRED"),
    field("nombre", "STRING"),
    field("pais", "STRING"),
    field("canal", "STRING"),
    *audit_fields(),
]

TIPO_CAMBIO_SCHEMA = [
    field("fecha", "DATE", "REQUIRED"),
    field("moneda", "STRING", "REQUIRED"),
    field("unidades_por_usd", "NUMERIC"),
    field("factor_usd", "NUMERIC"),
    *audit_fields(),
]
