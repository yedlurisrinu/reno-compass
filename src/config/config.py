"""Configuration module for the Reno Compass application.

This module defines the settings schema and loads configuration parameters
from environment variables using Pydantic Settings.
"""

import json
import os
import subprocess
import tempfile

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    import google.auth
except ImportError:
    google.auth = None


def _get_gcloud_config(key: str) -> str | None:
    """Helper to query the gcloud CLI config for a specific key."""
    try:
        val = (
            subprocess.check_output(
                ["gcloud", "config", "get-value", key], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        if val and "(unset)" not in val:
            return val
    except Exception:
        pass
    return None


def _discover_gcp_project_id() -> str | None:
    """Discovers the GCP Project ID dynamically from env, google-auth, or gcloud CLI."""
    # 1. Check environment variables
    for var in ["GCP_PROJECT_ID", "GOOGLE_CLOUD_PROJECT", "GCLOUD_PROJECT"]:
        val = os.getenv(var)
        if val:
            return val

    # 2. Try google.auth.default() (standard ADC)
    if google.auth:
        try:
            _, project_id = google.auth.default()
            if project_id:
                return project_id
        except Exception:
            pass

    # 3. Fallback to active gcloud config
    project_id = _get_gcloud_config("project")
    if project_id:
        return project_id

    return None


def _discover_vertex_location() -> str:
    """Discovers the Vertex location from env or active gcloud config, defaulting to us-central1."""
    # List of known regions where Vertex AI generative models (Gemini) are generally available
    SUPPORTED_GEMINI_REGIONS = {
        "us-central1",
        "us-west1",
        "us-east4",
        "us-west4",
        "europe-west1",
        "europe-west3",
        "europe-west4",
        "europe-west9",
        "asia-northeast1",
        "asia-southeast1",
    }

    # 1. Check environment variables (always respect manual overrides)
    for var in ["VERTEX_LOCATION", "GCP_REGION", "GOOGLE_CLOUD_REGION"]:
        val = os.getenv(var)
        if val:
            return val

    # 2. Try gcloud compute/region, validating if it supports Gemini
    region = _get_gcloud_config("compute/region")
    if region and region in SUPPORTED_GEMINI_REGIONS:
        return region

    # 3. Try gcloud compute/zone (extract region) and validate
    zone = _get_gcloud_config("compute/zone")
    if zone:
        parts = zone.split("-")
        if len(parts) >= 2:
            candidate_region = "-".join(parts[:2])
            if candidate_region in SUPPORTED_GEMINI_REGIONS:
                return candidate_region

    # Default fallback to us-central1 for Vertex AI Gemini model hosting
    return "us-central1"


class Settings(BaseSettings):
    """Application settings class parsing environment variables.

    Adheres to strict type hints and Pydantic v2 configuration guidelines.
    """

    # GCP Configurations
    gcp_project_id: str | None = Field(
        default=None,
        validation_alias="GCP_PROJECT_ID",
        description="The Google Cloud Project ID used for GCS and Vertex AI.",
    )
    gcs_bucket_name: str | None = Field(
        default=None,
        validation_alias="GCS_BUCKET_NAME",
        description="The GCS bucket name where session JSON checkpoints are stored.",
    )
    vertex_location: str | None = Field(
        default=None,
        validation_alias="VERTEX_LOCATION",
        description="The GCP location/region for Vertex AI API operations.",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias="GEMINI_MODEL",
        description="The Gemini model identifier to utilize in stage agents.",
    )

    # Authentication & Session Configurations
    session_ttl_seconds: int = Field(
        default=259200,  # 72 hours
        validation_alias="SESSION_TTL_SECONDS",
        description="Sliding session expiration duration in seconds.",
    )
    session_absolute_ttl_seconds: int = Field(
        default=2592000,  # 30 days
        validation_alias="SESSION_ABSOLUTE_TTL_SECONDS",
        description="Absolute session expiration duration in seconds from creation.",
    )
    rate_limit_per_minute: int = Field(
        default=10,
        validation_alias="RATE_LIMIT_PER_MINUTE",
        description="Max API chat requests allowed per token per minute (refill rate).",
    )
    rate_limit_burst: int = Field(
        default=5,
        validation_alias="RATE_LIMIT_BURST",
        description="Max API chat requests allowed in an instantaneous burst.",
    )

    # Credentials Fallback
    google_application_credentials_json: str | None = Field(
        default=None,
        validation_alias="GOOGLE_APPLICATION_CREDENTIALS_JSON",
        description="Optional raw service account JSON string for cross-account authentication.",
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
        description="Optional API key for authenticating with Google AI Studio (Generative Language API).",
    )

    # Product Scope — the renovation project types Reno Compass currently supports. The
    # guardrail data (safety tier matrix, cost bands, question bank) is bathroom-specific,
    # so the agent must plan ONLY these and politely decline anything else. Extend this
    # list ONLY in lockstep with adding the matching frozen reference data for that type.
    supported_project_types: list[str] = Field(
        default=["bathroom"],
        validation_alias="SUPPORTED_PROJECT_TYPES",
        description="Renovation project types the agent is allowed to plan (comma-separated in env).",
    )

    @field_validator("supported_project_types", mode="before")
    @classmethod
    def _split_supported_types(cls, value: object) -> object:
        """Allow a comma-separated env string (e.g. "bathroom,kitchen") for the list."""
        if isinstance(value, str):
            return [v.strip().lower() for v in value.split(",") if v.strip()]
        if isinstance(value, list):
            return [str(v).strip().lower() for v in value if str(v).strip()]
        return value

    @model_validator(mode="after")
    def resolve_dynamic_settings(self) -> "Settings":
        if not self.gcp_project_id:
            self.gcp_project_id = _discover_gcp_project_id()

        if not self.vertex_location:
            self.vertex_location = _discover_vertex_location()

        if not self.gcs_bucket_name:
            self.gcs_bucket_name = "reno-compass-checkpoints"

        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Instantiate settings
settings = Settings()

# Shorthands that still count as a supported type (e.g. "master bath" -> bathroom).
_SUPPORTED_TYPE_ALIASES = {
    "bathroom": ("bath", "powder room", "restroom", "washroom"),
}


def is_project_type_supported(project_type: str | None) -> bool:
    """Whether a project_type falls within the configured supported scope.

    Deliberately lenient so it only ever blocks a CLEARLY out-of-scope project:
    an unset/blank type is not yet a violation (scope is still being gathered), and
    a type that names a supported keyword or a known shorthand (e.g. "master bathroom
    remodel" or "master bath" -> bathroom) is supported. Anything else (e.g. "kitchen
    remodel") is unsupported.
    """
    if not project_type or not project_type.strip():
        return True
    pt = project_type.strip().lower()
    for t in settings.supported_project_types:
        if t in pt or any(alias in pt for alias in _SUPPORTED_TYPE_ALIASES.get(t, ())):
            return True
    return False


# Setup service account credentials if JSON string is provided
if settings.google_application_credentials_json:
    try:
        # Validate that the credentials string is a valid JSON
        json_data = json.loads(settings.google_application_credentials_json)

        # Write to a secure temporary file
        temp_creds = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        json.dump(json_data, temp_creds)
        temp_creds.close()

        # Export the standard GCP credentials environment variable to target the temp file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_creds.name
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid GOOGLE_APPLICATION_CREDENTIALS_JSON string configured.") from exc
