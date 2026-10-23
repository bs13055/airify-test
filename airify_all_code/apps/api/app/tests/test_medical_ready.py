"""Tests for medical-ready foundation modules.

Ensures health_context, ML, and RAG modules follow safety rules:
- No medical claims
- No heavy ML imports
- No external API calls
- All outputs include disclaimers
- Stubs only
"""

from __future__ import annotations

import ast
from pathlib import Path


class TestHealthContext:
    """Tests for health_context module."""

    def test_disclaimers_available(self):
        from app.health_context.disclaimers import get_disclaimer
        d = get_disclaimer("general")
        assert "not medical advice" in d.lower()

    def test_disclaimer_contexts(self):
        from app.health_context.disclaimers import get_disclaimer
        for ctx in ("general", "estimate", "recommendation", "feedback", "pwa"):
            d = get_disclaimer(ctx)
            assert len(d) > 10
            assert "medical" in d.lower() or "mock" in d.lower()

    def test_must_include_disclaimer_adds_field(self):
        from app.health_context.disclaimers import must_include_disclaimer
        output = {"data": "test"}
        result = must_include_disclaimer(output)
        assert "disclaimer" in result
        assert "not medical advice" in result["disclaimer"].lower()

    def test_risk_profile_is_placeholder(self):
        from app.health_context.risk_profiles import get_default_profile
        p = get_default_profile()
        assert p.sensitivity.value == "general"
        assert "placeholder" in p.note.lower() or "not" in p.disclaimer.lower()

    def test_consent_text_includes_key_points(self):
        from app.health_context.consent import (
            consent_includes_key_points,
            get_demo_consent_text,
        )
        text = get_demo_consent_text()
        assert consent_includes_key_points(text)
        assert "not medical advice" in text.lower()
        assert "mock data" in text.lower()

    def test_consent_text_does_not_claim_zero_personal_data(self):
        """Consent must use scoped wording, not absolute no-personal-data claims."""
        from app.health_context.consent import get_demo_consent_text

        text = get_demo_consent_text().lower()
        assert "no personal data" not in text
        assert "no personal data collected" not in text
        # Scoped, honest wording present.
        assert "does not ask for your name, email, or phone" in text
        assert "free-text feedback" in text
        assert "may still contain" in text


class TestMLModule:
    """Tests for ML stub module."""

    def test_model_registry_lists_models(self):
        from app.ml.model_registry import ModelRegistry
        reg = ModelRegistry()
        models = reg.list_models()
        assert len(models) > 0
        # All models should be in planned/stub status.
        for m in models:
            assert m.status.value == "planned"
            assert m.validated is False

    def test_no_validated_model(self):
        from app.ml.model_registry import ModelRegistry
        reg = ModelRegistry()
        assert reg.has_validated_model() is False

    def test_inference_returns_stub(self):
        from app.ml.inference_service import InferenceService
        from app.models.observations import GeoPoint
        svc = InferenceService()
        result = svc.predict(GeoPoint(lat=13.75, lon=100.5))
        assert result.is_stub is True
        assert result.pm25_predicted is None
        assert result.model_id == "none"

    def test_feature_schema_separates_pm25_from_weather(self):
        from app.ml.feature_schema import FeatureSet, Pm25Label, SpatialFeatures
        # Feature set should have separate weather and PM2.5 label.
        fs = FeatureSet(spatial=SpatialFeatures(lat=13.0, lon=100.0))
        assert fs.weather is not None
        assert fs.label is None  # Label separate
        # PM2.5 label when provided is distinct from weather.
        label = Pm25Label(pm25_ug_m3=25.0)
        assert label.source == "air4thai_pcd"

    def test_ml_modules_no_heavy_imports(self):
        """ML modules must NOT import xgboost, torch, tensorflow, etc."""
        ml_dir = Path(__file__).resolve().parents[1] / "ml"
        forbidden = {"xgboost", "torch", "tensorflow", "sklearn", "lightgbm", "keras"}
        offenders = {}
        for f in ml_dir.glob("*.py"):
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in forbidden:
                            offenders.setdefault(f.name, []).append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    mod = (node.module or "").split(".")[0]
                    if mod in forbidden:
                        offenders.setdefault(f.name, []).append(node.module)
        assert offenders == {}, f"Heavy ML imports found: {offenders}"


class TestRAGModule:
    """Tests for RAG stub module."""

    def test_knowledge_base_search(self):
        from app.rag.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        results = kb.search("pm2.5")
        assert len(results) > 0
        for entry in results:
            assert entry.entry_id
            assert entry.content

    def test_retrieval_service_is_stub(self):
        from app.rag.retrieval_service import RetrievalService
        svc = RetrievalService()
        result = svc.retrieve("air quality")
        assert result.is_stub is True
        assert result.method == "substring_match"

    def test_grounding_policy_blocks_medical_claims(self):
        from app.rag.grounding_policy import GroundingPolicy
        policy = GroundingPolicy()
        # Medical claims are never allowed.
        assert policy.can_claim("medical_diagnosis") is False
        assert policy.can_claim("disease_prediction") is False
        assert policy.can_claim("treatment_recommendation") is False
        assert policy.can_claim("clinical_advice") is False

    def test_grounding_policy_requires_source(self):
        from app.rag.grounding_policy import GroundingPolicy
        policy = GroundingPolicy()
        # Claims requiring source should fail without one.
        assert policy.can_claim("pm25_measurement", has_source=False) is False
        assert policy.can_claim("pm25_measurement", has_source=True) is True

    def test_rag_modules_no_external_api_imports(self):
        """RAG modules must NOT import openai, google, etc."""
        rag_dir = Path(__file__).resolve().parents[1] / "rag"
        forbidden = {"openai", "google", "anthropic", "cohere", "pinecone", "chromadb"}
        offenders = {}
        for f in rag_dir.glob("*.py"):
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in forbidden:
                            offenders.setdefault(f.name, []).append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    mod = (node.module or "").split(".")[0]
                    if mod in forbidden:
                        offenders.setdefault(f.name, []).append(node.module)
        assert offenders == {}, f"External API imports found: {offenders}"


class TestPWAFiles:
    """Tests for PWA manifest and service worker."""

    def test_manifest_exists(self):
        manifest = Path(__file__).resolve().parents[4] / "apps" / "web" / "public" / "manifest.webmanifest"
        assert manifest.is_file(), "manifest.webmanifest must exist in public/"

    def test_service_worker_exists(self):
        sw = Path(__file__).resolve().parents[4] / "apps" / "web" / "public" / "service-worker.js"
        assert sw.is_file(), "service-worker.js must exist in public/"

    def test_service_worker_local_only(self):
        """Service worker must only cache local assets."""
        sw = Path(__file__).resolve().parents[4] / "apps" / "web" / "public" / "service-worker.js"
        text = sw.read_text(encoding="utf-8")
        # Must not reference external domains.
        forbidden = ["googleapis.com", "cdnjs", "unpkg", "jsdelivr", "google-analytics"]
        for f in forbidden:
            assert f not in text, f"External reference in service-worker.js: {f}"
        # Should reference local paths.
        assert "/" in text

    def test_manifest_content(self):
        import json
        manifest = Path(__file__).resolve().parents[4] / "apps" / "web" / "public" / "manifest.webmanifest"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["name"]
        assert data["short_name"] == "Airify"
        assert data["start_url"] == "/"
        assert "not medical advice" in data.get("description", "").lower() or \
               "mock data" in data.get("description", "").lower()


class TestDocsRuntime:
    """Tests for docs_runtime readiness documents."""

    def test_required_docs_exist(self):
        docs_dir = Path(__file__).resolve().parents[4] / "docs_runtime"
        required = [
            "medical_ready_notes.md",
            "model_readiness_notes.md",
            "rag_readiness_notes.md",
            "security_baseline.md",
            "deployment_readiness.md",
            "mobile_pwa_security.md",
            "ab_testing_ethics.md",
            "privacy_policy_draft.md",
        ]
        for name in required:
            assert (docs_dir / name).is_file(), f"Missing: docs_runtime/{name}"

    def test_no_deploy_commands_in_makefile(self):
        makefile = Path(__file__).resolve().parents[4] / "Makefile"
        text = makefile.read_text(encoding="utf-8")
        # Check that no actual deploy/aws targets exist (comments mentioning "no deployment" are ok).
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            # Skip comments.
            if stripped.startswith("#"):
                continue
            assert "deploy:" not in stripped, "Deploy target found in Makefile"
            assert "aws " not in stripped.lower(), "AWS command found in Makefile"
