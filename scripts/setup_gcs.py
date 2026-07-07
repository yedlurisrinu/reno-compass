#!/usr/bin/env python3
"""Script to initialize GCS storage bucket for Reno Compass session checkpoints."""

import os
import sys

# Ensure project root and src directories are in the Python search path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from google.cloud import storage
from src.config.config import settings


def init_gcs_bucket():
    """Creates the session GCS bucket if it does not already exist."""
    bucket_name = settings.gcs_bucket_name
    project_id = settings.gcp_project_id

    if not bucket_name or not project_id:
        print("Error: GCP_PROJECT_ID or GCS_BUCKET_NAME is not set in configuration.")
        sys.exit(1)

    print(f"Connecting to Google Cloud Storage (Project: {project_id})...")
    client = storage.Client(project=project_id)

    try:
        bucket = client.get_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except Exception:
        print(f"Bucket '{bucket_name}' not found. Attempting to create...")
        try:
            bucket = client.create_bucket(bucket_name, location=settings.vertex_location)
            print(
                f"Bucket '{bucket_name}' successfully created in location '{settings.vertex_location}'."
            )
        except Exception as exc:
            print(f"Failed to create bucket '{bucket_name}': {exc}")
            sys.exit(1)


if __name__ == "__main__":
    init_gcs_bucket()
