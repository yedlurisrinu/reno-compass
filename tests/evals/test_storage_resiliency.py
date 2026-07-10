import datetime

import pytest

from config.config import settings
from data.storage import read_session, write_session
from domain.dossier import Dossier, DossierEnvelope, ProjectBody


def test_storage_gcs_fallback_resiliency(monkeypatch):
    """Verifies that GCS client failures fall back to local disk and do not crash requests."""
    # 1. Poison GCS bucket setting to trigger client connection error
    monkeypatch.setattr(
        settings, "gcs_bucket_name", "invalid-poisoned-bucket-name-that-does-not-exist"
    )

    token = "reno_s_test_resiliency_fallback"
    dossier = Dossier(
        envelope=DossierEnvelope(
            dossier_id=token,
            schema_version="1.0.0",
            created_at=datetime.datetime.now(datetime.UTC),
            last_updated_at=datetime.datetime.now(datetime.UTC),
            origin="fresh",
            current_stage="scope",
        ),
        project=ProjectBody(),
    )

    # 2. Write should succeed by falling back to local storage
    try:
        write_session(token, dossier)
    except Exception as e:
        pytest.fail(f"write_session crashed instead of falling back: {e}")

    # 3. Read should retrieve the dossier from local storage fallback
    try:
        loaded = read_session(token)
        assert loaded is not None
        assert loaded.envelope.dossier_id == token
    except Exception as e:
        pytest.fail(f"read_session crashed instead of falling back: {e}")
