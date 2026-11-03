-- Falla si un siniestro quedó guardado más de una vez.
SELECT claim_id, COUNT(*) AS n
FROM `${project}.core.fct_siniestro`
GROUP BY claim_id
HAVING COUNT(*) > 1
