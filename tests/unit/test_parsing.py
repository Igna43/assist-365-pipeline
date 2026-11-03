from datetime import datetime

from src.parsing import (
    clean_currency,
    decimal_string,
    is_after,
    parse_date,
    parse_timestamp,
)


# Una fecha ISO de calendario se conserva tal cual.
def test_iso_date():
    assert parse_date("2024-11-22") == "2024-11-22"


# Un timestamp ISO se recorta al día calendario, sin correr el día por la hora.
def test_iso_timestamp_keeps_the_calendar_day():
    assert parse_date("2024-03-11T00:00:00Z") == "2024-03-11"


# Las fechas con barra vienen día/mes/año. El 05/07 es el 5 de julio, no el 7 de mayo.
def test_slash_dates_are_day_first():
    assert parse_date("05/07/2024") == "2024-07-05"
    assert parse_date("19/11/2024") == "2024-11-19"


# Una fecha imposible, nula o el texto "nan" se descarta en vez de inventar un día.
def test_impossible_dates_are_dropped():
    assert parse_date("32/01/2024") is None
    assert parse_date("2024-02-31") is None
    assert parse_date(None) is None
    assert parse_date("nan") is None


# Un timestamp válido se conserva. Uno que no se puede leer queda nulo.
def test_timestamp_round_trip():
    assert parse_timestamp("2024-01-01T00:04:00Z") == "2024-01-01T00:04:00Z"
    assert parse_timestamp("not-a-timestamp") is None


# El watermark es estricto: la misma marca, o una nula, no cuenta como posterior.
def test_watermark_comparison_is_strict():
    assert is_after("2024-01-02T00:00:00Z", "2024-01-01T00:00:00Z")
    assert not is_after("2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z")
    assert not is_after(None, "2024-01-01T00:00:00Z")


# NaN en el monto o en la moneda se vuelve nulo. Una moneda válida queda en mayúsculas.
def test_decimal_and_currency_reject_nan():
    assert decimal_string("157993.91") == "157993.91"
    assert decimal_string(float("nan")) is None
    assert decimal_string("NaN") is None
    assert clean_currency(float("nan")) is None
    assert clean_currency("cop") == "COP"
    assert clean_currency(None) is None


# El watermark se serializa en UTC con sufijo Z, que es lo que la API espera en updated_since.
def test_datetime_watermark_formats_with_z():
    from src.parsing import format_watermark

    value = datetime.fromisoformat("2026-10-01T00:00:00+00:00")
    assert format_watermark(value) == "2026-10-01T00:00:00Z"
