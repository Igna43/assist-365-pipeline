import pytest
from mcp_bigquery.server import validate_select


# Un SELECT solo pasa el guardia de solo lectura del MCP.
def test_select_is_accepted():
    sql = validate_select("SELECT 1")
    assert sql == "SELECT 1"


# Un WITH también es una lectura.
# El punto y coma final se saca para que BigQuery reciba una sola sentencia.
def test_with_is_accepted_and_trailing_semicolon_is_stripped():
    sql = validate_select("WITH x AS (SELECT 1 AS n) SELECT n FROM x;")
    assert sql.endswith("x")
    assert ";" not in sql


# Un DELETE no puede correr por el MCP: escribiría en el warehouse.
def test_dml_is_rejected():
    with pytest.raises(ValueError):
        validate_select("DELETE FROM `a365-de-imangini.mart.siniestralidad_cohorte` WHERE TRUE")


# Dos sentencias en una sola llamada se rechazan, aunque la primera sea un SELECT.
def test_two_statements_are_rejected():
    with pytest.raises(ValueError):
        validate_select("SELECT 1; SELECT 2")


# Una consulta vacía o de solo espacios se rechaza.
def test_empty_is_rejected():
    with pytest.raises(ValueError):
        validate_select("   ")
