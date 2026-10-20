"""One HTTP helper: retries, a polite User-Agent, and a raw copy of every download."""
import time
from datetime import date
from pathlib import Path

import requests

from erkit import config


def fetch(url: str, name: str, params: dict | None = None, retries: int = 3) -> bytes:
    """Download url, save the raw bytes under data/raw/<name>/<today>.<ext>, return them."""
    headers = {"User-Agent": config.USER_AGENT}
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=config.TIMEOUT)
            if r.status_code == 429:  # rate limited: back off and retry
                raise requests.HTTPError("429 Too Many Requests", response=r)
            r.raise_for_status()
            _save_raw(name, r.content, _ext(r.headers.get("Content-Type", "")))
            return r.content
        except requests.RequestException as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {name} from {url}: {last_err}")


def _ext(content_type: str) -> str:
    if "json" in content_type:
        return "json"
    if "csv" in content_type or "text" in content_type:
        return "csv"
    return "bin"


def _save_raw(name: str, content: bytes, ext: str) -> Path:
    folder = config.RAW_DIR / name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{date.today().isoformat()}.{ext}"
    path.write_bytes(content)
    return path
