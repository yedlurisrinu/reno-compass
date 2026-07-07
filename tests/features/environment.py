"""Behave environment setup.

Enforces local storage fallback configuration to prevent GCS calls during BDD runs.
"""

import os
import shutil
import tempfile


def before_all(context):
    """Sets up local directory storage fallback before BDD scenarios run."""
    os.environ["STORAGE_LOCAL_FALLBACK"] = "true"
    context.tmpdir = tempfile.mkdtemp()

    # Inject the test temp directory function into the storage layer
    import data.storage

    data.storage._get_local_storage_dir = lambda: context.tmpdir


def after_all(context):
    """Cleans up temporary directory after all BDD runs complete."""
    shutil.rmtree(context.tmpdir)
    if "STORAGE_LOCAL_FALLBACK" in os.environ:
        del os.environ["STORAGE_LOCAL_FALLBACK"]
