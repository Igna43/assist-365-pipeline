from src.extract import normalize_siniestro


def test_claim_keeps_both_date_formats_and_null_currency():
    row = {
        "claim_id": "SIN-1",
        "policy_id": "POL-1",
        "occurred_at": "19/11/2024",
        "reported_at": "2024-11-22",
        "type": "DEMORA",
        "status": "PAGADO",
        "amount": {"value": "66.75", "currency": None},
        "detail": {"proveedor": "MedAssist", "city": "Orlando"},
    }
    out = normalize_siniestro(row, "batch", "2026-11-02T00:00:00Z")
    assert out["occurred_on"] == "2024-11-19"
    assert out["reported_on"] == "2024-11-22"
    assert out["amount_value"] == "66.75"
    assert out["amount_currency"] is None
    assert "Orlando" in out["detail"]
