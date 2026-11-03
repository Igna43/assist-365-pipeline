import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_DATASETS = {"raw", "core", "mart", "ops"}
DATASET_REF = re.compile(r"\$\{project\}\.([A-Za-z_][A-Za-z0-9_]*)\.")
BACKTICK_REF = re.compile(r"`([A-Za-z0-9_-]+)\.([A-Za-z_][A-Za-z0-9_]*)\.")


def _sql_files():
    yield from (ROOT / "sql").glob("*.sql")
    yield from (ROOT / "tests" / "data").glob("*.sql")


# El SQL del modelo y de los tests solo nombra datasets del proyecto: raw, core, mart y ops.
def test_model_sql_only_references_owned_datasets():
    offenders = []
    for path in _sql_files():
        text = path.read_text()
        for match in DATASET_REF.finditer(text):
            if match.group(1) not in ALLOWED_DATASETS:
                offenders.append(f"{path.name}: {match.group(0)}")
        for match in BACKTICK_REF.finditer(text):
            dataset = match.group(2)
            if dataset not in ALLOWED_DATASETS:
                offenders.append(f"{path.name}: {match.group(0)}")
    assert offenders == []


# Cada test de datos es un SELECT no vacío.
# Tiene WHERE o HAVING para devolver filas solo cuando la afirmación falla.
def test_data_tests_are_nonempty_failure_queries():
    paths = sorted((ROOT / "tests" / "data").glob("*.sql"))
    assert paths, "expected SQL data tests"
    for path in paths:
        text = path.read_text().strip()
        assert text, path.name
        lowered = text.lower()
        assert "having" in lowered or "where" in lowered, path.name
        assert "select" in lowered, path.name
