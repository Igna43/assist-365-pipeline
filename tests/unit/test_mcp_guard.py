import pytest
from mcp_bigquery.server import validate_select


def test_select_is_accepted():
    sql = validate_select("SELECT 1")
    assert sql == "SELECT 1"


def test_with_is_accepted_and_trailing_semicolon_is_stripped():
    sql = validate_select("WITH x AS (SELECT 1 AS n) SELECT n FROM x;")
    assert sql.endswith("x")
    assert ";" not in sql


def test_dml_is_rejected():
    with pytest.raises(ValueError):
        validate_select("DELETE FROM `a365-de-imangini.mart.siniestralidad_cohorte` WHERE TRUE")


def test_two_statements_are_rejected():
    with pytest.raises(ValueError):
        validate_select("SELECT 1; SELECT 2")


def test_empty_is_rejected():
    with pytest.raises(ValueError):
        validate_select("   ")
