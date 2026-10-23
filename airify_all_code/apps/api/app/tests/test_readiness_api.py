"""Tests for readiness/info API endpoints."""

from __future__ import annotations


def test_product_readiness(client):
    resp = client.get("/v1/product/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "demo"
    assert body["data_status"] == "mock"
    assert body["features"]["mock_pm25"] is True
    assert body["features"]["ml_ready"] is False


def test_privacy_summary(client):
    resp = client.get("/v1/security/privacy-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analytics_sdk"] == "none"
    assert body["third_party_sharing"] == "none"


def test_privacy_summary_uses_scoped_wording(client):
    """Privacy summary must NOT make absolute no-personal-data claims and must
    use scoped, honest wording that matches actual behavior."""
    resp = client.get("/v1/security/privacy-summary")
    assert resp.status_code == 200
    body = resp.json()

    # Serialize the whole response and check no absolute overclaim survives.
    import json

    blob = json.dumps(body).lower()
    assert "no personal data collected" not in blob
    assert '"personal_data": "none"' not in blob
    assert "personal_data: none" not in blob

    # Structured, honest fields.
    assert body["identity_fields_requested"] is False
    assert body["pii_key_stripping"] is True

    # Scoped claims present.
    assert "does not ask for name, email, or phone" in body["privacy_claim"].lower()
    assert "pii-like" in body["privacy_claim"].lower()
    assert "user-entered content" in body["free_text_notice"].lower()
    # personal_data field, if present, must be scoped rather than absolute.
    assert body["personal_data"] != "none"
    assert "free_text_may_contain_user_entered_content" in body["personal_data"]


def test_ml_readiness(client):
    resp = client.get("/v1/ml/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "stub_only"
    assert body["validated_models"] == 0
    assert body["planned_models"] > 0


def test_rag_readiness(client):
    resp = client.get("/v1/rag/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "stub_only"
    assert body["external_apis"] == "none"
    assert body["medical_claims_allowed"] is False


def test_health_context_disclaimer(client):
    resp = client.get("/v1/health-context/disclaimer")
    assert resp.status_code == 200
    body = resp.json()
    assert "not medical advice" in body["general"].lower()
    assert "general" in body
    assert "estimate" in body
    assert "recommendation" in body
