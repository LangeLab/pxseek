"""Tests for pxscraper.parse module."""

from pathlib import Path

import pytest

from pxscraper.parse import parse_dataset_xml, parse_summary_tsv, strip_html

# ---------------------------------------------------------------------------
# strip_html
# ---------------------------------------------------------------------------


class TestStripHtml:
    def test_simple_anchor(self):
        raw = '<a href="http://example.com" target="_blank">PXD063194</a>'
        assert strip_html(raw) == "PXD063194"

    def test_nested_tags(self):
        raw = '<b><a href="#">Hello</a></b>'
        assert strip_html(raw) == "Hello"

    def test_multiple_anchors(self):
        raw = (
            '<a href="https://doi.org/10.1234">10.1234</a>; '
            '<a href="https://pubmed.org/123">Author (2025)</a>'
        )
        assert strip_html(raw) == "10.1234; Author (2025)"

    def test_plain_text_unchanged(self):
        assert strip_html("Homo sapiens") == "Homo sapiens"

    def test_empty_string(self):
        assert strip_html("") == ""

    def test_non_string_passthrough(self):
        assert strip_html(None) is None
        assert strip_html(42) == 42

    def test_self_closing_tag(self):
        assert strip_html("text<br/>more") == "textmore"

    def test_whitespace_stripping(self):
        assert strip_html("  <b>hello</b>  ") == "hello"


# ---------------------------------------------------------------------------
# parse_summary_tsv
# ---------------------------------------------------------------------------

SAMPLE_TSV = (
    "Dataset Identifier\tTitle\tRepos\tSpecies\tInstrument\tPublication\tLabHead\t"
    "Announce Date\tKeywords\tannouncementXML\t\n"
    '<a href="http://x.org/cgi/GetDataset?ID=PXD063194" target="_blank">PXD063194</a>\t'
    "Treadmill training and venlafaxine\tPRIDE\tRattus norvegicus \tOrbitrap Exploris 480\t"
    '<a href="https://doi.org/10.1016/x" target="_blank">10.1016/x</a>\tMaciej Suski\t'
    "2026-03-13\tfrontal cortex, depression, \t\t\n"
    '<a href="http://x.org/cgi/GetDataset?ID=PXD036143" target="_blank">PXD036143</a>\t'
    "Surface proteins\tMassIVE\tHomo sapiens\tmaXis II\tno publication\t"
    "Lilla Turiak\t2026-03-13\tbiotinylated peptides, \t\t\n"
)


class TestParseSummaryTsv:
    def test_basic_shape(self):
        df = parse_summary_tsv(SAMPLE_TSV)
        assert len(df) == 2
        assert list(df.columns) == [
            "dataset_id", "title", "repository", "species",
            "instrument", "publication", "lab_head", "announce_date", "keywords",
        ]

    def test_html_stripped_from_dataset_id(self):
        df = parse_summary_tsv(SAMPLE_TSV)
        assert df.iloc[0]["dataset_id"] == "PXD063194"
        assert df.iloc[1]["dataset_id"] == "PXD036143"

    def test_html_stripped_from_publication(self):
        df = parse_summary_tsv(SAMPLE_TSV)
        assert "<a" not in df.iloc[0]["publication"]
        assert "10.1016/x" in df.iloc[0]["publication"]

    def test_announcement_xml_dropped(self):
        df = parse_summary_tsv(SAMPLE_TSV)
        assert "announcementXML" not in df.columns

    def test_trailing_whitespace_stripped(self):
        df = parse_summary_tsv(SAMPLE_TSV)
        # Species had trailing space in raw data
        assert df.iloc[0]["species"] == "Rattus norvegicus"

    def test_no_empty_rows(self):
        tsv_with_blank = SAMPLE_TSV + "\t\t\t\t\t\t\t\t\t\t\n"
        df = parse_summary_tsv(tsv_with_blank)
        assert len(df) == 2

    def test_single_row(self):
        single = (
            "Dataset Identifier\tTitle\tRepos\tSpecies\tInstrument\tPublication\t"
            "LabHead\tAnnounce Date\tKeywords\tannouncementXML\n"
            "PXD000001\tTest\tPRIDE\tHuman\tOrbitrap\tno pub\tDoe\t2020-01-01\ttest,\t\n"
        )
        df = parse_summary_tsv(single)
        assert len(df) == 1
        assert df.iloc[0]["dataset_id"] == "PXD000001"


# ---------------------------------------------------------------------------
# parse_summary_tsv with real fixture file
# ---------------------------------------------------------------------------


class TestParseSummaryTsvFixture:
    @pytest.fixture()
    def fixture_tsv(self):
        fixture_path = Path(__file__).parent / "fixtures" / "sample_summary.tsv"
        return fixture_path.read_text()

    def test_fixture_parses(self, fixture_tsv):
        df = parse_summary_tsv(fixture_tsv)
        assert len(df) >= 3
        assert "dataset_id" in df.columns
        # All dataset IDs should start with PXD
        assert df["dataset_id"].str.startswith("PXD").all()

    def test_fixture_no_html_in_any_cell(self, fixture_tsv):
        df = parse_summary_tsv(fixture_tsv)
        for col in df.columns:
            series = df[col].dropna()
            assert not series.str.contains("<a ", regex=False).any(), (
                f"HTML found in column {col}"
            )



# ---------------------------------------------------------------------------
# parse_dataset_xml
# ---------------------------------------------------------------------------

SAMPLE_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProteomeXchangeDataset id="PXD099999" formatVersion="1.4.0"
    xsi:noNamespaceSchemaLocation="proteomeXchange-1.4.0.xsd"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <DatasetSummary announceDate="2025-06-01" hostingRepository="PRIDE"
        title="Test dataset title">
        <Description>This is the abstract of the dataset.</Description>
        <ReviewLevel>
            <cvParam cvRef="MS" accession="MS:1002854" name="Peer-reviewed dataset"/>
        </ReviewLevel>
    </DatasetSummary>
    <SpeciesList>
        <Species>
            <cvParam cvRef="MS" accession="MS:1001469"
                name="taxonomy: scientific name" value="Homo sapiens"/>
            <cvParam cvRef="MS" accession="MS:1001467"
                name="taxonomy: NCBI TaxID" value="NEWT:9606"/>
        </Species>
    </SpeciesList>
    <InstrumentList>
        <Instrument id="Instrument_1">
            <cvParam cvRef="MS" accession="MS:1003028" name="Orbitrap Exploris 480"/>
        </Instrument>
    </InstrumentList>
    <ModificationList>
        <cvParam cvRef="MOD" accession="MOD:00397"
            name="iodoacetamide derivatized residue"/>
    </ModificationList>
    <ContactList>
        <Contact id="project_submitter">
            <cvParam cvRef="MS" accession="MS:1000586" name="contact name" value="Jane Doe"/>
            <cvParam cvRef="MS" accession="MS:1000589"
                name="contact email" value="jane@example.com"/>
            <cvParam cvRef="MS" accession="MS:1000590"
                name="contact affiliation" value="University of Test"/>
            <cvParam cvRef="MS" accession="MS:1002037" name="dataset submitter"/>
        </Contact>
        <Contact id="project_lab_head">
            <cvParam cvRef="MS" accession="MS:1002332" name="lab head"/>
            <cvParam cvRef="MS" accession="MS:1000586"
                name="contact name" value="Prof Smith"/>
            <cvParam cvRef="MS" accession="MS:1000589"
                name="contact email" value="smith@example.com"/>
            <cvParam cvRef="MS" accession="MS:1000590"
                name="contact affiliation" value="Institute of Science"/>
        </Contact>
    </ContactList>
    <PublicationList>
        <Publication id="PMID12345">
            <cvParam cvRef="MS" accession="MS:1000879"
                name="PubMed identifier" value="12345"/>
        </Publication>
        <Publication id="DOI-10_1234_test">
            <cvParam cvRef="MS" accession="MS:1001922"
                name="Digital Object Identifier (DOI)" value="10.1234/test"/>
        </Publication>
    </PublicationList>
    <KeywordList>
        <cvParam cvRef="MS" accession="MS:1001925"
            name="submitter keyword" value="proteomics, mass spec, test"/>
    </KeywordList>
    <FullDatasetLinkList>
        <FullDatasetLink>
            <cvParam cvRef="MS" accession="MS:1002852"
                name="Dataset FTP location"
                value="ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2025/06/PXD099999"/>
        </FullDatasetLink>
    </FullDatasetLinkList>
</ProteomeXchangeDataset>
"""


class TestParseDatasetXml:
    def test_dataset_id(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["dataset_id"] == "PXD099999"

    def test_title(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["title"] == "Test dataset title"

    def test_description(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["description"] == "This is the abstract of the dataset."

    def test_species(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["species"] == "Homo sapiens"

    def test_instruments(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["instruments"] == "Orbitrap Exploris 480"

    def test_modifications(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert "iodoacetamide" in result["modifications"]

    def test_submitter_contact(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["submitter_name"] == "Jane Doe"
        assert result["submitter_email"] == "jane@example.com"
        assert result["submitter_affiliation"] == "University of Test"

    def test_lab_head_contact(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["lab_head_name"] == "Prof Smith"
        assert result["lab_head_email"] == "smith@example.com"

    def test_pubmed(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["pubmed_ids"] == "12345"

    def test_doi(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["dois"] == "10.1234/test"

    def test_ftp_location(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert "PXD099999" in result["ftp_location"]

    def test_review_level(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["review_level"] == "Peer-reviewed dataset"

    def test_announce_date(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["announce_date"] == "2025-06-01"

    def test_repository(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert result["repository"] == "PRIDE"

    def test_keywords(self):
        result = parse_dataset_xml(SAMPLE_XML)
        assert "proteomics" in result["keywords"]


class TestParseDatasetXmlFixture:
    @pytest.fixture()
    def fixture_xml(self):
        fixture_path = Path(__file__).parent / "fixtures" / "sample_dataset.xml"
        return fixture_path.read_text()

    def test_fixture_parses(self, fixture_xml):
        result = parse_dataset_xml(fixture_xml)
        assert result["dataset_id"] == "PXD063194"
        assert "PRIDE" in result["repository"]

    def test_fixture_has_description(self, fixture_xml):
        result = parse_dataset_xml(fixture_xml)
        assert len(result["description"]) > 50

    def test_fixture_has_species(self, fixture_xml):
        result = parse_dataset_xml(fixture_xml)
        assert "Rattus" in result["species"]

    def test_fixture_has_contacts(self, fixture_xml):
        result = parse_dataset_xml(fixture_xml)
        assert result["submitter_name"] != ""
        assert "@" in result["submitter_email"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestParseEdgeCases:
    def test_xml_missing_description(self):
        xml = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProteomeXchangeDataset id="PXD000001" formatVersion="1.4.0"
    xsi:noNamespaceSchemaLocation="proteomeXchange-1.4.0.xsd"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <DatasetSummary announceDate="2020-01-01" hostingRepository="PRIDE"
        title="Minimal dataset">
    </DatasetSummary>
</ProteomeXchangeDataset>
"""
        result = parse_dataset_xml(xml)
        assert result["dataset_id"] == "PXD000001"
        assert result["description"] == ""
        assert result["species"] == ""
        assert result["keywords"] == ""

    def test_xml_multiple_species(self):
        xml = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProteomeXchangeDataset id="PXD000002" formatVersion="1.4.0"
    xsi:noNamespaceSchemaLocation="proteomeXchange-1.4.0.xsd"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <DatasetSummary announceDate="2020-01-01" hostingRepository="MassIVE"
        title="Multi-species">
    </DatasetSummary>
    <SpeciesList>
        <Species>
            <cvParam cvRef="MS" accession="MS:1001469"
                name="taxonomy: scientific name" value="Homo sapiens"/>
        </Species>
        <Species>
            <cvParam cvRef="MS" accession="MS:1001469"
                name="taxonomy: scientific name" value="Mus musculus"/>
        </Species>
    </SpeciesList>
</ProteomeXchangeDataset>
"""
        result = parse_dataset_xml(xml)
        assert "Homo sapiens" in result["species"]
        assert "Mus musculus" in result["species"]
        assert "; " in result["species"]

    def test_tsv_with_only_header(self):
        header_only = (
            "Dataset Identifier\tTitle\tRepos\tSpecies\tInstrument\t"
            "Publication\tLabHead\tAnnounce Date\tKeywords\tannouncementXML\n"
        )
        df = parse_summary_tsv(header_only)
        assert len(df) == 0
        assert "dataset_id" in df.columns

    def test_tsv_empty_string_raises(self):
        with pytest.raises(Exception):
            parse_summary_tsv("")

    def test_xml_invalid_raises(self):
        with pytest.raises(Exception):
            parse_dataset_xml("this is not xml")

    def test_xml_empty_string_raises(self):
        with pytest.raises(Exception):
            parse_dataset_xml("")
