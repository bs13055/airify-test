"""Readiness and info endpoints.

GET /v1/product/readiness — overall product readiness status
GET /v1/security/privacy-summary — privacy rules summary
GET /v1/ml/readiness — ML model readiness
GET /v1/rag/readiness — RAG system readiness
GET /v1/health-context/disclaimer — health disclaimer text

All mock/stub only. No external API calls. Not medical advice.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.health_context.disclaimers import GENERAL_DISCLAIMER, get_disclaimer
from app.ml.model_registry import ModelRegistry
from app.rag.grounding_policy import GroundingPolicy

router = APIRouter(tags=["readiness"])

_registry = ModelRegistry()
_grounding = GroundingPolicy()


@router.get("/v1/product/readiness")
def product_readiness() -> dict:
    return {
        "platform": "airify_v1",
        "status": "demo",
        "features": {
            "frontend": "react_vite_typescript",
            "backend": "fastapi_python",
            "ab_testing": True,
            "event_tracking": True,
            "pwa_ready": True,
            "mock_pm25": True,
            "ml_ready": False,
            "rag_ready": False,
            "medical_ready_foundation": True,
        },
        "data_status": "mock",
        "note": "Platform V1 demo. Mock data only. Not production ready.",
    }


@router.get("/v1/security/privacy-summary")
def privacy_summary() -> dict:
    return {
        "data_collection": "minimal_anonymous",
        "identity_fields_requested": False,
        "pii_key_stripping": True,
        "personal_data": "not_requested_by_demo; free_text_may_contain_user_entered_content",
        "location_precision": "3_decimals_max",
        "storage": "local_sqlite_only",
        "third_party_sharing": "none",
        "analytics_sdk": "none",
        "cookies": "none",
        "session_id": "random_uuid_localstorage",
        "deletion": "clear_browser_storage",
        "free_text_notice": (
            "Free-text feedback may contain user-entered content. Users are warned "
            "not to enter personal, address, or medical information."
        ),
        "privacy_claim": (
            "This demo does not ask for name, email, or phone and strips PII-like "
            "payload keys before local storage."
        ),
        "note": (
            "This demo does not ask for name, email, or phone; PII-like payload keys "
            "are stripped before local storage. Free-text feedback may still contain "
            "user-entered content. This is not a privacy compliance claim. "
            "Not production deployment."
        ),
    }


@router.get("/v1/ml/readiness")
def ml_readiness() -> dict:
    models = _registry.list_models()
    return {
        "status": "stub_only",
        "validated_models": 0,
        "planned_models": len(models),
        "models": [{"id": m.model_id, "type": m.model_type.value, "status": m.status.value} for m in models],
        "note": "No models trained or validated. Stub infrastructure only.",
    }


@router.get("/v1/rag/readiness")
def rag_readiness() -> dict:
    return {
        "status": "stub_only",
        "knowledge_entries": 4,
        "retrieval_method": "substring_match",
        "external_apis": "none",
        "vector_database": "none",
        "grounding_policy": "active",
        "medical_claims_allowed": _grounding.can_claim("medical_diagnosis"),
        "note": "Local stub only. No embedding models or external APIs.",
    }


@router.get("/v1/health-context/disclaimer")
def health_disclaimer() -> dict:
    return {
        "general": get_disclaimer("general"),
        "estimate": get_disclaimer("estimate"),
        "recommendation": get_disclaimer("recommendation"),
        "note": "All health-context outputs include mandatory disclaimers.",
    }
