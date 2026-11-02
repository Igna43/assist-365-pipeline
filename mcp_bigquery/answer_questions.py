"""Answer the five business questions by calling the warehouse MCP server.

The SQL follows .cursor/skills/assist365/SKILL.md. Results are not queried with
the bq CLI; they go through the MCP tool run_select.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "mcp_bigquery" / "server.py"
OUT = ROOT / "analysis" / "preguntas.md"

QUESTIONS = [
    {
        "pregunta": "¿Cuál es la siniestralidad por plan, en dólares?",
        "sql": """
            SELECT
              nombre_plan,
              producto_id,
              SUM(polizas_emitidas) AS polizas,
              SUM(prima_emitida_usd) AS prima_usd,
              SUM(costo_siniestros_usd) AS costo_usd,
              SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
            FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            GROUP BY nombre_plan, producto_id
            ORDER BY siniestralidad DESC
        """,
    },
    {
        "pregunta": "¿Cuál es la siniestralidad por país, en dólares?",
        "sql": """
            SELECT
              pais_emision,
              SUM(polizas_emitidas) AS polizas,
              SUM(prima_emitida_usd) AS prima_usd,
              SUM(costo_siniestros_usd) AS costo_usd,
              SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
            FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            GROUP BY pais_emision
            ORDER BY siniestralidad DESC
        """,
    },
    {
        "pregunta": "¿Qué país está peor en el último trimestre con datos?",
        "sql": """
            WITH bounds AS (
              SELECT DATE_TRUNC(MAX(mes_emision), QUARTER) AS trimestre
              FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            )
            SELECT
              b.trimestre,
              m.pais_emision,
              SUM(m.polizas_emitidas) AS polizas,
              SUM(m.prima_emitida_usd) AS prima_usd,
              SUM(m.costo_siniestros_usd) AS costo_usd,
              SAFE_DIVIDE(SUM(m.costo_siniestros_usd), SUM(m.prima_emitida_usd)) AS siniestralidad
            FROM `a365-de-imangini.mart.siniestralidad_cohorte` AS m
            CROSS JOIN bounds AS b
            WHERE m.mes_emision >= b.trimestre
              AND m.mes_emision < DATE_ADD(b.trimestre, INTERVAL 3 MONTH)
            GROUP BY b.trimestre, m.pais_emision
            ORDER BY siniestralidad DESC
        """,
    },
    {
        "pregunta": (
            "¿Qué plan destruye margen, mirando la pérdida en dólares y la siniestralidad?"
        ),
        "sql": """
            SELECT
              nombre_plan,
              producto_id,
              SUM(prima_emitida_usd) AS prima_usd,
              SUM(costo_siniestros_usd) AS costo_usd,
              SUM(costo_siniestros_usd) - SUM(prima_emitida_usd) AS perdida_usd,
              SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
            FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            GROUP BY nombre_plan, producto_id
            ORDER BY perdida_usd DESC
        """,
    },
    {
        "pregunta": (
            "En el plan que más margen destruye, ¿el problema es la frecuencia "
            "de siniestros o el monto promedio?"
        ),
        "sql": """
            WITH by_plan AS (
              SELECT
                nombre_plan,
                SAFE_DIVIDE(SUM(siniestros_pagados), SUM(polizas_emitidas)) AS frecuencia,
                SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(siniestros_pagados)) AS severidad_usd,
                SUM(costo_siniestros_usd) - SUM(prima_emitida_usd) AS perdida_usd
              FROM `a365-de-imangini.mart.siniestralidad_cohorte`
              GROUP BY nombre_plan
            ),
            portafolio AS (
              SELECT
                SAFE_DIVIDE(SUM(siniestros_pagados), SUM(polizas_emitidas)) AS frecuencia,
                SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(siniestros_pagados)) AS severidad_usd
              FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            )
            SELECT
              b.nombre_plan,
              b.frecuencia,
              p.frecuencia AS frecuencia_portafolio,
              SAFE_DIVIDE(b.frecuencia, p.frecuencia) AS frecuencia_vs_portafolio,
              b.severidad_usd,
              p.severidad_usd AS severidad_portafolio,
              SAFE_DIVIDE(b.severidad_usd, p.severidad_usd) AS severidad_vs_portafolio
            FROM by_plan AS b
            CROSS JOIN portafolio AS p
            WHERE b.nombre_plan = (
              SELECT nombre_plan FROM by_plan ORDER BY perdida_usd DESC LIMIT 1
            )
        """,
    },
]


def _text(result) -> str:
    chunks = []
    for block in result.content:
        text = getattr(block, "text", None)
        chunks.append(text if text is not None else str(block))
    return "\n".join(chunks)


async def _ask() -> str:
    import sys

    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], cwd=str(ROOT))
    sections = [
        "# Preguntas de negocio",
        "",
        "Resueltas contra `a365-de-imangini` llamando al MCP `assist365-bigquery` "
        "(`list_tables`, `describe_table`, `run_select`). Las definiciones están en `SKILL.md`.",
        "",
    ]
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tables = await session.call_tool("list_tables", {})
            described = await session.call_tool(
                "describe_table", {"dataset": "mart", "table": "siniestralidad_cohorte"}
            )
            sections.append("## Herramientas")
            sections.append("")
            sections.append("`list_tables`")
            sections.append("")
            sections.append("```json")
            sections.append(_text(tables).strip())
            sections.append("```")
            sections.append("")
            sections.append("`describe_table` mart.siniestralidad_cohorte")
            sections.append("")
            sections.append("```json")
            sections.append(_text(described).strip())
            sections.append("```")
            for item in QUESTIONS:
                result = await session.call_tool("run_select", {"sql": item["sql"].strip()})
                body = _text(result).strip()
                sections.extend(
                    [
                        "",
                        f"## {item['pregunta']}",
                        "",
                        "Herramienta: `run_select`",
                        "",
                        "```sql",
                        item["sql"].strip(),
                        "```",
                        "",
                        "```json",
                        body,
                        "```",
                    ]
                )
                parsed = json.loads(body)
                print(item["pregunta"], "bytes", parsed.get("total_bytes_processed"), flush=True)
    return "\n".join(sections) + "\n"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(asyncio.run(_ask()))
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
