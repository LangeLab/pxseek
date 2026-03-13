"""Tests for pxscraper.cache module."""

import json
import time

import pandas as pd
import pytest

from pxscraper.cache import (
    cache_info,
    get_cache_dir,
    is_stale,
    load,
    save,
)
from pxscraper.models import CACHE_DIR_NAME, CACHE_META_FILE


@pytest.fixture()
def cache_dir(tmp_path):
    """Provide a temporary cache directory."""
    cdir = tmp_path / CACHE_DIR_NAME
    cdir.mkdir()
    return cdir


@pytest.fixture()
def sample_df():
    return pd.DataFrame(
        {
            "dataset_id": ["PXD000001", "PXD000002", "PXD000003"],
            "title": ["Title A", "Title B", "Title C"],
            "species": ["Homo sapiens", "Mus musculus", "Rattus norvegicus"],
        }
    )


# ---------------------------------------------------------------------------
# get_cache_dir
# ---------------------------------------------------------------------------


class TestGetCacheDir:
    def test_creates_dir(self, tmp_path):
        cdir = get_cache_dir(tmp_path)
        assert cdir.exists()
        assert cdir.name == CACHE_DIR_NAME

    def test_idempotent(self, tmp_path):
        cdir1 = get_cache_dir(tmp_path)
        cdir2 = get_cache_dir(tmp_path)
        assert cdir1 == cdir2

    def test_default_base_is_cwd(self):
        cdir = get_cache_dir()
        assert cdir.name == CACHE_DIR_NAME


# ---------------------------------------------------------------------------
# save / load roundtrip
# ---------------------------------------------------------------------------


class TestSaveLoad:
    def test_roundtrip(self, cache_dir, sample_df):
        save(sample_df, "test_data", cache_dir=cache_dir)
        loaded = load("test_data", cache_dir=cache_dir)
        assert loaded is not None
        assert len(loaded) == 3
        assert list(loaded["dataset_id"]) == ["PXD000001", "PXD000002", "PXD000003"]

    def test_save_creates_tsv_file(self, cache_dir, sample_df):
        save(sample_df, "mydata", cache_dir=cache_dir)
        assert (cache_dir / "mydata.tsv").exists()

    def test_save_creates_metadata(self, cache_dir, sample_df):
        save(sample_df, "mydata", cache_dir=cache_dir)
        meta_path = cache_dir / CACHE_META_FILE
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text())
        assert "mydata" in meta
        assert meta["mydata"]["rows"] == 3
        assert "timestamp" in meta["mydata"]

    def test_load_nonexistent_returns_none(self, cache_dir):
        assert load("nonexistent", cache_dir=cache_dir) is None

    def test_multiple_datasets(self, cache_dir, sample_df):
        df2 = sample_df.head(1)
        save(sample_df, "full", cache_dir=cache_dir)
        save(df2, "partial", cache_dir=cache_dir)

        full = load("full", cache_dir=cache_dir)
        partial = load("partial", cache_dir=cache_dir)
        assert len(full) == 3
        assert len(partial) == 1

        meta = json.loads((cache_dir / CACHE_META_FILE).read_text())
        assert "full" in meta
        assert "partial" in meta

    def test_overwrite(self, cache_dir, sample_df):
        save(sample_df, "data", cache_dir=cache_dir)
        save(sample_df.head(1), "data", cache_dir=cache_dir)
        loaded = load("data", cache_dir=cache_dir)
        assert len(loaded) == 1


# ---------------------------------------------------------------------------
# is_stale
# ---------------------------------------------------------------------------


class TestIsStale:
    def test_missing_is_stale(self, cache_dir):
        assert is_stale("nonexistent", cache_dir=cache_dir) is True

    def test_fresh_is_not_stale(self, cache_dir, sample_df):
        save(sample_df, "fresh", cache_dir=cache_dir)
        assert is_stale("fresh", max_age_hours=1, cache_dir=cache_dir) is False

    def test_old_is_stale(self, cache_dir, sample_df):
        save(sample_df, "old", cache_dir=cache_dir)
        # Manually backdate the timestamp
        meta_path = cache_dir / CACHE_META_FILE
        meta = json.loads(meta_path.read_text())
        meta["old"]["timestamp"] = time.time() - 48 * 3600  # 48 hours ago
        meta_path.write_text(json.dumps(meta))
        assert is_stale("old", max_age_hours=24, cache_dir=cache_dir) is True

    def test_custom_max_age(self, cache_dir, sample_df):
        save(sample_df, "data", cache_dir=cache_dir)
        # Even 0 hours max age should make it stale (unless instant)
        # We just need to check the logic works with different values
        assert is_stale("data", max_age_hours=99999, cache_dir=cache_dir) is False


# ---------------------------------------------------------------------------
# cache_info
# ---------------------------------------------------------------------------


class TestCacheInfo:
    def test_existing(self, cache_dir, sample_df):
        save(sample_df, "info_test", cache_dir=cache_dir)
        info = cache_info("info_test", cache_dir=cache_dir)
        assert info is not None
        assert info["rows"] == 3
        assert "timestamp" in info

    def test_nonexistent(self, cache_dir):
        assert cache_info("nope", cache_dir=cache_dir) is None
