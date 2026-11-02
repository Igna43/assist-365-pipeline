# Cómo usé IA en este ejercicio

Usé Cursor, con el agente en el repo, para construir el pipeline a partir del PDF del caso. No para que escribiera el informe sin mirar los datos.

Qué le pedí, en este orden:

1. Leer el PDF y el token, y armar un plan: extracción con reintentos, carga a BigQuery, modelo con grano declarado, job diario, tablero bajo 50 MB, y los tres bonus (SKILL.md con preguntas vía MCP, tests de datos, GitHub Actions).
2. Implementar ese plan. El agente escribió el extractor, el SQL, los tests y el servidor MCP. Yo revisé las definiciones que el glosario deja abiertas (anuladas fuera de la prima, solo `PAGADO`, cohorte de emisión, ratios con `SUM / SUM`).
3. Cuando el test de costo negativo falló con 477 filas, no se apagó el test: se comprobó que el monto de origen es negativo y que el factor de cambio no lo es. El test ahora exige que el signo se conserve.
4. Cuando 215.219 pólizas quedaron sin dólares, se miró el calendario: hay huecos adentro del rango, no solo fechas posteriores al 2026-10-30. El modelo arrastra la última tasa. Los números del informe son los de después de ese arreglo.
5. Las cinco preguntas de `analysis/preguntas.md` se resolvieron con el MCP del repo (`run_select`), siguiendo `SKILL.md`.

Contexto que quedó en el repo para repetirlo: `SKILL.md`, `.cursor/mcp.json`, `mcp_bigquery/server.py` y este archivo.

No commiteé el token. Está en `.env`, que el `.gitignore` excluye.
