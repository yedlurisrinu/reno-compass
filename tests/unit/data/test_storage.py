import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta

import pytest

from data.storage import read_session, write_session
from domain.dossier import Dossier, DossierEnvelope, ProjectBody


@pytest.fixture(autouse=True)
def setup_local_fallback(monkeypatch):
    """Enforces local fallback storage during test runs."""
    tmpdir = tempfile.mkdtemp()
    monkeypatch.setenv("STORAGE_LOCAL_FALLBACK", "true")
    # Dynamically inject the test temp directory function into storage.py
    import data.storage

    monkeypatch.setattr(data.storage, "_get_local_storage_dir", lambda: tmpdir)
    yield
    # Cleanup files
    shutil.rmtree(tmpdir)


def _create_test_dossier(
    token: str,
    schema_version: str = "1.0.0",
    created_at: datetime = None,
    last_updated_at: datetime = None,
) -> Dossier:
    """Helper to generate a mock Dossier object."""
    if not created_at:
        created_at = datetime.utcnow()
    if not last_updated_at:
        last_updated_at = datetime.utcnow()

    return Dossier(
        envelope=DossierEnvelope(
            dossier_id=token,
            schema_version=schema_version,
            created_at=created_at,
            last_updated_at=last_updated_at,
            origin="fresh",
            current_stage="scope",
        ),
        project=ProjectBody(),
    )


def test_session_token_prefix_enforcement():
    """Verifies write and read reject tokens lacking 'reno_s_' prefix."""
    dossier = _create_test_dossier("invalid_token")

    with pytest.raises(ValueError):
        write_session("invalid_token", dossier)

    with pytest.raises(ValueError):
        read_session("invalid_token")


def test_write_and_read_session_success():
    """Verifies atomic write followed by read loads identical data."""
    token = "reno_s_validtoken123"
    dossier = _create_test_dossier(token)

    write_session(token, dossier)
    loaded = read_session(token)

    assert loaded is not None
    assert loaded.envelope.dossier_id == token
    assert loaded.envelope.schema_version == "1.0.0"


def test_session_read_expired_sliding_ttl():
    """Verifies that a session past 72h sliding TTL returns None."""
    token = "reno_s_expired_sliding"
    dossier = _create_test_dossier(token)
    write_session(token, dossier)

    # Manually modify the file on disk to set last_updated_at to 4 days ago
    import data.storage

    filepath = os.path.join(data.storage._get_local_storage_dir(), f"{token}.json")
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    # Set last_updated_at back in time (sliding TTL is 72h = 3 days)
    data["envelope"]["last_updated_at"] = (datetime.utcnow() - timedelta(days=4)).isoformat()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)

    loaded = read_session(token)
    assert loaded is None


def test_session_read_expired_absolute_ttl():
    """Verifies that a session past 30 days absolute TTL returns None."""
    token = "reno_s_expired_abs"
    dossier = _create_test_dossier(token)
    write_session(token, dossier)

    # Manually modify the file on disk to set created_at and last_updated_at
    import data.storage

    filepath = os.path.join(data.storage._get_local_storage_dir(), f"{token}.json")
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    # Set created_at back in time (absolute TTL is 30 days)
    data["envelope"]["created_at"] = (datetime.utcnow() - timedelta(days=31)).isoformat()
    data["envelope"]["last_updated_at"] = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)

    loaded = read_session(token)
    assert loaded is None


def test_session_read_major_version_mismatch():
    """Verifies that a loaded session with major version mismatch returns None."""
    token = "reno_s_version_mismatch"
    # Current version is 1.0.0, we write a 2.0.0 dossier
    dossier = _create_test_dossier(token, schema_version="2.0.0")

    write_session(token, dossier)
    loaded = read_session(token)

    assert loaded is None
