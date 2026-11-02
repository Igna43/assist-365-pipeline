-- Fails when a claim is stored more than once.
SELECT claim_id, COUNT(*) AS n
FROM `${project}.core.fct_siniestro`
GROUP BY claim_id
HAVING COUNT(*) > 1
