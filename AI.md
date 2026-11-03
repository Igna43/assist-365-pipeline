# Cómo usé IA en este ejercicio

Leí el caso y armé el proceso antes de pedirle a la IA que escribiera código. Cursor me sirvió para ordenar ese diseño en un plan y para redactar cada pieza contra reglas que ya había fijado. No le pedí un informe: le pedí que materializara decisiones y después revisé el resultado contra los datos.

## Qué decidí yo

La API no es una tabla. Son eventos de póliza con cursor, una foto de siniestros y catálogos chicos, con fechas mezcladas y monedas `NaN`. Por eso el flujo es ELT: extraer, dejar NDJSON comprimido en Cloud Storage y cargar con un load job. El streaming no deja un archivo para repetir la carga y cobra por fila. Un JSON único de un millón de pólizas no se puede ir escribiendo mientras llegan las páginas.

El modelo lo definí con grano explícito. `fct_venta` es la póliza vigente: gana el `updated_at` más nuevo y, en empate, `D` sobre `U` sobre `I`. `fct_siniestro` es un siniestro. El mart es una fila por mes de emisión, país y plan, y solo guarda columnas aditivas. Looker calcula los ratios con `SUM / SUM`. Si promediara porcentajes, un plan chico pesaría igual que uno grande.

El glosario no cierra tres definiciones, así que las cerré yo y las dejé escritas en el README y en `SKILL.md`:

- Prima emitida: pólizas cuyo estado vigente no es `ANULADA`. No hay devolución, así que la anulada sale del denominador.
- Costo: solo `status = PAGADO`.
- Atribución por cohorte de emisión, no por mes de ocurrencia. "Este trimestre" tiene que responder qué se vendió en el trimestre.
- Los siniestros de una anulada también quedan afuera. Si no, el costo entra y la prima no.

La segunda corrida no vuelve a bajar el millón de pólizas. El watermark es el máximo `updated_at` ya cargado, y el cliente tira las filas viejas que la página del salto todavía trae. Siniestros y catálogos se reemplazan enteros porque no hay feed de cambios. Los hechos se reconstruyen siempre desde el log, para que un `D` tardío corrija la póliza vigente.

El tablero lee solo `mart.siniestralidad_cohorte`. Un `SELECT *` procesa 217.152 bytes, muy por debajo de los 50 MB del ejercicio.

## Para qué usé la IA

Con esas reglas le pedí a Cursor que armara el plan en el orden en que se construye: cliente con reintentos, extracción, carga, SQL, tests que frenan la corrida, job diario, y los tres bonus (capa semántica, tests de datos, CI sin credenciales).

Después le pedí que redactara cada parte en ese orden, no que inventara el diseño. El extractor, el SQL, los tests y el servidor MCP salieron de ahí. Yo contrasté cada borrador con la regla correspondiente: paginación de pólizas contra el cursor real, siniestros contra offset múltiplo de 500, el mart contra `SUM / SUM`, y el CI contra "no hay token ni credencial de GCP en el workflow".

La IA también me sirvió para dejar el repo ordenado para una pregunta en vivo: `SKILL.md` con el glosario, el MCP de solo lectura, y la transcripción de las cinco preguntas en `analysis/preguntas.md`. Esas respuestas salieron de `run_select`, no de una consulta suelta al lado.

## Dónde corregí el borrador

Dos resultados del primer modelo estaban mal, y no los resolví apagando el test.

El test de costo negativo falló con 477 siniestros pagados. El monto de origen es negativo y el factor de cambio no lo es. Conservar el signo es lo correcto: tirar esas filas subiría el costo. El test ahora exige que el signo se mantenga.

215.219 pólizas emitidas quedaron sin dólares. No era solo que el calendario termina el 2026-10-30. Adentro del rango hay huecos: 5.124 filas son 732 fechas, no todos los días. El join por fecha exacta no alcanza. `dim_tipo_cambio` arma un día por moneda y arrastra la última tasa, y marca de dónde salió (`exact`, `carried_forward`, `extrapolated_forward`, `extrapolated_backward`, `missing`). Los números del informe son los de después de ese arreglo. Cuando la moneda viene `NaN`, no inventé una.

## Qué no delegué

El token de la API no está en el repo. Vive en `.env`, que el `.gitignore` excluye, y entra al Cloud Run Job en el deploy. Secret Manager no se pudo habilitar: esta cuenta no tiene `serviceusage.services.enable`.

Tampoco delegué el criterio de los números. Equipaje Protegido destruye margen (147,8%, pérdida de USD 659.948) y no es por frecuencia ni por severidad: ambas están apenas debajo del portafolio. El país casi no separa. La compra con 0 a 2 días de anticipación tiene siniestralidad 63,7% contra 33,7% del resto, con el doble de frecuencia y la misma severidad. Eso está en `analysis/resultados.md` y es lo que defendería en la entrevista.
