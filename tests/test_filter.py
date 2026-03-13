"""Tests for pxscraper.filter module."""

import pandas as pd
import pytest

from pxscraper.filter import (
    apply_filters,
    by_date_range,
    by_instrument,
    by_keywords,
    by_repository,
    by_species,
)


@pytest.fixture()
def sample_df():
    """Small synthetic DataFrame mimicking parse_summary_tsv() output."""
    return pd.DataFrame(
        {
            "dataset_id": ["PXD000001", "PXD000002", "PXD000003", "PXD000004", "PXD000005"],
            "title": [
                "Cancer proteomics study",
                "Mouse brain phosphoproteomics",
                "Human plasma biomarkers",
                "Yeast cell cycle analysis",
                "Cancer immunopeptidomics in mice",
            ],
            "repository": ["PRIDE", "MassIVE", "PRIDE", "jPOST", "PRIDE"],
            "species": [
                "Homo sapiens",
                "Mus musculus",
                "Homo sapiens",
                "Saccharomyces cerevisiae",
                "Mus musculus; Homo sapiens",
            ],
            "instrument": [
                "Orbitrap Exploris 480",
                "Q Exactive HF",
                "timsTOF Pro",
                "Orbitrap Fusion Lumos",
                "Q Exactive HF",
            ],
            "publication": ["10.1234/a", "no pub", "10.1234/b", "no pub", "10.1234/c"],
            "lab_head": ["Smith", "Jones", "Smith", "Lee", "Jones"],
            "announce_date": [
                "2024-01-15",
                "2024-06-20",
                "2025-03-01",
                "2023-11-10",
                "2025-01-05",
            ],
            "keywords": [
                "cancer, proteomics,",
                "brain, phospho,",
                "plasma, biomarker,",
                "cell cycle, yeast,",
                "cancer, immunopeptidome,",
            ],
        }
    )


# ---------------------------------------------------------------------------
# by_species
# ---------------------------------------------------------------------------


class TestBySpecies:
    def test_exact_species(self, sample_df):
        result = by_species(sample_df, "Homo sapiens")
        assert list(result["dataset_id"]) == ["PXD000001", "PXD000003", "PXD000005"]

    def test_case_insensitive(self, sample_df):
        result = by_species(sample_df, "homo sapiens")
        assert len(result) == 3

    def test_partial_match(self, sample_df):
        result = by_species(sample_df, "mus")
        assert list(result["dataset_id"]) == ["PXD000002", "PXD000005"]

    def test_semicolon_delimited_match(self, sample_df):
        """Multi-species rows should match either species."""
        result = by_species(sample_df, "Mus musculus")
        assert "PXD000005" in result["dataset_id"].values

    def test_no_match(self, sample_df):
        result = by_species(sample_df, "Drosophila")
        assert len(result) == 0
        assert list(result.columns) == list(sample_df.columns)

    def test_regex_pattern(self, sample_df):
        result = by_species(sample_df, "Homo|Mus")
        assert len(result) == 4  # PXD1, 2, 3, 5

    def test_nan_handling(self, sample_df):
        sample_df.loc[0, "species"] = None
        result = by_species(sample_df, "Homo")
        assert "PXD000001" not in result["dataset_id"].values


# ---------------------------------------------------------------------------
# by_repository
# ---------------------------------------------------------------------------


class TestByRepository:
    def test_single_repo(self, sample_df):
        result = by_repository(sample_df, "PRIDE")
        assert list(result["dataset_id"]) == ["PXD000001", "PXD000003", "PXD000005"]

    def test_multiple_repos(self, sample_df):
        result = by_repository(sample_df, "PRIDE,MassIVE")
        assert len(result) == 4

    def test_case_insensitive(self, sample_df):
        result = by_repository(sample_df, "pride")
        assert len(result) == 3

    def test_spaces_around_repos(self, sample_df):
        result = by_repository(sample_df, " PRIDE , MassIVE ")
        assert len(result) == 4

    def test_no_match(self, sample_df):
        result = by_repository(sample_df, "PeptideAtlas")
        assert len(result) == 0

    def test_single_unique_repo(self, sample_df):
        result = by_repository(sample_df, "jPOST")
        assert list(result["dataset_id"]) == ["PXD000004"]


# ---------------------------------------------------------------------------
# by_keywords
# ---------------------------------------------------------------------------


class TestByKeywords:
    def test_single_keyword_in_title(self, sample_df):
        result = by_keywords(sample_df, "cancer")
        # PXD1 title has "Cancer", PXD5 title has "Cancer"
        assert len(result) >= 2

    def test_single_keyword_in_keywords_col(self, sample_df):
        result = by_keywords(sample_df, "biomarker")
        assert "PXD000003" in result["dataset_id"].values

    def test_multiple_keywords_or_logic(self, sample_df):
        result = by_keywords(sample_df, "cancer,yeast")
        assert "PXD000001" in result["dataset_id"].values
        assert "PXD000004" in result["dataset_id"].values

    def test_case_insensitive(self, sample_df):
        result = by_keywords(sample_df, "CANCER")
        assert len(result) >= 2

    def test_word_boundary_matching(self, sample_df):
        """'plasma' should match but 'plas' should not (word boundary)."""
        result_full = by_keywords(sample_df, "plasma")
        result_partial = by_keywords(sample_df, "plas")
        assert len(result_full) > 0
        assert len(result_partial) == 0

    def test_custom_columns(self, sample_df):
        # Search only in title column
        result = by_keywords(sample_df, "cancer", columns=["title"])
        assert len(result) >= 2

    def test_keyword_from_file(self, sample_df, tmp_path):
        kw_file = tmp_path / "keywords.txt"
        kw_file.write_text("cancer\nyeast\n")
        result = by_keywords(sample_df, str(kw_file))
        assert "PXD000001" in result["dataset_id"].values
        assert "PXD000004" in result["dataset_id"].values

    def test_keyword_file_with_blank_lines(self, sample_df, tmp_path):
        kw_file = tmp_path / "keywords.txt"
        kw_file.write_text("cancer\n\n  \nyeast\n")
        result = by_keywords(sample_df, str(kw_file))
        assert len(result) >= 3  # PXD1, PXD4, PXD5

    def test_no_match(self, sample_df):
        result = by_keywords(sample_df, "nonexistent_keyword_xyz")
        assert len(result) == 0

    def test_empty_keywords_returns_all(self, sample_df):
        result = by_keywords(sample_df, ",,,")
        assert len(result) == len(sample_df)

    def test_nan_handling(self, sample_df):
        sample_df.loc[0, "title"] = None
        sample_df.loc[0, "keywords"] = None
        result = by_keywords(sample_df, "cancer")
        assert "PXD000001" not in result["dataset_id"].values


# ---------------------------------------------------------------------------
# by_date_range
# ---------------------------------------------------------------------------


class TestByDateRange:
    def test_after_only(self, sample_df):
        result = by_date_range(sample_df, after="2025-01-01")
        ids = list(result["dataset_id"])
        assert "PXD000003" in ids  # 2025-03-01
        assert "PXD000005" in ids  # 2025-01-05
        assert "PXD000001" not in ids  # 2024-01-15

    def test_before_only(self, sample_df):
        result = by_date_range(sample_df, before="2024-01-31")
        ids = list(result["dataset_id"])
        assert "PXD000001" in ids  # 2024-01-15
        assert "PXD000004" in ids  # 2023-11-10
        assert "PXD000003" not in ids

    def test_both_after_and_before(self, sample_df):
        result = by_date_range(sample_df, after="2024-01-01", before="2024-12-31")
        ids = list(result["dataset_id"])
        assert "PXD000001" in ids
        assert "PXD000002" in ids
        assert "PXD000003" not in ids

    def test_inclusive_boundaries(self, sample_df):
        result = by_date_range(sample_df, after="2024-01-15", before="2024-01-15")
        assert list(result["dataset_id"]) == ["PXD000001"]

    def test_no_match(self, sample_df):
        result = by_date_range(sample_df, after="2030-01-01")
        assert len(result) == 0

    def test_unparseable_dates_excluded(self, sample_df):
        sample_df.loc[0, "announce_date"] = "not-a-date"
        result = by_date_range(sample_df, after="2020-01-01")
        assert "PXD000001" not in result["dataset_id"].values

    def test_nan_dates_excluded(self, sample_df):
        sample_df.loc[0, "announce_date"] = None
        result = by_date_range(sample_df, after="2020-01-01")
        assert "PXD000001" not in result["dataset_id"].values


# ---------------------------------------------------------------------------
# by_instrument
# ---------------------------------------------------------------------------


class TestByInstrument:
    def test_exact_instrument(self, sample_df):
        result = by_instrument(sample_df, "Orbitrap Exploris 480")
        assert list(result["dataset_id"]) == ["PXD000001"]

    def test_partial_match(self, sample_df):
        result = by_instrument(sample_df, "Orbitrap")
        ids = list(result["dataset_id"])
        assert "PXD000001" in ids
        assert "PXD000004" in ids

    def test_case_insensitive(self, sample_df):
        result = by_instrument(sample_df, "orbitrap")
        assert len(result) == 2

    def test_regex_pattern(self, sample_df):
        result = by_instrument(sample_df, "Q Exactive|timsTOF")
        assert len(result) == 3

    def test_no_match(self, sample_df):
        result = by_instrument(sample_df, "MALDI")
        assert len(result) == 0

    def test_nan_handling(self, sample_df):
        sample_df.loc[0, "instrument"] = None
        result = by_instrument(sample_df, "Orbitrap")
        assert "PXD000001" not in result["dataset_id"].values


# ---------------------------------------------------------------------------
# apply_filters
# ---------------------------------------------------------------------------


class TestApplyFilters:
    def test_single_filter(self, sample_df):
        df, summary = apply_filters(sample_df, species="Homo sapiens")
        assert summary["original_count"] == 5
        assert summary["filtered_count"] == 3
        assert len(summary["active_filters"]) == 1
        assert "species" in summary["active_filters"][0]

    def test_multiple_filters(self, sample_df):
        df, summary = apply_filters(
            sample_df, species="Homo sapiens", repository="PRIDE"
        )
        # PXD1 (Homo, PRIDE), PXD3 (Homo, PRIDE), PXD5 (Mus;Homo, PRIDE)
        assert summary["filtered_count"] == 3

    def test_combo_species_and_keywords(self, sample_df):
        df, summary = apply_filters(
            sample_df, species="Homo sapiens", keywords="cancer"
        )
        # Homo sapiens: PXD1, PXD3, PXD5
        # Then cancer: PXD1 title "Cancer...", PXD5 title "Cancer..."
        assert summary["filtered_count"] == 2
        assert "PXD000001" in df["dataset_id"].values
        assert "PXD000005" in df["dataset_id"].values

    def test_no_filters_returns_all(self, sample_df):
        df, summary = apply_filters(sample_df)
        assert summary["original_count"] == 5
        assert summary["filtered_count"] == 5
        assert summary["active_filters"] == []

    def test_date_filter_in_summary(self, sample_df):
        df, summary = apply_filters(sample_df, after="2025-01-01")
        assert any("date" in f for f in summary["active_filters"])
        assert "after" in summary["active_filters"][0]

    def test_all_filters_combined(self, sample_df):
        df, summary = apply_filters(
            sample_df,
            species="Homo",
            repository="PRIDE",
            keywords="cancer",
            after="2024-01-01",
            instrument="Orbitrap|Q Exactive",
        )
        assert summary["filtered_count"] <= summary["original_count"]
        assert len(summary["active_filters"]) == 5

    def test_keyword_columns_passthrough(self, sample_df):
        # Search only in title
        df, summary = apply_filters(
            sample_df, keywords="proteomics", keyword_columns="title"
        )
        # word-boundary: "proteomics" matches PXD1, but not "phosphoproteomics" in PXD2
        assert summary["filtered_count"] == 1

    def test_returns_copy(self, sample_df):
        df, _ = apply_filters(sample_df, species="Homo sapiens")
        assert df is not sample_df


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------


class TestFilterEdgeCases:
    """Edge cases not covered by specific filter class tests."""

    @pytest.fixture()
    def empty_df(self, sample_df):
        """Zero-row DataFrame with correct columns."""
        return sample_df.iloc[0:0].copy()

    def test_empty_df_by_species(self, empty_df):
        result = by_species(empty_df, "Homo sapiens")
        assert len(result) == 0
        assert list(result.columns) == list(empty_df.columns)

    def test_empty_df_by_repository(self, empty_df):
        result = by_repository(empty_df, "PRIDE")
        assert len(result) == 0

    def test_empty_df_by_keywords(self, empty_df):
        result = by_keywords(empty_df, "cancer")
        assert len(result) == 0

    def test_empty_df_by_date_range(self, empty_df):
        result = by_date_range(empty_df, after="2024-01-01")
        assert len(result) == 0

    def test_empty_df_by_instrument(self, empty_df):
        result = by_instrument(empty_df, "Orbitrap")
        assert len(result) == 0

    def test_empty_df_apply_filters(self, empty_df):
        df, summary = apply_filters(empty_df, species="Homo", keywords="cancer")
        assert summary["original_count"] == 0
        assert summary["filtered_count"] == 0
        assert len(summary["active_filters"]) == 2

    def test_special_chars_in_keyword_escaped(self, sample_df):
        r"""Keywords with regex special chars are escaped via \b re.escape."""
        result = by_keywords(sample_df, "cancer (advanced)")
        assert len(result) == 0  # not in data, but should not raise

    def test_date_format_validation(self, sample_df):
        """Non-YYYY-MM-DD dates in the column are coerced to NaT."""
        sample_df.loc[0, "announce_date"] = "Jan 15, 2024"
        result = by_date_range(sample_df, after="2020-01-01")
        assert "PXD000001" not in result["dataset_id"].values
