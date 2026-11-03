import json

from src.client import ApiClient, ApiError
from src.extract import filter_polizas_since, next_cursor, poliza_params
from src.parsing import loads_payload


class FakeResponse:
    def __init__(self, status, payload, headers=None):
        self.status_code = status
        self.text = json.dumps(payload) if not isinstance(payload, str) else payload
        self.headers = headers or {}


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        return self.responses.pop(0)


# Un 500 transitorio se reintenta una vez y la respuesta 200 se devuelve con sus headers.
def test_retries_transient_500_then_returns_json():
    sleeps = []
    session = FakeSession(
        [
            FakeResponse(500, {"error": "transient"}),
            FakeResponse(200, {"data": [1]}, {"x-total-count": "10"}),
        ]
    )
    client = ApiClient("https://example.test/v1", "token", session=session, sleep=sleeps.append)
    payload, headers = client.get_json("/polizas", {"cursor": "abc"})
    assert payload == {"data": [1]}
    assert headers["x-total-count"] == "10"
    assert client.retries == 1
    assert len(sleeps) == 1
    assert session.calls[0][1] == {"cursor": "abc"}


# Un 401 no se reintenta: el token está mal y esperar no lo arregla.
def test_401_does_not_retry():
    sleeps = []
    session = FakeSession([FakeResponse(401, {"error": "unauthorized"})])
    client = ApiClient("https://example.test/v1", "token", session=session, sleep=sleeps.append)
    try:
        client.get_json("/polizas")
        raised = False
    except ApiError as exc:
        raised = True
        assert exc.status == 401
    assert raised
    assert sleeps == []
    assert len(session.calls) == 1


# Un 429 espera lo que dice Retry-After antes de volver a pedir.
def test_429_uses_retry_after():
    sleeps = []
    session = FakeSession(
        [
            FakeResponse(429, {"error": "slow down"}, {"Retry-After": "0.25"}),
            FakeResponse(200, {"ok": True}),
        ]
    )
    client = ApiClient("https://example.test/v1", "token", session=session, sleep=sleeps.append)
    payload, _headers = client.get_json("/siniestros", {"offset": 0})
    assert payload == {"ok": True}
    assert sleeps == [0.25]


# El JSON de la API trae el token NaN en la moneda. Se lee como null, no como texto.
def test_nan_token_becomes_null():
    payload = loads_payload('{"amount": {"value": "10", "currency": NaN}}')
    assert payload["amount"]["currency"] is None


# updated_since solo va en la primera página. Si ya hay cursor, no se vuelve a mandar.
def test_poliza_params_send_watermark_only_without_cursor():
    assert poliza_params(None, None) == {}
    assert poliza_params(None, "2026-10-01T00:00:00Z") == {"updated_since": "2026-10-01T00:00:00Z"}
    assert poliza_params("cursor-1", "2026-10-01T00:00:00Z") == {"cursor": "cursor-1"}


# El cursor avanza solo cuando la página dice que hay más.
# El filtro tira las pólizas viejas que esa página todavía trae.
def test_cursor_and_watermark_filter():
    assert next_cursor({"has_more": True, "next_cursor": "abc"}) == "abc"
    assert next_cursor({"has_more": False, "next_cursor": "abc"}) is None
    rows = [
        {"poliza_id": "a", "updated_at": "2026-09-30T00:00:00Z"},
        {"poliza_id": "b", "updated_at": "2026-10-02T00:00:00Z"},
    ]
    kept = filter_polizas_since(rows, "2026-10-01T00:00:00Z")
    assert [row["poliza_id"] for row in kept] == ["b"]
    assert filter_polizas_since(rows, None) == rows
