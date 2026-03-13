"""Local caching of fetched data.

Cache is stored in `.pxscraper_cache/` in the current working directory
so users can see and manage it directly. The directory is gitignored.
"""

import json
import time
from pathlib import Path

import pandas as pd

from pxscraper.models import CACHE_DIR_NAME, CACHE_META_FILE, DEFAULT_CACHE_MAX_AGE_HOURS


def get_cache_dir(base: Path | None = None) -> Path:
    """Return the cache directory path, creating it if needed.

    By default, uses `.pxscraper_cache/` in the current working directory.
    """
    base = base or Path.cwd()
    cache_dir = base / CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _meta_path(cache_dir: Path) -> Path:
    return cache_dir / CACHE_META_FILE


def _read_meta(cache_dir: Path) -> dict:
    meta_path = _meta_path(cache_dir)
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _write_meta(cache_dir: Path, meta: dict) -> None:
    _meta_path(cache_dir).write_text(json.dumps(meta, indent=2))


def save(df: pd.DataFrame, name: str, cache_dir: Path | None = None) -> Path:
    """Save a DataFrame to cache as TSV and record the timestamp."""
    cache_dir = cache_dir or get_cache_dir()
    filepath = cache_dir / f"{name}.tsv"
    df.to_csv(filepath, sep="\t", index=False)

    meta = _read_meta(cache_dir)
    meta[name] = {"timestamp": time.time(), "rows": len(df), "file": str(filepath.name)}
    _write_meta(cache_dir, meta)

    return filepath


def load(name: str, cache_dir: Path | None = None) -> pd.DataFrame | None:
    """Load a cached DataFrame by name. Returns None if not found."""
    cache_dir = cache_dir or get_cache_dir()
    filepath = cache_dir / f"{name}.tsv"
    if not filepath.exists():
        return None
    return pd.read_csv(filepath, sep="\t", dtype=str)


def is_stale(
    name: str,
    max_age_hours: float = DEFAULT_CACHE_MAX_AGE_HOURS,
    cache_dir: Path | None = None,
) -> bool:
    """Check if a cached dataset is older than max_age_hours.

    Returns True if cache is missing or stale.
    """
    cache_dir = cache_dir or get_cache_dir()
    meta = _read_meta(cache_dir)
    if name not in meta:
        return True
    age_hours = (time.time() - meta[name]["timestamp"]) / 3600
    return age_hours > max_age_hours


def cache_info(name: str, cache_dir: Path | None = None) -> dict | None:
    """Return metadata about a cached dataset, or None if not cached."""
    cache_dir = cache_dir or get_cache_dir()
    meta = _read_meta(cache_dir)
    return meta.get(name)
