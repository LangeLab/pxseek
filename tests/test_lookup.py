"""Tests for the 'lookup' CLI command."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import requests
from click.testing import CliRunner

from pxscraper.cli import main

# ---------------------------------------------------------------------------
# Fixtures / shared test data
# ---------------------------------------------------------------------------

# Minimal but fully valid ProteomeXchange XML with all fields used by
# parse_dataset_xml()
MOCK_XML_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<ProteomeXchangeDataset id="{dataset_id}" xmlns="http://proteomexchange.org/schema"
    formatVersion="1.4.0">
  <DatasetSummary title="Test dataset {dataset_id}" announceDate="2025-01-15"
      hostingRepository="PRIDE">
    <Description>A mock dataset for testing purposes.</Description>
  </DatasetSummary>
  <ReviewLevel>
    <cvParam accession="PRIDE:0000414" name="Peer-reviewed dataset" />
  </ReviewLevel>
  <SpeciesList>
    <Species>
      <cvParam accession="MS:1001207" name="taxonomy: scientific name"
               value="Homo sapiens" />
    </Species>
  </SpeciesList>
  <InstrumentList>
    <Instrument id="Instrument_1">
      <cvParam accession="MS:1001742" name="LTQ Orbitrap Velos" />
    </Instrument>
  </InstrumentList>
  <ModificationList>
    <cvParam accession="MOD:00696" name="phosphorylated residue" />
  </ModificationList>
  <KeywordList>
    <cvParam accession="PRIDE:0000428" name="submitter keyword" value="phosphoproteomics" />
  </KeywordList>
  <ContactList>
    <Contact id="project_submitter">
      <cvParam accession="MS:1000586" name="contact name" value="Jane Doe" />
      <cvParam accession="MS:1000589" name="contact email" value="jane@example.com" />
      <cvParam accession="MS:1000590" name="contact affiliation"
               value="Example University" />
    </Contact>
    <Contact id="project_lab_head">
      <cvParam accession="MS:1000586" name="contact name" value="John Smith" />
      <cvParam accession="MS:1000589" name="contact email" value="john@example.com" />
      <cvParam accession="MS:1000590" name="contact affiliation"
               value="Example University" />
    </Contact>
  </ContactList>
  <PublicationList>
    <Publication id="PMID123">
      <cvParam accession="MS:1000879" name="PubMed identifier" value="12345678" />
      <cvParam accession="MS:1001912"
               name="Digital Object Identifier (DOI)" value="10.1234/test" />
    </Publication>
  </PublicationList>
  <DatasetFileList>
    <DatasetFile id="FILE_1" name="test.raw">
      <cvParam accession="PRIDE:0000410" name="Dataset FTP location"
               value="ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD000001" />
    </DatasetFile>
  </DatasetFileList>
</ProteomeXchangeDataset>
"""

MOCK_XML_001 = MOCK_XML_TEMPLATE.format(dataset_id="PXD000001")
MOCK_XML_002 = MOCK_XML_TEMPLATE.format(dataset_id="PXD000002")


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def input_tsv(tmp_path):
    """Write a minimal filter-output TSV with two dataset IDs."""
    p = tmp_path / "filtered.tsv"
    p.write_text("dataset_id\ttitle\tspecies\nPXD000001\tFoo\tHomo sapiens\n"
                 "PXD000002\tBar\tMus musculus\n")
    return p


@pytest.fixture()
def ids_file(tmp_path):
    """Write a one-ID-per-line file."""
    p = tmp_path / "ids.txt"
    p.write_text("PXD000001\nPXD000002\n")
    return p


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestLookupHappyPath:
    def test_single_id_via_flag(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001},
        ):
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001", "-o", str(out),
                 "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code == 0, result.output
        assert out.exists()
        df = pd.read_csv(out, sep="\t")
        assert len(df) == 1
        assert df.iloc[0]["dataset_id"] == "PXD000001"

    def test_multiple_ids_via_flag(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001, "PXD000002": MOCK_XML_002},
        ):
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001,PXD000002",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code == 0, result.output
        df = pd.read_csv(out, sep="\t")
        assert len(df) == 2
        assert set(df["dataset_id"]) == {"PXD000001", "PXD000002"}

    def test_ids_file(self, runner, tmp_path, ids_file):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001, "PXD000002": MOCK_XML_002},
        ):
            result = runner.invoke(
                main,
                ["lookup", "--ids-file", str(ids_file),
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code == 0, result.output
        df = pd.read_csv(out, sep="\t")
        assert len(df) == 2

    def test_input_tsv_pipeline(self, runner, tmp_path, input_tsv):
        """Filter-output TSV is consumed as IDs for lookup."""
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001, "PXD000002": MOCK_XML_002},
        ):
            result = runner.invoke(
                main,
                ["lookup", "--input", str(input_tsv),
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code == 0, result.output
        df = pd.read_csv(out, sep="\t")
        assert len(df) == 2

    def test_ids_combined_with_ids_file(self, runner, tmp_path, ids_file):
        """--ids and --ids-file sources are merged and deduplicated."""
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        # PXD000001 appears in both --ids and --ids-file → should appear once
        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001, "PXD000002": MOCK_XML_002},
        ) as mock_fetch:
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001", "--ids-file", str(ids_file),
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code == 0, result.output
        # fetch_datasets_xml should be called with deduplicated IDs
        called_ids = mock_fetch.call_args[0][0]
        assert called_ids.count("PXD000001") == 1

    def test_output_has_expected_columns(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001},
        ):
            runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        df = pd.read_csv(out, sep="\t")
        for col in [
            "dataset_id", "title", "species", "instruments",
            "submitter_name", "lab_head_name",
        ]:
            assert col in df.columns, f"Missing column: {col}"

    def test_default_output_filename(self, runner, tmp_path):
        """Without -o the default output file is created."""
        cache_dir = tmp_path / "cache"

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with patch(
                "pxscraper.api.fetch_datasets_xml",
                return_value={"PXD000001": MOCK_XML_001},
            ):
                result = runner.invoke(
                    main,
                    ["lookup", "--ids", "PXD000001",
                     "--cache-dir", str(cache_dir), "--yes"],
                )
            assert result.exit_code == 0, result.output
            assert Path("lookup_results.tsv").exists()


# ---------------------------------------------------------------------------
# --yes / confirmation prompt
# ---------------------------------------------------------------------------


class TestLookupConfirmation:
    def test_yes_flag_skips_prompt(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001},
        ):
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )
        assert result.exit_code == 0

    def test_prompt_abort_exits_cleanly(self, runner, tmp_path):
        """Answering 'n' to the confirmation prompt aborts without error code 1."""
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch("pxscraper.api.fetch_datasets_xml") as mock_fetch:
            runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir)],
                input="n\n",
            )

        mock_fetch.assert_not_called()
        assert not out.exists()


# ---------------------------------------------------------------------------
# Cache behaviour
# ---------------------------------------------------------------------------


class TestLookupCache:
    def test_cache_hit_skips_fetch(self, runner, tmp_path):
        """IDs already cached on disk are not re-fetched."""
        out = tmp_path / "result.tsv"
        cache_base = tmp_path / "cache"
        # get_cache_dir appends .pxscraper_cache to the base
        actual_cache = cache_base / ".pxscraper_cache"
        actual_cache.mkdir(parents=True)
        (actual_cache / "PXD000001.xml").write_text(MOCK_XML_001, encoding="utf-8")
        cache_dir = cache_base

        with patch("pxscraper.api.fetch_datasets_xml") as mock_fetch:
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        mock_fetch.assert_not_called()
        assert result.exit_code == 0, result.output

    def test_partial_cache_fetches_only_missing(self, runner, tmp_path):
        """Cached IDs are served from disk; only uncached IDs are fetched."""
        out = tmp_path / "result.tsv"
        cache_base = tmp_path / "cache"
        actual_cache = cache_base / ".pxscraper_cache"
        actual_cache.mkdir(parents=True)
        (actual_cache / "PXD000001.xml").write_text(MOCK_XML_001, encoding="utf-8")
        cache_dir = cache_base

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000002": MOCK_XML_002},
        ) as mock_fetch:
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001,PXD000002",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code == 0, result.output
        called_ids = mock_fetch.call_args[0][0]
        assert called_ids == ["PXD000002"]
        df = pd.read_csv(out, sep="\t")
        assert len(df) == 2

    def test_fetched_xml_is_cached(self, runner, tmp_path):
        """After a successful lookup, the XML is written to cache."""
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001},
        ):
            runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert (cache_dir / ".pxscraper_cache" / "PXD000001.xml").exists()


# ---------------------------------------------------------------------------
# Error / edge-case tests
# ---------------------------------------------------------------------------


class TestLookupErrors:
    def test_no_ids_given_exits_with_error(self, runner, tmp_path):
        result = runner.invoke(main, ["lookup"])
        assert result.exit_code != 0
        assert "No PXD IDs" in result.output

    def test_invalid_id_exits_with_error(self, runner, tmp_path):
        result = runner.invoke(
            main,
            ["lookup", "--ids", "NOTANID", "--yes"],
        )
        assert result.exit_code != 0
        assert "Invalid" in result.output

    def test_mixed_valid_invalid_ids_exits(self, runner, tmp_path):
        result = runner.invoke(
            main,
            ["lookup", "--ids", "PXD000001,BADID", "--yes"],
        )
        assert result.exit_code != 0
        assert "BADID" in result.output

    def test_input_tsv_missing_dataset_id_column(self, runner, tmp_path):
        bad_tsv = tmp_path / "bad.tsv"
        bad_tsv.write_text("accession\ttitle\nPXD000001\tFoo\n")
        result = runner.invoke(
            main,
            ["lookup", "--input", str(bad_tsv), "--yes"],
        )
        assert result.exit_code != 0
        assert "dataset_id" in result.output

    def test_all_fetches_fail_exits_with_error(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": None},
        ):
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code != 0
        assert "all lookups failed" in result.output.lower()

    def test_partial_failure_writes_successful_rows(self, runner, tmp_path):
        """If some IDs fail, the successfully parsed rows are still written."""
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001, "PXD000002": None},
        ):
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001,PXD000002",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code == 0, result.output
        assert out.exists()
        df = pd.read_csv(out, sep="\t")
        assert len(df) == 1
        assert df.iloc[0]["dataset_id"] == "PXD000001"
        assert "Warning" in result.output or "warning" in result.output.lower()

    def test_connection_error_exits_friendly(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            side_effect=requests.ConnectionError("network down"),
        ):
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code != 0
        assert "Could not reach ProteomeCentral" in result.output

    def test_timeout_error_exits_friendly(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            side_effect=requests.Timeout("timed out"),
        ):
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code != 0
        assert "timed out" in result.output.lower()

    def test_duplicate_ids_deduplication(self, runner, tmp_path):
        """Duplicate IDs (same ID in --ids twice) are fetched only once."""
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001},
        ) as mock_fetch:
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001,PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        assert result.exit_code == 0, result.output
        called_ids = mock_fetch.call_args[0][0]
        assert called_ids.count("PXD000001") == 1


# ---------------------------------------------------------------------------
# --delay option
# ---------------------------------------------------------------------------


class TestLookupDelay:
    def test_delay_passed_to_fetch(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_dir = tmp_path / "cache"

        with patch(
            "pxscraper.api.fetch_datasets_xml",
            return_value={"PXD000001": MOCK_XML_001},
        ) as mock_fetch:
            runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001", "--delay", "0.5",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes"],
            )

        kwargs = mock_fetch.call_args[1]
        assert kwargs.get("delay") == 0.5


# ---------------------------------------------------------------------------
# --verbose flag
# ---------------------------------------------------------------------------


class TestLookupVerbose:
    def test_verbose_reports_cache_hits(self, runner, tmp_path):
        out = tmp_path / "result.tsv"
        cache_base = tmp_path / "cache"
        actual_cache = cache_base / ".pxscraper_cache"
        actual_cache.mkdir(parents=True)
        (actual_cache / "PXD000001.xml").write_text(MOCK_XML_001, encoding="utf-8")
        cache_dir = cache_base

        with patch("pxscraper.api.fetch_datasets_xml"):
            result = runner.invoke(
                main,
                ["lookup", "--ids", "PXD000001",
                 "-o", str(out), "--cache-dir", str(cache_dir), "--yes", "-v"],
            )

        assert "cached" in result.output.lower()


# ---------------------------------------------------------------------------
# Existing test_cli.py stub must now be updated (checked here for regression)
# ---------------------------------------------------------------------------


class TestLookupHelp:
    def test_lookup_help_shows_all_options(self, runner):
        result = runner.invoke(main, ["lookup", "--help"])
        assert result.exit_code == 0
        for flag in ["--ids", "--ids-file", "--input", "--output",
                     "--delay", "--yes", "--cache-dir"]:
            assert flag in result.output, f"Missing flag in help: {flag}"
