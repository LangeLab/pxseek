"""Tests for pxscraper.cli module."""

from unittest.mock import patch

import pandas as pd
import requests
from click.testing import CliRunner

from pxscraper.cli import main

MOCK_TSV = (
    "Dataset Identifier\tTitle\tRepos\tSpecies\tInstrument\tPublication\t"
    "LabHead\tAnnounce Date\tKeywords\tannouncementXML\n"
    '<a href="http://x.org/cgi/GetDataset?ID=PXD000001" target="_blank">PXD000001</a>\t'
    "Test title\tPRIDE\tHomo sapiens\tOrbitrap\tno pub\tJ Doe\t2025-01-01\ttest,\t\n"
    '<a href="http://x.org/cgi/GetDataset?ID=PXD000002" target="_blank">PXD000002</a>\t'
    "Another title\tMassIVE\tMus musculus\tQ Exactive\tno pub\tA Smith\t2025-02-01\tmouse,\t\n"
)


# ---------------------------------------------------------------------------
# --version and --help
# ---------------------------------------------------------------------------


class TestCliBasics:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.2.0" in result.output

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "fetch" in result.output
        assert "filter" in result.output
        assert "lookup" in result.output

    def test_fetch_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--refresh" in result.output
        assert "--cache-dir" in result.output


# ---------------------------------------------------------------------------
# fetch command
# ---------------------------------------------------------------------------


class TestFetchCommand:
    def test_fetch_writes_output(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            result = runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir)],
            )

        assert result.exit_code == 0, result.output
        assert output_file.exists()
        df = pd.read_csv(output_file, sep="\t")
        assert len(df) == 2
        assert "PXD000001" in df["dataset_id"].values

    def test_fetch_verbose(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            result = runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir), "-v"],
            )

        assert result.exit_code == 0
        assert "Downloading" in result.output

    def test_fetch_uses_cache(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        # First fetch populates cache
        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV) as mock_fetch:
            runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir)],
            )
            assert mock_fetch.call_count == 1

        # Second fetch uses cache (no API call)
        output_file2 = tmp_path / "result2.tsv"
        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV) as mock_fetch:
            result = runner.invoke(
                main,
                ["fetch", "-o", str(output_file2), "--cache-dir", str(cache_dir)],
            )
            assert mock_fetch.call_count == 0
            assert "cached" in result.output.lower()

    def test_fetch_refresh_bypasses_cache(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        # First fetch
        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir)],
            )

        # Second fetch with --refresh
        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV) as mock_fetch:
            runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir), "--refresh"],
            )
            assert mock_fetch.call_count == 1

    def test_fetch_output_has_clean_columns(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir)],
            )

        df = pd.read_csv(output_file, sep="\t")
        assert "dataset_id" in df.columns
        assert "announcementXML" not in df.columns
        assert "Dataset Identifier" not in df.columns

    def test_fetch_no_html_in_output(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir)],
            )

        content = output_file.read_text()
        assert "<a " not in content
        assert "</a>" not in content


# ---------------------------------------------------------------------------
# filter and lookup stubs
# ---------------------------------------------------------------------------


class TestStubs:
    def test_filter_stub(self):
        runner = CliRunner()
        result = runner.invoke(main, ["filter"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output

    def test_lookup_stub(self):
        runner = CliRunner()
        result = runner.invoke(main, ["lookup"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------


class TestFetchErrors:
    def test_fetch_network_error(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_summary",
            side_effect=requests.ConnectionError("network down"),
        ):
            result = runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir)],
            )

        assert result.exit_code != 0
        assert not output_file.exists()
