"""Paths and settings. Override with environment variables, never hard-code secrets."""
import os
from pathlib import Path

ROOT = Path(os.environ.get("ERKIT_HOME", Path.cwd()))
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"          # untouched downloads, one dated file per fetch
DB_PATH = DATA_DIR / "research.duckdb"
CATALOG_PATH = Path(os.environ.get("ERKIT_CATALOG", ROOT / "catalog.yaml"))

# SEC asks every client to identify itself: "Name email". Set ERKIT_USER_AGENT in your shell.
USER_AGENT = os.environ.get("ERKIT_USER_AGENT", "erkit research contact@example.com")

TIMEOUT = 60
