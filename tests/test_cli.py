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
        assert "0.3.0" in result.output

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
# stubs (only lookup remains a stub)
# ---------------------------------------------------------------------------


class TestStubs:
    def test_lookup_stub(self):
        runner = CliRunner()
        result = runner.invoke(main, ["lookup"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output


# ---------------------------------------------------------------------------
# filter command
# ---------------------------------------------------------------------------


class TestFilterCommand:
    def test_filter_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["filter", "--help"])
        assert result.exit_code == 0
        for flag in ["--species", "--repo", "--keywords", "--after",
                      "--before", "--instrument", "--keyword-columns"]:
            assert flag in result.output

    def test_filter_requires_at_least_one_filter(self, tmp_path):
        runner = CliRunner()
        input_file = tmp_path / "data.tsv"
        input_file.write_text(
            "dataset_id\ttitle\trepository\tspecies\tinstrument\t"
            "publication\tlab_head\tannounce_date\tkeywords\n"
            "PXD000001\tTest\tPRIDE\tHomo sapiens\tOrbitrap\tno pub\tDoe\t2025-01-01\ttest,\n"
        )
        result = runner.invoke(
            main, ["filter", "-i", str(input_file), "-o", str(tmp_path / "out.tsv")]
        )
        assert result.exit_code != 0
        assert "No filters specified" in result.output

    def test_filter_with_input_file(self, tmp_path):
        runner = CliRunner()
        input_file = tmp_path / "data.tsv"
        output_file = tmp_path / "filtered.tsv"
        input_file.write_text(
            "dataset_id\ttitle\trepository\tspecies\tinstrument\t"
            "publication\tlab_head\tannounce_date\tkeywords\n"
            "PXD000001\tTest\tPRIDE\tHomo sapiens\tOrbitrap\tno pub\tDoe\t2025-01-01\ttest,\n"
            "PXD000002\tMouse\tPRIDE\tMus musculus\tOrbitrap\tno pub\tDoe\t2025-02-01\tmouse,\n"
        )
        result = runner.invoke(
            main,
            ["filter", "-i", str(input_file), "-o", str(output_file), "-s", "Homo"],
        )
        assert result.exit_code == 0, result.output
        assert "Filtered 2 -> 1" in result.output
        df = pd.read_csv(output_file, sep="\t")
        assert len(df) == 1
        assert df.iloc[0]["dataset_id"] == "PXD000001"

    def test_filter_auto_fetch(self, tmp_path):
        """Filter auto-fetches from API when no --input given."""
        runner = CliRunner()
        output_file = tmp_path / "filtered.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            result = runner.invoke(
                main,
                ["filter", "-o", str(output_file), "--cache-dir", str(cache_dir),
                 "-s", "Homo sapiens"],
            )

        assert result.exit_code == 0, result.output
        assert "Filtered" in result.output
        assert output_file.exists()

    def test_filter_uses_cache(self, tmp_path):
        """Filter uses existing cache without re-downloading."""
        runner = CliRunner()
        cache_dir = tmp_path / "cache"

        # Populate cache via fetch
        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            runner.invoke(
                main,
                ["fetch", "-o", str(tmp_path / "full.tsv"), "--cache-dir", str(cache_dir)],
            )

        # Filter should use cache (no API call)
        output_file = tmp_path / "filtered.tsv"
        with patch("pxscraper.api.fetch_summary") as mock_fetch:
            result = runner.invoke(
                main,
                ["filter", "-o", str(output_file), "--cache-dir", str(cache_dir),
                 "-s", "Homo"],
            )
            assert mock_fetch.call_count == 0
        assert result.exit_code == 0

    def test_filter_by_species(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "filtered.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            result = runner.invoke(
                main,
                ["filter", "-o", str(output_file), "--cache-dir", str(cache_dir),
                 "-s", "Mus musculus"],
            )

        assert result.exit_code == 0, result.output
        df = pd.read_csv(output_file, sep="\t")
        assert len(df) == 1
        assert df.iloc[0]["dataset_id"] == "PXD000002"

    def test_filter_by_repo(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "filtered.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            result = runner.invoke(
                main,
                ["filter", "-o", str(output_file), "--cache-dir", str(cache_dir),
                 "-r", "MassIVE"],
            )

        assert result.exit_code == 0
        df = pd.read_csv(output_file, sep="\t")
        assert len(df) == 1

    def test_filter_no_matches(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "filtered.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            result = runner.invoke(
                main,
                ["filter", "-o", str(output_file), "--cache-dir", str(cache_dir),
                 "-s", "Drosophila"],
            )

        assert result.exit_code == 0
        assert "No datasets matched" in result.output
        assert not output_file.exists()

    def test_filter_by_date(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "filtered.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            result = runner.invoke(
                main,
                ["filter", "-o", str(output_file), "--cache-dir", str(cache_dir),
                 "--after", "2025-02-01"],
            )

        assert result.exit_code == 0
        df = pd.read_csv(output_file, sep="\t")
        assert len(df) == 1
        assert df.iloc[0]["dataset_id"] == "PXD000002"

    def test_filter_connection_error(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "filtered.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_summary",
            side_effect=requests.ConnectionError("network down"),
        ):
            result = runner.invoke(
                main,
                ["filter", "-o", str(output_file), "--cache-dir", str(cache_dir),
                 "-s", "Homo"],
            )

        assert result.exit_code != 0
        assert "Could not reach ProteomeCentral" in result.output


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------


class TestFetchErrors:
    def test_fetch_connection_error(self, tmp_path):
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
        assert "Could not reach ProteomeCentral" in result.output
        assert not output_file.exists()

    def test_fetch_timeout_error(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_summary",
            side_effect=requests.Timeout("timed out"),
        ):
            result = runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir)],
            )

        assert result.exit_code != 0
        assert "timed out" in result.output

    def test_fetch_http_error(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_summary",
            side_effect=requests.HTTPError("500 Server Error"),
        ):
            result = runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir)],
            )

        assert result.exit_code != 0
        assert "error" in result.output.lower()


# ---------------------------------------------------------------------------
# parse diagnostics in CLI output
# ---------------------------------------------------------------------------


class TestFetchDiagnostics:
    def test_fetch_reports_no_skipped_rows_verbose(self, tmp_path):
        runner = CliRunner()
        output_file = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_summary", return_value=MOCK_TSV):
            result = runner.invoke(
                main,
                ["fetch", "-o", str(output_file), "--cache-dir", str(cache_dir), "-v"],
            )

        assert result.exit_code == 0
        assert "no rows skipped" in result.output.lower()
