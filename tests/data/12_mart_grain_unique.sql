-- Fails when the dashboard mart repeats a grain key.
SELECT mes_emision, pais_emision, producto_id, COUNT(*) AS n
FROM `${project}.mart.siniestralidad_cohorte`
GROUP BY mes_emision, pais_emision, producto_id
HAVING COUNT(*) > 1
