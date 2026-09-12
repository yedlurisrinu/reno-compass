"""Coverage for the GCS-backed and error branches of the storage layer.

The default suite runs in ``STORAGE_LOCAL_FALLBACK`` mode, so the GCS read /
write / delete paths and their disk-fallback recovery never execute. Here we
monkeypatch ``_use_local_fallback`` off and stub ``_get_bucket`` so those
branches — plus the invalid-token guards and corrupted-file handling — run.
"""

import json
import os
import tempfile
from datetime import UTC, datetime

import pytest
from google.cloud.exceptions import NotFound

import data.storage as storage
from domain.dossier import Dossier, DossierEnvelope, ProjectBody


def _dossier(token="reno_s_gcs"):
    return Dossier(
        envelope=DossierEnvelope(
            dossier_id=token,
            schema_version="1.0.0",
            created_at=datetime.now(UTC),
            last_updated_at=datetime.now(UTC),
            origin="fresh",
            current_stage="scope",
        ),
        project=ProjectBody(),
    )


class _FakeBlob:
    def __init__(self, store, name):
        self._store = store
        self._name = name

    def upload_from_string(self, data, content_type=None):
        self._store[self._name] = data

    def download_as_text(self):
        if self._name not in self._store:
            raise NotFound(f"{self._name} missing")
        return self._store[self._name]

    def delete(self):
        if self._name not in self._store:
            raise NotFound(f"{self._name} missing")
        del self._store[self._name]


class _FakeBucket:
    def __init__(self, store):
        self._store = store

    def blob(self, name):
        return _FakeBlob(self._store, name)

    def copy_blob(self, src_blob, _bucket, dest_name):
        self._store[dest_name] = self._store[src_blob._name]


@pytest.fixture
def gcs(monkeypatch):
    """Forces GCS mode with an in-memory fake bucket; returns the backing store."""
    store: dict[str, str] = {}
    monkeypatch.setattr(storage, "_use_local_fallback", lambda: False)
    monkeypatch.setattr(storage, "_get_bucket", lambda: _FakeBucket(store))
    return store


# --------------------------------------------------------------------------- #
# Invalid-token guards
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("fn", [storage.read_session, storage.delete_session])
def test_invalid_token_raises(fn):
    with pytest.raises(ValueError):
        fn("bad_token")


def test_write_invalid_token_raises():
    with pytest.raises(ValueError):
        storage.write_session("bad_token", _dossier())


# --------------------------------------------------------------------------- #
# GCS happy paths
# --------------------------------------------------------------------------- #


def test_gcs_write_then_read_roundtrip(gcs):
    token = "reno_s_roundtrip"
    storage.write_session(token, _dossier(token))
    # tmp blob swapped to final and removed.
    assert f"{token}.json" in gcs
    assert f"{token}.json.tmp" not in gcs

    loaded = storage.read_session(token)
    assert loaded is not None
    assert loaded.envelope.dossier_id == token


def test_gcs_read_not_found_no_local_copy(gcs, monkeypatch):
    # Point the local fallback dir somewhere empty so the NotFound branch returns None.
    monkeypatch.setattr(
        storage, "_get_local_storage_dir", lambda: os.path.join(tempfile.mkdtemp(), "empty")
    )
    assert storage.read_session("reno_s_absent") is None


def test_gcs_delete_found_and_missing(gcs):
    token = "reno_s_del"
    storage.write_session(token, _dossier(token))
    assert storage.delete_session(token) is True
    # Second delete: blob gone (NotFound) and no local copy -> False.
    assert storage.delete_session(token) is False


# --------------------------------------------------------------------------- #
# GCS failure -> local disk fallback
# --------------------------------------------------------------------------- #


def test_gcs_write_falls_back_to_disk(monkeypatch):
    token = "reno_s_fallback"
    monkeypatch.setattr(storage, "_use_local_fallback", lambda: False)

    def _boom():
        raise RuntimeError("GCS down")

    monkeypatch.setattr(storage, "_get_bucket", _boom)
    local_dir = tempfile.mkdtemp()
    monkeypatch.setattr(storage, "_get_local_storage_dir", lambda: local_dir)

    storage.write_session(token, _dossier(token))
    # The disk-fallback wrote the final file.
    assert os.path.exists(os.path.join(local_dir, f"{token}.json"))


def test_gcs_read_error_recovers_from_disk(monkeypatch):
    token = "reno_s_recover"
    local_dir = tempfile.mkdtemp()
    monkeypatch.setattr(storage, "_use_local_fallback", lambda: False)
    monkeypatch.setattr(storage, "_get_local_storage_dir", lambda: local_dir)

    # Seed a valid checkpoint on disk.
    with open(os.path.join(local_dir, f"{token}.json"), "w", encoding="utf-8") as f:
        f.write(_dossier(token).model_dump_json())

    def _boom():
        raise RuntimeError("transient GCS error")

    monkeypatch.setattr(storage, "_get_bucket", _boom)
    loaded = storage.read_session(token)
    assert loaded is not None and loaded.envelope.dossier_id == token


# --------------------------------------------------------------------------- #
# Corrupted checkpoint -> None
# --------------------------------------------------------------------------- #


def test_corrupted_local_file_returns_none(monkeypatch):
    token = "reno_s_corrupt"
    local_dir = tempfile.mkdtemp()
    monkeypatch.setattr(storage, "_use_local_fallback", lambda: True)
    monkeypatch.setattr(storage, "_get_local_storage_dir", lambda: local_dir)
    with open(os.path.join(local_dir, f"{token}.json"), "w", encoding="utf-8") as f:
        f.write("{not valid json")
    assert storage.read_session(token) is None


def test_valid_json_wrong_schema_shape_returns_none(monkeypatch):
    token = "reno_s_badshape"
    local_dir = tempfile.mkdtemp()
    monkeypatch.setattr(storage, "_use_local_fallback", lambda: True)
    monkeypatch.setattr(storage, "_get_local_storage_dir", lambda: local_dir)
    with open(os.path.join(local_dir, f"{token}.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"envelope": {"nope": 1}}))
    assert storage.read_session(token) is None
