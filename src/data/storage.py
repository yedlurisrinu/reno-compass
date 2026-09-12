"""GCS session checkpoint persistence layer.

This module provides functions for reading, writing, and validating session
checkpoints in Google Cloud Storage using session tokens as keys.
It implements atomic writes (write-then-swap) and sliding/absolute TTL checks.
"""

import json
import logging
import os
import tempfile
from datetime import UTC, datetime

from google.cloud import storage
from google.cloud.exceptions import NotFound

from config.config import settings
from domain.dossier import Dossier, check_schema_version

logger = logging.getLogger("reno_project")


def _get_bucket():
    """Helper to return GCS bucket object using settings client context."""
    client = storage.Client(project=settings.gcp_project_id)
    return client.bucket(settings.gcs_bucket_name)


def _verify_ttl(dossier: Dossier) -> tuple[bool, str]:
    """Evaluates session expiration against sliding and absolute TTLs.

    Args:
        dossier: The loaded Dossier object.

    Returns:
        A tuple of (is_active: bool, status_message: str).
    """
    now = datetime.now(UTC)

    # Check absolute TTL (from creation)
    created_at = dossier.envelope.created_at.replace(tzinfo=UTC)
    abs_elapsed = (now - created_at).total_seconds()
    if abs_elapsed > settings.session_absolute_ttl_seconds:
        return (
            False,
            f"Session expired absolute TTL limit ({settings.session_absolute_ttl_seconds}s).",
        )

    # Check sliding TTL (from last update)
    last_updated_at = dossier.envelope.last_updated_at.replace(tzinfo=UTC)
    sliding_elapsed = (now - last_updated_at).total_seconds()
    if sliding_elapsed > settings.session_ttl_seconds:
        return False, f"Session expired sliding TTL limit ({settings.session_ttl_seconds}s)."

    return True, "Session is active and within TTL bounds."


# [Minor Decision] Fallback to local file storage for local test environments
# if GCS authentication context is not available.
def _use_local_fallback() -> bool:
    """Checks if we should fallback to local disk storage."""
    return os.getenv("STORAGE_LOCAL_FALLBACK", "false").lower() == "true"


def _get_local_storage_dir() -> str:
    """Returns local storage directory path."""
    return os.path.join(tempfile.gettempdir(), "reno_compass_sessions")


def read_session(session_token: str) -> Dossier | None:
    """Reads and parses session data from storage by session token.

    Verifies TTL limits and schema version compatibility.

    Args:
        session_token: The target session key (prefixed with reno_s_).

    Returns:
        Optional Dossier object if found and active, otherwise None.
    """
    if not session_token.startswith("reno_s_"):
        raise ValueError("Invalid session token format. Must be prefixed with 'reno_s_'.")

    json_content = None

    if _use_local_fallback():
        filepath = os.path.join(_get_local_storage_dir(), f"{session_token}.json")
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                json_content = f.read()
    else:
        try:
            bucket = _get_bucket()
            blob = bucket.blob(f"{session_token}.json")
            json_content = blob.download_as_text()
        except NotFound:
            filepath = os.path.join(_get_local_storage_dir(), f"{session_token}.json")
            if os.path.exists(filepath):
                with open(filepath, encoding="utf-8") as f:
                    json_content = f.read()
            else:
                return None
        except Exception as exc:
            # Observability: Log GCS connection issues and fallback to local disk
            logger.error(f"Error connecting to GCS: {exc}. Attempting local storage fallback.")
            filepath = os.path.join(_get_local_storage_dir(), f"{session_token}.json")
            if os.path.exists(filepath):
                with open(filepath, encoding="utf-8") as f:
                    json_content = f.read()
            else:
                return None

    if not json_content:
        return None

    try:
        data = json.loads(json_content)
        dossier = Dossier.model_validate(data)
    except Exception:
        # Schema validation failed / corrupted file
        return None

    # Verify Version compatibility
    compat_ok, compat_msg = check_schema_version(dossier.envelope.schema_version)
    if not compat_ok:
        logger.error(f"Schema compatibility error: {compat_msg}")
        return None

    # Verify TTL
    ttl_ok, ttl_msg = _verify_ttl(dossier)
    if not ttl_ok:
        logger.error(f"Session TTL error: {ttl_msg}")
        return None

    return dossier


def write_session(session_token: str, dossier: Dossier) -> None:
    """Atomic write/checkpoint session JSON to storage.

    Uses a temporary write-then-swap pattern to achieve write idempotency.

    Args:
        session_token: The target session key (prefixed with reno_s_).
        dossier: Dossier object to checkpoint.
    """
    if not session_token.startswith("reno_s_"):
        raise ValueError("Invalid session token format. Must be prefixed with 'reno_s_'.")

    # Update metadata timestamps
    dossier.envelope.last_updated_at = datetime.now(UTC)
    json_data = dossier.model_dump_json(indent=2)

    if _use_local_fallback():
        local_dir = _get_local_storage_dir()
        os.makedirs(local_dir, exist_ok=True)
        tmp_path = os.path.join(local_dir, f"{session_token}.json.tmp")
        final_path = os.path.join(local_dir, f"{session_token}.json")

        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(json_data)
        os.replace(tmp_path, final_path)
    else:
        try:
            bucket = _get_bucket()

            # Write to tmp blob
            tmp_blob = bucket.blob(f"{session_token}.json.tmp")
            tmp_blob.upload_from_string(json_data, content_type="application/json")

            # Atomically copy tmp blob to final location (swap)
            bucket.copy_blob(tmp_blob, bucket, f"{session_token}.json")

            # Delete tmp blob
            tmp_blob.delete()
        except Exception as exc:
            # GCS failure: log and execute local storage fallback to prevent request crash
            logger.error(
                f"GCS checkpoint failed for token {session_token} (bucket: {settings.gcs_bucket_name}). "
                f"Falling back to local disk storage. Error details: {exc}"
            )

            local_dir = _get_local_storage_dir()
            os.makedirs(local_dir, exist_ok=True)
            tmp_path = os.path.join(local_dir, f"{session_token}.json.tmp")
            final_path = os.path.join(local_dir, f"{session_token}.json")

            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(json_data)
            os.replace(tmp_path, final_path)


def delete_session(session_token: str) -> bool:
    """Best-effort removal of a session checkpoint from storage.

    Deletes the session blob from GCS and any local-fallback copy (a GCS write can
    fall back to disk, so both are swept). Never raises — cleanup failures must not
    break the caller's request; they are logged and reported via the return value.

    Args:
        session_token: The target session key (prefixed with reno_s_).

    Returns:
        True if a checkpoint was found and removed from at least one backend.
    """
    if not session_token.startswith("reno_s_"):
        raise ValueError("Invalid session token format. Must be prefixed with 'reno_s_'.")

    removed = False

    # GCS (skipped when explicitly running against local disk only).
    if not _use_local_fallback():
        try:
            bucket = _get_bucket()
            bucket.blob(f"{session_token}.json").delete()
            removed = True
        except NotFound:
            pass
        except Exception as exc:
            logger.error(f"Failed to delete GCS session blob for {session_token}: {exc}")

    # Local-fallback copy (present in local mode, or after a GCS write fell back to disk).
    try:
        filepath = os.path.join(_get_local_storage_dir(), f"{session_token}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            removed = True
    except Exception as exc:
        logger.error(f"Failed to delete local session file for {session_token}: {exc}")

    if removed:
        logger.info(f"Session checkpoint deleted for token {session_token}.")
    return removed
