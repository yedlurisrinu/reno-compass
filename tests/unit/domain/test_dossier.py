"""Unit tests for domain Pydantic dossier models and SemVer checks."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.dossier import (
    Dossier,
    check_schema_version,
    parse_semver,
)


def test_parse_semver_valid():
    """Verifies parsing of correct semantic version strings."""
    assert parse_semver("1.0.0") == [1, 0, 0]
    assert parse_semver("2.14.3") == [2, 14, 3]
    assert parse_semver("0.1.0") == [0, 1, 0]


def test_parse_semver_invalid():
    """Verifies that invalid semver strings raise ValueError."""
    with pytest.raises(ValueError):
        parse_semver("1.0")
    with pytest.raises(ValueError):
        parse_semver("a.b.c")
    with pytest.raises(ValueError):
        parse_semver("1.0.0.0")


def test_check_schema_version():
    """Verifies schema version compatibility checks under various mismatches.

    Enforces Versioning Dimension:
    * Major mismatch -> compatible = False
    * Minor mismatch -> compatible = True (with warnings)
    * Exact match -> compatible = True
    """
    # Exact Match
    ok, msg = check_schema_version("1.0.0", "1.0.0")
    assert ok is True
    assert "matches exactly" in msg

    # Major Mismatch
    ok, msg = check_schema_version("2.0.0", "1.0.0")
    assert ok is False
    assert "Major schema mismatch" in msg

    # Minor mismatch: import is older
    ok, msg = check_schema_version("1.0.0", "1.1.0")
    assert ok is True
    assert "Upgrading" in msg

    # Minor mismatch: import is newer
    ok, msg = check_schema_version("1.2.0", "1.1.0")
    assert ok is True
    assert "Proceeding with best-effort" in msg


def test_dossier_validation_correct():
    """Verifies Pydantic successfully parses a valid minimal dossier."""
    dossier_data = {
        "envelope": {
            "app_id": "reno-compass",
            "schema_version": "1.0.0",
            "dossier_id": "reno_s_test123",
            "created_at": datetime.now(UTC).isoformat(),
            "last_updated_at": datetime.now(UTC).isoformat(),
            "origin": "fresh",
            "current_stage": "scope",
        },
        "project": {},
    }
    dossier = Dossier.model_validate(dossier_data)
    assert dossier.envelope.dossier_id == "reno_s_test123"
    assert dossier.project.scope is None


def test_dossier_validation_incorrect():
    """Verifies Pydantic fails validation when required fields are missing/wrong type."""
    # missing dossier_id
    dossier_data = {
        "envelope": {"app_id": "reno-compass", "schema_version": "1.0.0"},
        "project": {},
    }
    with pytest.raises(ValidationError):
        Dossier.model_validate(dossier_data)
